"""
Importa Pokémon desde PokéAPI a la base local SQLite.

Estrategia:
- Usa /api/v2/pokemon/{id}/ (público, sin API key).
- update_or_create por pokemon_id garantiza idempotencia.
- Solo importa stats básicos (hp, atk, def, spd, sp_atk, sp_def).
- Mapeo de tipos 1:1 con POKEAPI_TYPE_MAP.
- Sprite preferido: official-artwork con fallback a front_default.

Limitaciones deliberadas (por diseño, no por error):
- No importa movimientos, habilidades o tipos de efectividad.
- Solo pokemon_id nullable para no romper pokémon legacy.
- Importación offline-only: las vistas no llaman a PokéAPI.
"""

import time

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from myapp.models import Creature


# Endpoint base de PokéAPI (no requiere API key, es público y gratuito).
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/pokemon"

# Mapa de tipos PokéAPI -> claves internas de Pokemon.TYPE_CHOICES.
# Coinciden todos en minúscula y en inglés, así que es 1:1, pero lo
# centralizamos por si en el futuro queremos traducir o filtrar.
POKEAPI_TYPE_MAP = {
    "normal": "normal", "fire": "fire", "water": "water",
    "electric": "electric", "grass": "grass", "ice": "ice",
    "fighting": "fighting", "poison": "poison", "ground": "ground",
    "flying": "flying", "psychic": "psychic", "bug": "bug",
    "rock": "rock", "ghost": "ghost", "dragon": "dragon",
    "dark": "dark", "steel": "steel", "fairy": "fairy",
}

# Stats mínimos para no chocar con MinValueValidator(1) del modelo Creature.
_DEFAULT_STATS = {"hp": 1, "attack": 1, "defense": 1, "speed": 1, "sp_attack": 1, "sp_defense": 1}


class Command(BaseCommand):
    help = "Importa Pokémon desde PokéAPI a la base local SQLite"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start", type=int, default=1,
            help="ID del primer Pokémon a importar (default: 1)"
        )
        parser.add_argument(
            "--limit", type=int, default=151,
            help="Cantidad de Pokémon a importar (default: 151)"
        )
        parser.add_argument(
            "--delay", type=float, default=0.1,
            help="Segundos de espera entre peticiones para no saturar la API.",
        )
        parser.add_argument(
            "--timeout", type=float, default=10.0,
            help="Timeout (segundos) para cada petición HTTP.",
        )
        parser.add_argument(
            "--replace", action="store_true",
            help="Elimina todas las Pokemon existentes antes de importar.",
        )

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _fetch_pokemon(self, pokemon_id, timeout):
        """Descarga el JSON de un Pokémon. Devuelve dict o None si hay error."""
        url = f"{POKEAPI_BASE_URL}/{pokemon_id}/"
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as exc:
            self.stdout.write(self.style.ERROR(f"  HTTP error {exc.response.status_code}"))
        except requests.exceptions.RequestException as exc:
            self.stdout.write(self.style.ERROR(f"  Request error: {exc}"))
        except ValueError as exc:
            self.stdout.write(self.style.ERROR(f"  JSON decode error: {exc}"))
        return None

    def _parse_types(self, data):
        """Extrae type1 y type2 del JSON de PokéAPI."""
        types = data.get("types", [])
        if not types:
            return None, None
        type1 = POKEAPI_TYPE_MAP.get(types[0].get("type", {}).get("name"))
        type2 = None
        if len(types) > 1:
            type2 = POKEAPI_TYPE_MAP.get(types[1].get("type", {}).get("name"))
        return type1, type2

    def _parse_stats(self, data):
        """Extrae stats básicos del JSON de PokéAPI."""
        stats_map = {
            "hp": "hp",
            "attack": "attack",
            "defense": "defense",
            "speed": "speed",
            "special-attack": "sp_attack",
            "special-defense": "sp_defense",
        }
        stats = {}
        for stat_entry in data.get("stats", []):
            name = stat_entry.get("stat", {}).get("name")
            value = stat_entry.get("base_stat", 0)
            if name in stats_map:
                stats[stats_map[name]] = min(value, 255)  # Cap a 255
        return stats

    def _parse_image_url(self, data):
        """Extrae la URL del sprite preferido."""
        sprites = data.get("sprites", {}) or {}
        other = sprites.get("other", {}) or {}
        official = other.get("official-artwork", {}) or {}
        url = official.get("front_default")
        if not url:
            url = sprites.get("front_default")
        return url or ""

    # ------------------------------------------------------------------ #
    #  Main                                                               #
    # ------------------------------------------------------------------ #

    def handle(self, *args, **options):
        start = options["start"]
        limit = options["limit"]
        delay = options["delay"]
        timeout = options["timeout"]
        replace = options["replace"]

        if start < 1 or limit < 1:
            raise CommandError("--start y --limit deben ser enteros positivos.")

        if replace:
            deleted, _ = Creature.objects.filter(pokemon_id__isnull=False).delete()
            self.stdout.write(self.style.WARNING(
                f"--replace activo: eliminadas {deleted} pokémon importadas previas."
            ))

        end = start + limit - 1
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Importando Pokémon #{start} a #{end} desde PokéAPI..."
        ))

        created_count = 0
        updated_count = 0
        failed = []

        for pokemon_id in range(start, end + 1):
            self.stdout.write(f"  #{pokemon_id:>3} ", ending="")
            data = self._fetch_pokemon(pokemon_id, timeout)
            if not data:
                failed.append(pokemon_id)
                self.stdout.write(self.style.ERROR("FAIL"))
                time.sleep(delay)
                continue

            try:
                name = data["name"].capitalize()
                type1, type2 = self._parse_types(data)
                stats = self._parse_stats(data)
                image_url = self._parse_image_url(data)

                # update_or_create por pokemon_id evita duplicados aunque
                # se ejecute el comando varias veces.
                # Garantiza que todos los stats mínimos están presentes.
                final_stats = {**_DEFAULT_STATS, **stats}
                with transaction.atomic():
                    creature, created = Creature.objects.update_or_create(
                        pokemon_id=pokemon_id,
                        defaults={
                            "name": name,
                            "type1": type1,
                            "type2": type2,
                            "image_url": image_url,
                            "description": "",
                            **final_stats,
                        },
                    )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"{name} {type1}/{type2 or '-'} [nuevo]"))
                else:
                    updated_count += 1
                    self.stdout.write(f"{name} {type1}/{type2 or '-'} [actualizado]")
            except Exception as e:  # noqa: BLE001 (queremos seguir el bucle)
                failed.append(pokemon_id)
                self.stdout.write(self.style.ERROR(f"FAIL: {e}"))

            time.sleep(delay)

        # Resumen final
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Resumen"))
        self.stdout.write(f"  Creados: {created_count}")
        self.stdout.write(f"  Actualizados: {updated_count}")
        if failed:
            self.stdout.write(self.style.ERROR(f"  Fallidos: {len(failed)} IDs: {failed}"))
        else:
            self.stdout.write(self.style.SUCCESS("  Fallidos: 0"))
