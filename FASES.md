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
- **TeamCreatureInline**: `autocomplete_fields` en criatura.
- **TeamAdmin**: `list_editable=is_public`, autocomplete de usuario, `date_hierarchy`.
- **BattleTurnInline**: más `readonly_fields`, `can_delete=False`.
- **BattleAdmin / BattleTurnAdmin**: filtros por fechas y daño, autocomplete de jugadores/equipos/combate.

---

## Fase 5: Datos iniciales
- **Estructura**: `myapp/management/__init__.py`, `myapp/management/commands/__init__.py` para soportar comandos personalizados.
- **Decisión**: las criaturas inventadas iniciales se han descartado en favor de la importación real desde PokéAPI (ver Fase 11). La base de datos arranca vacía y se puebla con `python manage.py import_pokemon`.

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

### Objetivo
Convertir el flujo de combate (formulario → redirect → GET) en una interacción **sin recargas de página** usando HTMX, e introducir una animación progresiva de la barra de HP estilo Pokémon.

### Cambios en la vista (`views.py`)
- Helper `_is_htmx(request)` detecta la cabecera `HX-Request`.
- `battle_turn` unifica GET y POST en una sola pasada (sin redirect):
  - Si HTMX: devuelve solo el partial `battles/_battle_content.html`.
  - Si no: renderiza la plantilla completa `battle_arena.html`.
  - Los redirects (KO total, sin combate, finalizado) se hacen vía cabecera `HX-Redirect`.
- Los eventos del turno ("X ha caído", "¡Adelante, Y!", "El rival envía Z") ya **no** usan `messages.info` (no son visibles en HTMX): se añaden directamente a `battle['log']` como entradas `{'turn': N, 'event': '...'}` y se renderizan en el historial.
- Snapshots `prev_hp1/prev_hp2` + `prev_active1/prev_active2` antes de procesar el turno → contexto recibe `hp1_percent_prev` y `hp2_percent_prev`. Tras un relevo automático se fuerza `prev = 100` para que el pokémon entrante muestre la barra llena.

### Partial nuevo (`templates/battles/_battle_content.html`)
Contiene todo lo que se intercambia por HTMX:
- Escena Showdown (sprite jugador / rival + plataformas + mini-cards laterales).
- Tarjetas de HP y stats.
- Selector de movimientos (4 botones con tipos coloreados).
- Historial del combate (soporta entradas de daño y entradas de evento puro).
- `<script>` final que en `requestAnimationFrame` ajusta `width` de cada `.hp-bar` a su `data-target`.

### Formulario HTMX
```html
<form hx-post="{% url 'battle_turn' %}"
      hx-target="#battle-content"
      hx-swap="outerHTML"
      hx-indicator="#battle-indicator">
```
- Indicador de carga visible mientras procesa el turno.

### Animación progresiva de la barra HP
- Render: `<div class="progress-bar hp-bar" style="width: {{ prev }}%" data-target="{{ now }}">`.
- Tras el swap, el script JS cambia `width` al objetivo → la transición CSS lo anima.
- CSS: `.progress-bar.hp-bar { transition: width 1.2s cubic-bezier(.4, 0, .2, 1), background-color .8s ease; }` reemplaza al antiguo `transition: width 0.5s ease`.
- El color (`bg-success` → `bg-warning` → `bg-danger`) también se interpola.

### Plantilla wrapper (`battle_arena.html`)
Reducida a estructura externa + `{% include 'battles/_battle_content.html' %}`. Mantiene las reglas CSS de la escena, plataformas, mini-cards y barra HP.

### Mejoras adicionales
- Eliminadas las badges duplicadas de "Tu equipo / Equipo rival" en la cabecera (la información está en las mini-cards laterales de la escena).
- HTMX ya estaba cargado globalmente desde `base.html` (CDN), no requiere instalación adicional.

---

## Fase 10: Integración con NVIDIA Build API

### Servicio aislado (`myapp/services/nvidia_service.py`)
- `NVIDIABuildService` con `_call_chat` central (HTTP, timeout, validación, parseo).
- API pública: `get_team_recommendations(creature_data)` y `get_battle_recommendation(player, enemy)`.
- Config vía `settings`/`.env`: `NVIDIA_API_KEY`, `NVIDIA_API_URL`, `NVIDIA_API_MODEL` (default `meta/llama-3.1-8b-instruct`).
- `is_configured()` para chequeo sin excepción; excepción específica `NVIDIAServiceError`.

### Seguridad
- `python-dotenv` carga `.env` desde `settings.py`; `NVIDIA_API_KEY = os.getenv(...)`.
- `.env` en `.gitignore`, sin claves hardcoded.

### Vistas
- `get_ai_recommendation` (login required): valida configuración, soporta contextos `battle` y `team`, persiste en `AIMessage`, acepta preselección `?team=<id>`.
- `ai_history`: listado de recomendaciones del usuario.
- Rutas `ai/recommendation/` y `ai/history/`.

