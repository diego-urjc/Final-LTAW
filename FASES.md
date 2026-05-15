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

## Fase 5: Datos de Ejemplo (Management Command)
- **Archivos**: `myapp/management/__init__.py`, `myapp/management/commands/__init__.py`, `myapp/management/commands/load_sample_data.py`.
- **12 criaturas** balanceadas: Flamisaur, Aquatix, Verdantix, Electroz, Psikix, Rocadon, Glacix, Dragox, Normix, Voladrix, Venomix, Fantasmix.
- **20 movimientos** de 10 tipos (Fuego, Agua, Planta, Eléctrico, Normal, Psíquico, Roca, Tierra, Hielo, Dragón).
- **Lógica**: limpia `CreatureMove/Creature/Move`, recrea movimientos y criaturas, asigna 4 movimientos por criatura con `level_learned`, logs de progreso.
- **Uso**: `python manage.py load_sample_data`.

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

## Fase 9: Integración con NVIDIA Build API

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

## Fase 10: Gestión de Criaturas en Equipo y Mejoras de Navegación

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

*PocketArena cubre actualmente: autenticación, modelos completos, admin avanzado, CRUD de equipos con gestión de criaturas, combate por equipos con IA local, integración con NVIDIA Build API y navegación completa.*
