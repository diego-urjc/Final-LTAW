# PocketArena - Fases de Desarrollo

## Fase 1: Base del Proyecto Django
- **settings.py**: `myapp` registrada, `TEMPLATES.DIRS = [BASE_DIR/templates]`, `STATICFILES_DIRS`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`, `LOGIN_URL`.
- **urls.py**: rutas `home`, `login`, `logout` (auth views de Django).
- **Plantillas**: `base.html` (Bootstrap 5.3 + HTMX + navbar condicional + mensajes), `home.html` (hero + cards), `registration/login.html`.
- **Estáticos**: `static/css/style.css` con variables de tema, estilos para 18 tipos elementales, arena y team builder, diseño responsive mobile-first.
- **Vistas**: `home()` con contexto dinámico.

---

## Fase 2: Sistema de Autenticación
- **forms.py**: `CustomUserCreationForm` con validación de email único, regex de username y widgets Bootstrap.
- **views.py**: `register()` (POST + auto-login + mensajes) y `profile()` protegida con `@login_required`.
- **urls.py**: `register/` y `profile/`.
- **Plantillas**: `registration/register.html` y `users/profile.html`.
- **UX**: navbar con `{% if user.is_authenticated %}`, CTA dinámicos en `home`, login ↔ register enlazados.
- **Seguridad**: `@login_required`, validación cliente + servidor, mensajes `success/error/info`.

---

## Fase 3: Modelos de Datos
- **models.py** (7 modelos):
  - `Creature` (stats 1-255, 18 tipos), `Move` (físico/especial/estado, poder/precisión/PP), `CreatureMove` (intermedia con `level_learned`, `unique_together`).
  - `Team` (público/privado), `TeamCreature` (posiciones 1-6).
  - `Battle` (PK UUID, jugadores, equipos, estado, timestamps), `BattleTurn` (acciones, daño, HP por turno).
- **Relaciones**: MTM (Creature↔Move, Team↔Creature) y OTM (User→Team/Battle, Battle→Turn).
- **admin.py**: inlines (`TeamCreatureInline`, etc.), `select_related`/`prefetch_related`, filtros por tipo/categoría/estado, columnas calculadas (duración, conteo).

---

## Fase 4: Mejoras del Django Admin
Cambios solo en `admin.py`:
- **CreatureAdmin**: stats especiales en `list_display`, `date_hierarchy`, `list_per_page=25`.
- **MoveAdmin**: filtros por precisión/fecha, `list_per_page=50`.
- **CreatureMoveAdmin**: método `get_move_type_display`, filtros por tipo y categoría.
- **TeamCreatureInline**: `autocomplete_fields` en pokémon.
- **TeamAdmin**: `list_editable=is_public`, autocomplete de usuario, `date_hierarchy`.
- **BattleTurnInline**: más `readonly_fields`, `can_delete=False`.
- **BattleAdmin / BattleTurnAdmin**: filtros por fechas y daño, autocomplete de jugadores/equipos/combate.

---

## Fase 5: Datos iniciales
- **Estructura**: `myapp/management/__init__.py`, `myapp/management/commands/__init__.py` para soportar comandos personalizados.
- **Decisión**: las pokémon inventadas iniciales se han descartado en favor de la importación real desde PokéAPI (ver Fase 11). La base de datos arranca vacía y se puebla con `python manage.py import_pokemon`.

---

## Fase 6: CRUD Completo de Equipos
- **forms.py**: `TeamForm` (ModelForm) con validación de nombre ≥3 y descripción ≤500, checkbox `is_public`.
- **views.py**: `team_list` (buscador por nombre/descr./entrenador), `team_detail`, `team_create`, `team_update`, `team_delete` (los tres últimos con verificación de propiedad).
- **urls.py**: `/teams/`, `/teams/<id>/`, `/teams/create/`, `/teams/<id>/edit/`, `/teams/<id>/delete/`.
- **Plantillas nuevas**: `team_list.html`, `team_detail.html`, `team_form.html`, `team_confirm_delete.html` (Bootstrap 5, breadcrumbs, cards, badges, alerts).
- **Permisos**: creación con login, edición/borrado solo dueño (validado en servidor), lectura pública para `is_public`.

---

## Fase 7: Perfil de Usuario con Estadísticas
- **views.py `profile()`**: importa `Battle` y `Count`; calcula `teams_count`, `battles_count` (P1+P2 vía `related_name`), `victories`, `defeats` filtrando `winner`.
- **users/profile.html**: sustitución de valores hardcoded, tarjeta de derrotas, enlaces a `my_teams`, `team_create`, `team_list`.
- Sin nuevos modelos ni archivos; todo a través de relaciones Django existentes.

---

## Fase 8: Sistema de Combate por Turnos

### 8.1 Combate 1vs1 simple
- **views.py**: `battle_setup`, `battle_turn`, `battle_result` con persistencia en `request.session`.
- **urls.py**: `/battle/setup/`, `/battle/turn/`, `/battle/result/`.
- **Plantillas**: `battles/battle_setup.html`, `battles/battle_arena.html` (barras HP + log), `battles/battle_result.html`.
- **Mecánica**: daño = `move.power` o 20 base; orden por `speed`; gestión por HTTP estándar.

### 8.2 Correcciones de plantilla
- `views.py`: añadidos `hp1_percent`/`hp2_percent` al contexto de `battle_turn`.
- `battle_arena.html`: eliminadas `{% widthratio ... as ... %}` inválidas (Django no permite alias en `widthratio`); arreglado `{% endif }` → `{% endif %}`.
- `battle_result.html`: corregido `log|last.target_hp` → `log.last.target_hp` (Django no encadena propiedades tras un filtro).

### 8.3 IA básica del enemigo
- `battle_turn` elige movimiento de la IA con `random.choice` sobre los `ai_moves` disponibles.
- Orden de ataque por `speed` (empate aleatorio); verificación de KO antes del contraataque.
- Log con `player=2` para acciones de la IA; en plantillas se etiqueta "(IA)" con icono robot.

---

## Fase 9: Combates Interactivos con HTMX
- **views.py**: helper `_is_htmx`; `battle_turn` unifica GET/POST sin redirect (partial `_battle_content.html` si HTMX, plantilla completa si no, redirects vía cabecera `HX-Redirect`).
- **Eventos del turno** ("X ha caído", "¡Adelante, Y!") se añaden a `battle['log']` como entradas `{'turn', 'event'}` en lugar de `messages.info` (invisibles en HTMX).
- **Snapshots** `prev_hp1/prev_hp2` y `prev_active1/prev_active2` antes del turno → contexto con `hpN_percent_prev`; tras relevo se fuerza `prev=100`.
- **Partial `_battle_content.html`**: escena Showdown, tarjetas HP/stats, selector de movimientos, historial y `<script>` que ajusta `width` de `.hp-bar` a `data-target` con `requestAnimationFrame`.
- **Animación HP**: CSS `transition: width 1.2s cubic-bezier(.4,0,.2,1)` + interpolación de color (`bg-success`→`bg-warning`→`bg-danger`).
- **Wrapper `battle_arena.html`** reducido a `{% include %}` del partial; HTMX cargado en `base.html` (CDN).

---

## Fase 10: Integración con NVIDIA Build API
- **Servicio `myapp/services/nvidia_service.py`**: `NVIDIABuildService` con `_call_chat` (HTTP/timeout/parseo); API `get_team_recommendations` y `get_battle_recommendation`; `is_configured()` y excepción `NVIDIAServiceError`.
- **Config**: `python-dotenv` carga `.env`; `NVIDIA_API_KEY`, `NVIDIA_API_URL`, `NVIDIA_API_MODEL` (default `meta/llama-3.1-8b-instruct`); `.env` en `.gitignore`.
- **Vistas**: `get_ai_recommendation` (login required, contextos `battle`/`team`, persiste en `AIMessage`, preselección `?team=<id>`) y `ai_history`.
- **urls.py**: `ai/recommendation/` y `ai/history/`.
- **Errores**: logging, captura diferenciada de `Timeout`/`RequestException`/parseo; validación previa con `messages.error`.
- **UI**: `recommendation_form.html`, `recommendation.html` (`pre-wrap`), `history.html` (accordion); dropdown **Asesor IA** en navbar; botón de análisis IA en `team_detail.html` (solo dueño).

---

## Fase 11: Gestión de Pokémon en Equipo y Navegación
- **views.py**: `team_add_creature` (valida tope de 6, posición libre, no duplicados) y `team_remove_creature` (POST + CSRF), ambas restringidas al dueño.
- **urls.py**: `teams/<id>/creatures/add/` y `teams/<id>/creatures/<tc_id>/remove/`.
- **Plantilla `team_add_creature.html`**: selector de pokémon, preview JS de stats y lista de miembros; `team_detail.html` con botones de añadir/eliminar.
- **Menú de combate**: `battle_setup` con tarjetas **Normal** (selector de equipo + CPU aleatoria) y **Random** (6vs6 aleatorio, requiere ≥12 pokémon).
- **Refactor combate por equipos**: cada bando con lista de pokémon, HP por slot e índice activo; **relevo automático** al caer el activo; cabecera con slots vivos/caídos en `battle_arena.html` y `battle_result.html`.
- **Catálogo `creature_list`** (`/creatures/`) en cuadrícula; navbar con entradas **Combates** y **Pokémon**.

---

## Fase 12: Integración PokéAPI
- **Modelo `Creature`**: nuevo campo `pokemon_id` (`PositiveIntegerField`, `unique`, `null/blank`) para distinguir pokémon importadas de custom.
- **admin.py**: columnas `pokemon_id` y `sprite_preview` (miniatura 48×48), búsqueda y edición por `pokemon_id`.
- **Comando `import_pokemon.py`**: consume `https://pokeapi.co/api/v2/pokemon/{id}/` con `requests`; flags `--start`, `--limit` (151), `--delay`, `--timeout`, `--replace`.
- **Idempotente**: `update_or_create(pokemon_id=...)`; captura `HTTPError`/`RequestException`/`ValueError` por Pokémon y reporta fallidos al final.
- **Mapeo**: `POKEAPI_TYPE_MAP` (18 tipos), stats limitados a 255, sprite `official-artwork` (fallback `front_default`), nombre capitalizado.
- **Decisiones**: importación offline-only (las vistas no llaman a PokéAPI), sin DRF, `--delay 0.1s` por cortesía con la API pública.

