"""
Motor de daño estilo Pokémon (Gen V/VI, sin items ni naturalezas).

Fórmula clásica:

    base = ((2 * nivel / 5 + 2) * potencia * A / D) / 50 + 2
    daño = base * STAB * efectividad * crítico * aleatorio

Donde:
- nivel: fijo en 50 (estándar de torneo).
- A: `attack` si el movimiento es físico, `sp_attack` si es especial.
- D: `defense` si el movimiento es físico, `sp_defense` si es especial.
- STAB (Same-Type Attack Bonus): 1.5 si el tipo del movimiento coincide con
  alguno de los tipos del atacante.
- efectividad: producto de los multiplicadores tipo->tipo de cada tipo del
  defensor, leído de la tabla `TypeEffectiveness` (×0, ×0.5, ×2 o ×1 por
  defecto si no hay fila).
- crítico: 1.5 con probabilidad CRIT_CHANCE.
- aleatorio: uniforme [0.85, 1.0] (similar al RNG real del juego).

Movimientos de estado o sin potencia hacen 0 daño (sin efectos por simplicidad).
"""

import random as _random
from typing import Optional

from myapp.models import TypeEffectiveness


# Constantes de balance.
BATTLE_LEVEL = 50
CRIT_CHANCE = 0.0625        # 1/16, como en Gen II+.
CRIT_MULTIPLIER = 1.5
STAB_MULTIPLIER = 1.5
RNG_LOW, RNG_HIGH = 0.85, 1.0


def _type_effectiveness(attacker_type: str, defender_types: list) -> float:
    """Producto del multiplicador atacante -> cada tipo del defensor."""
    if not defender_types:
        return 1.0
    rows = TypeEffectiveness.objects.filter(
        attacker_type=attacker_type,
        defender_type__in=defender_types,
    ).values_list("defender_type", "multiplier")
    found = {d: m for d, m in rows}
    mult = 1.0
    for dt in defender_types:
        mult *= found.get(dt, 1.0)
    return mult


def calculate_damage(attacker, defender, move, *, level: int = BATTLE_LEVEL,
                     rng: Optional[_random.Random] = None):
    """Calcula el daño de `move` lanzado por `attacker` contra `defender`.

    Devuelve `(damage:int, info:dict)`. `info` contiene flags útiles para el
    log de combate:
        missed         True si falla por precisión.
        crit           True si fue crítico.
        stab           1.0 / 1.5
        effectiveness  multiplicador final por tipos.
        category       categoría del movimiento.
    """
    rng = rng or _random
    info = {
        "missed": False,
        "crit": False,
        "stab": 1.0,
        "effectiveness": 1.0,
        "category": move.category,
    }

    # Movimientos de estado o sin potencia: sin daño (de momento).
    if move.category == "status" or not move.power:
        info["status_move"] = True
        return 0, info

    # 1) Precisión.
    if move.accuracy is not None and rng.random() * 100 > move.accuracy:
        info["missed"] = True
        return 0, info

    # 2) Estadísticas según categoría.
    if move.category == "physical":
        A = attacker.attack
        D = defender.defense
    else:  # special
        A = attacker.sp_attack
        D = defender.sp_defense
    D = max(D, 1)  # evita división por cero si llegara una D=0.

    # 3) STAB.
    attacker_types = [attacker.type1] + ([attacker.type2] if attacker.type2 else [])
    if move.type in attacker_types:
        info["stab"] = STAB_MULTIPLIER

    # 4) Efectividad de tipos.
    defender_types = [defender.type1] + ([defender.type2] if defender.type2 else [])
    eff = _type_effectiveness(move.type, defender_types)
    info["effectiveness"] = eff

    # Inmunidad: cero, sin pasar por el resto.
    if eff == 0:
        return 0, info

    # 5) Crítico y RNG.
    if rng.random() < CRIT_CHANCE:
        info["crit"] = True
    rand = rng.uniform(RNG_LOW, RNG_HIGH)

    # 6) Fórmula.
    base = (((2 * level / 5 + 2) * move.power * A / D) / 50) + 2
    modifier = (
        info["stab"]
        * eff
        * (CRIT_MULTIPLIER if info["crit"] else 1.0)
        * rand
    )
    damage = int(base * modifier)
    return max(damage, 1), info


def describe_effect(info: dict) -> str:
    """Texto auxiliar tras un ataque: '¡Súper eficaz!', '¡Crítico!', etc."""
    if info.get("missed"):
        return "¡El ataque falló!"
    if info.get("status_move"):
        return "Movimiento de estado (sin daño)."
    parts = []
    eff = info.get("effectiveness", 1.0)
    if eff == 0:
        parts.append("No tuvo efecto…")
    elif eff >= 2:
        parts.append("¡Es súper eficaz!")
    elif 0 < eff < 1:
        parts.append("No es muy eficaz…")
    if info.get("crit"):
        parts.append("¡Golpe crítico!")
    return " ".join(parts)