### Manejo de errores
- Logging (no `print`), captura diferenciada de `Timeout`, `RequestException`, parseo y `NVIDIAServiceError`.
- Validación de inputs antes de llamar a la API; `messages.error` con texto claro.

### UI
- `recommendation_form.html` con preselección de contexto y equipo.
- `recommendation.html` con `white-space: pre-wrap`.
- Nuevo `history.html` con accordion Bootstrap.
- Dropdown **Asesor IA** en `base.html` (navbar global).
- Botón "Pedir análisis IA del equipo" en `team_detail.html` (solo dueño).

---

## Fase 11: Gestión de Criaturas en Equipo y Mejoras de Navegación

### Añadir / quitar criaturas a un equipo
- `views.py`: `team_add_creature` (solo dueño, valida tope de 6, posición libre, no duplicados) y `team_remove_creature` (POST con CSRF).
- `urls.py`: `teams/<id>/creatures/add/` y `teams/<id>/creatures/<tc_id>/remove/`.
- **Plantilla nueva**: `teams/team_add_creature.html` con selector de criaturas disponibles, preview JS de stats, posiciones libres y lista de miembros actuales.
- `team_detail.html`: botón "Añadir criatura" (si dueño y <6) y botón eliminar por criatura con confirm.

### Menú de combate con elección de formato
- `battle_setup` ahora muestra menú con dos tarjetas: **Normal** y **Random**.
- **Normal** (`/battle/normal/`): selector de equipos del usuario, CPU genera equipo aleatorio del mismo tamaño.
- **Random** (`/battle/random/`): combate **6vs6** con criaturas aleatorias por ambos lados (POST + CSRF).
- Helpers: `_build_random_team`, `_init_battle_session`, `_team_view`, `_team_finished`, `_hp_color`.

### Refactor de combate a formato por equipos
- `battle_turn` y `battle_result` rediseñadas: cada bando guarda lista de criaturas con HP por slot e índice del combatiente activo.
- **Relevo automático** cuando el activo cae; el combate termina al agotar un equipo.
- `battle_arena.html`: cabecera con los slots de ambos equipos (activo, vivos, caídos).
- `battle_result.html`: estado final de cada equipo con supervivientes.

### Catálogo de criaturas
- `creature_list` (`/creatures/`): cuadrícula con nombre, tipos, descripción y stats.
- Plantilla nueva: `creatures/creature_list.html`.

### Navbar
- **Combates** → `battle_setup` (menú).
- **Criaturas** → `creature_list`.

### Notas
- Modo Random requiere ≥12 criaturas en BD; el botón se desactiva si no se cumple.

---

## Fase 12: Integración PokéAPI

### Objetivo
Importar datos reales de Pokémon desde PokéAPI a SQLite **una sola vez**, para que la app funcione siempre offline contra la base local.

### Cambios en el código

#### 1. Modelo `Creature` (`models.py:32-37`)
- Nuevo campo `pokemon_id: PositiveIntegerField`, `unique=True`, `null=True`, `blank=True`.
- **Propósito**: identificar criaturas importadas y mantener compatibilidad con criaturas custom/legacy.

#### 2. Admin (`admin.py:13-48`)
- **Listado**: añadidas columnas `pokemon_id` y `sprite_preview` (miniatura 48×48 desde `image_url`).
- **Búsqueda y fieldsets**: `pokemon_id` indexado y editable en el formulario.

#### 3. Management command nuevo (`import_pokemon.py`)
- **Endpoint**: `https://pokeapi.co/api/v2/pokemon/{id}/`, sin API key, con `requests`.
- **Flags**: `--start`, `--limit` (default 151), `--delay`, `--timeout`, `--replace`.
- **Idempotente**: `Creature.objects.update_or_create(pokemon_id=...)` evita duplicados.
- **Robusto**: captura `HTTPError`, `RequestException` y `ValueError` por Pokémon. Sigue el bucle y lista los IDs fallidos al final.
- **Mapeo**: `POKEAPI_TYPE_MAP` (18 tipos), stats limitados a 255, sprite preferido `official-artwork` con fallback a `front_default`, nombre capitalizado.
- **Progreso**: una línea por Pokémon (`#001 Bulbasaur grass/poison [nuevo]`) y resumen final con creados/actualizados/fallidos.

### Cómo se usa
```bash
python manage.py makemigrations myapp
python manage.py migrate
python manage.py import_pokemon            # 151 primeros
python manage.py import_pokemon --replace  # reemplazo total
```
> El resultado es visible en `/admin/myapp/creature/` con el sprite incluido.

