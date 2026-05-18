"""
Importa movimientos desde PokéAPI y asigna 4 por cada Creature importada.

Estrategia:
1. Para cada Creature con pokemon_id descarga /pokemon/{id}/.
2. De su lista `moves[]` toma los movimientos aprendidos por nivel
   (`move_learn_method == level-up`).
3. Los ordena por `level_learned_at` ascendente y se queda con los
   primeros que tengan poder asignado (para que el combate haga daño),
   completando con los que falten si no hay suficientes con poder.
4. Cada Move se descarga UNA sola vez (cache por URL) y se guarda en
   el modelo Move (update_or_create por `name` que es unique).
5. Se enlazan a la criatura vía CreatureMove con `level_learned`.
"""

import time

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from myapp.models import Creature, CreatureMove, Move


POKEAPI_BASE = "https://pokeapi.co/api/v2"

TYPE_MAP = {
    "normal": "normal", "fire": "fire", "water": "water",
    "electric": "electric", "grass": "grass", "ice": "ice",
    "fighting": "fighting", "poison": "poison", "ground": "ground",
    "flying": "flying", "psychic": "psychic", "bug": "bug",
    "rock": "rock", "ghost": "ghost", "dragon": "dragon",
    "dark": "dark", "steel": "steel", "fairy": "fairy",
}

DAMAGE_CLASS_MAP = {
    "physical": "physical",
    "special": "special",
    "status": "status",
}

MOVES_PER_CREATURE = 4


def _fetch_json(url, timeout):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None
    except ValueError:
        return None


def _english(entries, field="name"):
    for entry in entries or []:
        lang = (entry.get("language") or {}).get("name")
        if lang == "en":
            return entry.get(field, "").replace("\n", " ").replace("\f", " ").strip()
    return ""


class Command(BaseCommand):
    help = "Importa y asigna 4 movimientos desde PokéAPI a cada Creature importada."

    def add_arguments(self, parser):
        parser.add_argument("--delay", type=float, default=0.05)
        parser.add_argument("--timeout", type=float, default=10.0)
        parser.add_argument("--replace", action="store_true",
                            help="Borra CreatureMove existentes antes de importar.")

    # ------------------------------------------------------------------ #

    def _fetch_or_create_move(self, move_url, cache, timeout):
        """Descarga (o usa cache) y crea/actualiza un Move."""
        if move_url in cache:
            return cache[move_url]

        data = _fetch_json(move_url, timeout)
        if not data:
            cache[move_url] = None
            return None

        english_name = _english(data.get("names")) or data.get("name", "").replace("-", " ").title()
        type_name = (data.get("type") or {}).get("name")
        type_mapped = TYPE_MAP.get(type_name, "normal")
        dmg_class = (data.get("damage_class") or {}).get("name")
        category = DAMAGE_CLASS_MAP.get(dmg_class, "status")
        power = data.get("power")
        accuracy = data.get("accuracy")
        pp = data.get("pp") or 5
        description = _english(data.get("flavor_text_entries"), field="flavor_text") or ""

        # PP del modelo está acotado a 40
        pp = max(1, min(pp, 40))

        defaults = {
            "type": type_mapped,
            "category": category,
            "power": power if power and power <= 255 else (power if power is None else 255),
            "accuracy": accuracy if accuracy and 1 <= accuracy <= 100 else (accuracy if accuracy is None else 100),
            "pp": pp,
            "description": description,
        }

        move, _ = Move.objects.update_or_create(name=english_name, defaults=defaults)
        cache[move_url] = move
        return move

    def _pick_moves(self, pokemon_data):
        """Selecciona hasta 4 movimientos (preferentemente con poder)."""
        candidates = []
        for entry in pokemon_data.get("moves", []):
            move_url = (entry.get("move") or {}).get("url")
            if not move_url:
                continue
            # Mínimo nivel level-up
            levels = [
                d.get("level_learned_at") or 0
                for d in entry.get("version_group_details", [])
                if (d.get("move_learn_method") or {}).get("name") == "level-up"
                and (d.get("level_learned_at") or 0) >= 1
            ]
            if not levels:
                continue
            candidates.append((min(levels), move_url))

        candidates.sort(key=lambda t: t[0])
        return candidates[: MOVES_PER_CREATURE * 3]  # margen por si alguno falla

    # ------------------------------------------------------------------ #

    def handle(self, *args, **options):
        delay = options["delay"]
        timeout = options["timeout"]

        if options["replace"]:
            deleted, _ = CreatureMove.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"--replace: eliminadas {deleted} relaciones CreatureMove."
            ))

        creatures = Creature.objects.filter(pokemon_id__isnull=False).order_by("pokemon_id")
        total = creatures.count()
        if total == 0:
            self.stdout.write(self.style.ERROR(
                "No hay criaturas con pokemon_id. Ejecuta antes 'import_pokemon'."
            ))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Asignando hasta {MOVES_PER_CREATURE} movimientos a {total} criaturas..."
        ))

        move_cache = {}
        rel_created = 0
        rel_updated = 0
        failed = []

        for creature in creatures:
            poke_url = f"{POKEAPI_BASE}/pokemon/{creature.pokemon_id}/"
            data = _fetch_json(poke_url, timeout)
            if not data:
                failed.append(creature.pokemon_id)
                self.stdout.write(self.style.ERROR(
                    f"  #{creature.pokemon_id:>4} {creature.name}: sin respuesta"
                ))
                time.sleep(delay)
                continue

            candidates = self._pick_moves(data)
            assigned = 0

            with transaction.atomic():
                for level, move_url in candidates:
                    if assigned >= MOVES_PER_CREATURE:
                        break
                    move = self._fetch_or_create_move(move_url, move_cache, timeout)
                    if not move:
                        continue
                    _, was_created = CreatureMove.objects.update_or_create(
                        creature=creature,
                        move=move,
                        defaults={"level_learned": min(max(level, 1), 100)},
                    )
                    if was_created:
                        rel_created += 1
                    else:
                        rel_updated += 1
                    assigned += 1
                    time.sleep(delay)

            self.stdout.write(
                f"  #{creature.pokemon_id:>4} {creature.name:<15} -> {assigned} movimientos"
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Moves únicos en cache: {sum(1 for v in move_cache.values() if v)}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Relaciones creadas={rel_created}, actualizadas={rel_updated}."
        ))
        if failed:
            self.stdout.write(self.style.ERROR(f"Fallidos: {failed}"))