---

## Fase 13: API REST con `JsonResponse`
- **Objetivo**: API REST ligera con herramientas nativas (`JsonResponse` + ORM), sin Django REST Framework.
- **`GET /api/creatures/`**: `{"creatures": [...], "total": N}` con `id`, `name`, `type1`, `type2`, stats, `pokemon_id`.
- **`GET /api/creatures/<id>/`**: detalle con stats completos y `moves[]` (`id`, `name`, `type`, `power`, `accuracy`); 404 si no existe.
- **`GET /api/teams/`**: equipos públicos con `id`, `name`, `user`, `created_at`, `updated_at`, `creatures_count`.
- **views.py**: import de `JsonResponse` y 3 funciones con serialización manual del ORM.
- **urls.py**: 3 rutas bajo `/api/`.
- **Verificación**: navegador, Postman o cURL contra `/api/creatures/`, `/api/creatures/1/`, `/api/teams/`.

---

## Fase 14: Suite de Pruebas Automatizadas (`tests.py`)
- **Modelos**: `CreatureModelTests`, `TeamModelTests`, `MoveModelTests` validan creación, `__str__` y formato de tipos.
- **Autenticación (`AuthenticationTests`)**: login correcto/fallido, registro y logout.
- **Vistas protegidas (`ProtectedViewTests`)**: redirección sin sesión y acceso autorizado a `profile`, `my_teams` y `battle_setup`.
- **Combate (`CombatSystemTests`)**: pokémon con movimientos, cálculo de daño básico, inicio de sesión en `battle_setup` y restricción de `battle_turn` sin sesión activa.
- **API (`APITests`)**: listado y detalle de pokémon, 404 ante IDs inexistentes y listado de equipos públicos.
- **Ejecución**: `python3 manage.py test myapp` (suite completa) o `python3 manage.py test myapp.tests.CreatureModelTests` (test específico).

---

*PocketArena cubre actualmente: autenticación, modelos completos, admin avanzado, CRUD de equipos con gestión de pokémon, combate por equipos con IA local, integración con NVIDIA Build API, importación de datos reales desde PokéAPI, API REST nativa con `JsonResponse` y suite de pruebas automatizadas.*
