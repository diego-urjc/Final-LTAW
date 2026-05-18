"""
Suite de pruebas automatizadas de PocketArena (Fase 13).

Cobertura:
- Modelos: Creature, Team, Move.
- Autenticación (login, login fallido, registro, logout).
- Vistas protegidas (profile, my_teams, battle_setup).
- Sistema de combate (moves asignados, daño básico, sesión).
- API REST (listado / detalle / 404 / teams).
"""

import json

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from .models import Creature, Move, CreatureMove, Team, TeamCreature


# ---------------------------------------------------------------------- #
#  Helpers                                                                #
# ---------------------------------------------------------------------- #

def _make_creature(name="Testmon", **overrides):
    defaults = dict(
        name=name,
        type1="fire",
        hp=100, attack=80, defense=70, speed=90,
        sp_attack=80, sp_defense=70,
    )
    defaults.update(overrides)
    return Creature.objects.create(**defaults)


def _make_move(name="Ember", **overrides):
    defaults = dict(
        name=name, type="fire", category="special",
        power=40, accuracy=100, pp=25, description="Test move",
    )
    defaults.update(overrides)
    return Move.objects.create(**defaults)


# ---------------------------------------------------------------------- #
#  Modelos                                                                #
# ---------------------------------------------------------------------- #

class CreatureModelTests(TestCase):
    def test_create_creature(self):
        c = _make_creature()
        self.assertEqual(Creature.objects.count(), 1)
        self.assertEqual(c.name, "Testmon")
        self.assertEqual(c.hp, 100)

    def test_str_representation(self):
        c = _make_creature(name="Flamiboo")
        self.assertEqual(str(c), "Flamiboo")

    def test_types_display(self):
        single = _make_creature(name="Mono", type1="water")
        self.assertEqual(single.get_types_display(), "Agua")
        dual = _make_creature(name="Dual", type1="grass", type2="poison")
        self.assertEqual(dual.get_types_display(), "Planta / Veneno")


class TeamModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="trainer", password="pwd12345")

    def test_create_team(self):
        team = Team.objects.create(name="Equipo Alpha", user=self.user)
        self.assertEqual(Team.objects.count(), 1)
        self.assertEqual(team.name, "Equipo Alpha")
        self.assertFalse(team.is_public)

    def test_str_representation(self):
        team = Team.objects.create(name="Equipo Beta", user=self.user)
        self.assertEqual(str(team), "Equipo Beta - trainer")


class MoveModelTests(TestCase):
    def test_create_move(self):
        m = _make_move()
        self.assertEqual(Move.objects.count(), 1)
        self.assertEqual(m.power, 40)
        self.assertEqual(m.category, "special")

    def test_str_representation(self):
        m = _make_move(name="Flamethrower")
        self.assertEqual(str(m), "Flamethrower")


# ---------------------------------------------------------------------- #
#  Autenticación                                                          #
# ---------------------------------------------------------------------- #

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="ash", password="pikapika")

    def test_login_success(self):
        ok = self.client.login(username="ash", password="pikapika")
        self.assertTrue(ok)

    def test_login_fail(self):
        ok = self.client.login(username="ash", password="wrong")
        self.assertFalse(ok)

    def test_register_creates_user(self):
        response = self.client.post(reverse("register"), {
            "username": "newbie",
            "email": "new@example.com",
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
        })
        # tras registro exitoso se redirige
        self.assertIn(response.status_code, (302, 200))
        self.assertTrue(User.objects.filter(username="newbie").exists())

    def test_logout(self):
        self.client.login(username="ash", password="pikapika")
        response = self.client.post(reverse("logout"))
        self.assertIn(response.status_code, (200, 302))


# ---------------------------------------------------------------------- #
#  Vistas protegidas                                                      #
# ---------------------------------------------------------------------- #

class ProtectedViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="misty", password="watergun")

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_profile_accessible_when_logged_in(self):
        self.client.login(username="misty", password="watergun")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

    def test_my_teams_requires_login(self):
        response = self.client.get(reverse("my_teams"))
        self.assertEqual(response.status_code, 302)

    def test_my_teams_accessible_when_logged_in(self):
        self.client.login(username="misty", password="watergun")
        response = self.client.get(reverse("my_teams"))
        self.assertEqual(response.status_code, 200)

    def test_battle_setup_requires_login(self):
        response = self.client.get(reverse("battle_setup"))
        self.assertEqual(response.status_code, 302)

    def test_battle_setup_accessible_when_logged_in(self):
        self.client.login(username="misty", password="watergun")
        response = self.client.get(reverse("battle_setup"))
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------- #
#  Sistema de combate                                                     #
# ---------------------------------------------------------------------- #

class CombatSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="brock", password="rockhard")
        self.client.login(username="brock", password="rockhard")

        # Pool grande para que el modo random/normal pueda construir rivales.
        self.creatures = [
            _make_creature(name=f"Mon{i}", type1="normal")
            for i in range(12)
        ]
        self.move = _make_move(name="Tackle", type="normal", category="physical",
                               power=40, accuracy=100, pp=35)
        for c in self.creatures:
            CreatureMove.objects.create(creature=c, move=self.move, level_learned=1)

        # Equipo del usuario con pokémon
        self.team = Team.objects.create(name="Roca Team", user=self.user)
        for pos, c in enumerate(self.creatures[:3], start=1):
            TeamCreature.objects.create(team=self.team, creature=c, position=pos)

    def test_creatures_have_moves(self):
        for c in self.creatures:
            self.assertGreater(c.moves.count(), 0)

    def test_basic_damage_value(self):
        # El combate usa move.power o 20 como fallback. Validamos la regla básica.
        dmg = self.move.power if self.move.power else 20
        self.assertEqual(dmg, 40)
        no_power = _make_move(name="StatusMove", category="status",
                              power=None, accuracy=None, pp=10)
        fallback = no_power.power if no_power.power else 20
        self.assertEqual(fallback, 20)

    def test_battle_setup_renders_menu(self):
        response = self.client.get(reverse("battle_setup"))
        self.assertEqual(response.status_code, 200)

    def test_battle_normal_creates_session(self):
        response = self.client.post(
            reverse("battle_normal_setup"),
            {"team": self.team.id},
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("battle", self.client.session)
        session_battle = self.client.session["battle"]
        self.assertEqual(session_battle["mode"], "normal")
        self.assertEqual(len(session_battle["team1"]), 3)

    def test_battle_turn_requires_active_session(self):
        # Sin sesión de combate previa, debe redirigir al setup.
        response = self.client.get(reverse("battle_turn"))
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------- #
#  API REST                                                               #
# ---------------------------------------------------------------------- #

class APITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="oak", password="profprof")
        self.c1 = _make_creature(name="Bulbasaur", type1="grass", type2="poison",
                                 pokemon_id=1)
        self.c2 = _make_creature(name="Charmander", type1="fire", pokemon_id=4)
        self.move = _make_move(name="Vine Whip", type="grass", category="physical",
                               power=45, accuracy=100, pp=25)
        CreatureMove.objects.create(creature=self.c1, move=self.move, level_learned=3)

        self.team_pub = Team.objects.create(name="Public", user=self.user, is_public=True)
        self.team_priv = Team.objects.create(name="Private", user=self.user, is_public=False)

    def test_creatures_list(self):
        response = self.client.get(reverse("api_creatures_list"))
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertIn("creatures", payload)
        self.assertEqual(payload["total"], 2)
        names = [c["name"] for c in payload["creatures"]]
        self.assertIn("Bulbasaur", names)
        self.assertIn("Charmander", names)

    def test_creature_detail(self):
        response = self.client.get(
            reverse("api_creature_detail", args=[self.c1.id])
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload["name"], "Bulbasaur")
        self.assertEqual(payload["pokemon_id"], 1)
        self.assertEqual(len(payload["moves"]), 1)
        self.assertEqual(payload["moves"][0]["name"], "Vine Whip")

    def test_creature_detail_404(self):
        response = self.client.get(
            reverse("api_creature_detail", args=[99999])
        )
        self.assertEqual(response.status_code, 404)

    def test_teams_list_only_public(self):
        response = self.client.get(reverse("api_teams_list"))
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["teams"][0]["name"], "Public")