### Decisiones de diseño
- **Importación offline-only**: las vistas no llaman a PokéAPI. Cumple el requisito universitario de simplicidad y rendimiento.
- **`pokemon_id` nullable**: no rompe registros existentes y separa "criaturas oficiales" de "custom".
- **Sin Django REST Framework**: solo `requests` + ORM.
- **Cortesía con la API pública**: `--delay 0.1s` entre peticiones.

### Vías de ampliación futura (preparadas conceptualmente)
- `import_moves`: usando `moves[].move.url` y `/api/v2/move/{id}/` para poblar `Move` y `CreatureMove` (con `level_learned_at`).
- `import_types`: desde `/api/v2/type/{name}/` para tabla de efectividades (requiere modelo `TypeEffectiveness`).
- `import_abilities`: desde `/api/v2/ability/{id}/` (requiere modelos `Ability` y `CreatureAbility`).
- `import_all`: orquestador que llame a los comandos anteriores con `call_command` en el orden correcto.

---

## Fase 13: API REST con `JsonResponse`

### Objetivo
Implementar una API REST básica utilizando únicamente las herramientas nativas de Django (`JsonResponse` y ORM), prescindiendo por completo de Django REST Framework (DRF) para mantener la ligereza del proyecto.

### Endpoints creados

#### 1. Lista de criaturas
- **Ruta**: `GET /api/creatures/`
- **Estructura de respuesta**: `{"creatures": [...], "total": N}`
- **Campos**: `id`, `name`, `type1`, `type2`, `hp`, `attack`, `defense`, `speed`, `pokemon_id`.

#### 2. Detalle de criatura
- **Ruta**: `GET /api/creatures/<id>/`
- **Estructura de respuesta**: objeto JSON con datos generales de la criatura y la relación de sus movimientos.
- **Campos**: `id`, `name`, `type1`, `type2`, stats, `pokemon_id`, `moves[]`.
- **Campos por movimiento**: `id`, `name`, `type`, `power`, `accuracy`.

#### 3. Lista de equipos públicos
- **Ruta**: `GET /api/teams/`
- **Estructura de respuesta**: `{"teams": [...], "total": N}`
- **Campos**: `id`, `name`, `user`, `created_at`, `updated_at`, `creatures_count`.

### Cambios realizados en el código
- **`views.py`**: añadido `JsonResponse` a las importaciones; 3 funciones de vista con serialización manual del ORM.
- **`urls.py`**: 3 nuevas rutas bajo el espacio de nombres `/api/`.

### Pruebas de funcionamiento
Endpoints disponibles para verificación en el navegador, Postman o cURL:
```
/api/creatures/
/api/creatures/1/
/api/teams/
```

---

## Fase 14: Suite de Pruebas Automatizadas (`tests.py`)

### Objetivo
Garantizar la estabilidad, la seguridad y el correcto funcionamiento del sistema mediante pruebas unitarias y de integración que validan los modelos, el flujo de autenticación, las vistas protegidas, las mecánicas de combate y los endpoints de la API REST.

### Cobertura de la Suite

#### 1. Pruebas de Modelos
- **`CreatureModelTests`**: validación de creación de registros, representación en cadena (`__str__`) y correcto despliegue/formato de tipos.
- **`TeamModelTests`**: verificación de creación de equipos y su representación en cadena.
- **`MoveModelTests`**: control de creación de movimientos y su representación en cadena.

#### 2. Pruebas de Autenticación
- **`AuthenticationTests`**: validación de flujos críticos: inicio de sesión exitoso, inicio de sesión fallido, registro de nuevas cuentas y cierre de sesión.

#### 3. Pruebas de Vistas Protegidas
- **`ProtectedViewTests`**: restricciones de acceso mediante login (redirección segura) y accesibilidad autorizada para Perfil, `my_teams` y `battle_setup`.

#### 4. Pruebas del Sistema de Combate
- **`CombatSystemTests`**: lógica de negocio del juego:
  - Verificación de que las criaturas tienen movimientos asignados.
  - Cálculo correcto del daño básico.
  - Creación e inicio de sesión de combate en `battle_setup`.
  - Restricción de turnos (`battle_turn`) condicionados a una sesión activa.

#### 5. Pruebas de la API REST
- **`APITests`**: listado general de criaturas, detalle individual, manejo correcto del 404 ante IDs inexistentes y listado de equipos públicos.

### Comandos de ejecución
```bash
# Ejecutar todos los tests de la aplicación
python3 manage.py test myapp

# Ejecutar únicamente un test específico (ejemplo: modelos de criaturas)
python3 manage.py test myapp.tests.CreatureModelTests
```

---

*PocketArena cubre actualmente: autenticación, modelos completos, admin avanzado, CRUD de equipos con gestión de criaturas, combate por equipos con IA local, integración con NVIDIA Build API, importación de datos reales desde PokéAPI, API REST nativa con `JsonResponse` y suite de pruebas automatizadas.*
