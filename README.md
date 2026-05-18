# Entrega convocatoria mayo

## Datos

* Nombre: Diego Lucas Luis
* Titulación: Grado en Ingeniería en Sistemas Audiovisuales y Multimedia
* Cuenta en laboratorios: dlucas
* Cuenta URJC: d.lucas.2021
* Vídeo básico (URL):
* Vídeo parte opcional (URL):
* Despliegue (URL): https://final-ltaw.onrender.com
* Usuarios y contraseñas: user / password123
* Cuenta Admin Site: admin / admin123

## Nombre del proyecto

**PocketArena** — Simulador web de combates por turnos inspirado en Pokémon Showdown, con datos reales importados desde PokéAPI y recomendaciones generadas por la API de NVIDIA Build.

## Recursos y métodos HTTP

### Páginas públicas
* `/` — Página de inicio
  * Métodos permitidos: GET
* `/login/` — Inicio de sesión
  * Métodos permitidos: GET, POST
* `/logout/` — Cierre de sesión
  * Métodos permitidos: POST
* `/register/` — Registro de nuevos usuarios
  * Métodos permitidos: GET, POST
* `/creatures/` — Catálogo público de pokémon
  * Métodos permitidos: GET

### Perfil y equipos (requieren login)
* `/profile/` — Perfil con estadísticas del usuario
  * Métodos permitidos: GET
* `/teams/` — Listado público de equipos (con buscador)
  * Métodos permitidos: GET
* `/teams/my/` — Equipos del usuario actual
  * Métodos permitidos: GET
* `/teams/create/` — Crear nuevo equipo
  * Métodos permitidos: GET, POST
* `/teams/<id>/` — Detalle de un equipo
  * Métodos permitidos: GET
* `/teams/<id>/edit/` — Editar un equipo (solo dueño)
  * Métodos permitidos: GET, POST
* `/teams/<id>/delete/` — Borrar un equipo (solo dueño)
  * Métodos permitidos: GET, POST
* `/teams/<id>/creatures/add/` — Añadir pokémon a un equipo
  * Métodos permitidos: GET, POST
* `/teams/<id>/creatures/<tc_id>/remove/` — Quitar pokémon de un equipo
  * Métodos permitidos: POST

### Sistema de combate
* `/battle/` — Menú de selección de formato (Normal / Random)
  * Métodos permitidos: GET
* `/battle/normal/` — Configuración de combate Normal (equipo del usuario vs CPU)
  * Métodos permitidos: GET, POST
* `/battle/random/` — Inicio de combate Random 6vs6 aleatorio
  * Métodos permitidos: POST
* `/battle/turn/` — Procesado de un turno (admite peticiones HTMX)
  * Métodos permitidos: GET, POST
* `/battle/result/` — Resultado final del combate
  * Métodos permitidos: GET

### Asesor IA
* `/ai/recommendation/` — Solicitud de recomendación (combate o equipo)
  * Métodos permitidos: GET, POST
* `/ai/history/` — Historial de recomendaciones del usuario
  * Métodos permitidos: GET

### API REST (JsonResponse, sin DRF)
* `/api/creatures/` — Listado de pokémon en JSON
  * Métodos permitidos: GET
* `/api/creatures/<id>/` — Detalle de una pokémon con sus movimientos
  * Métodos permitidos: GET
* `/api/teams/` — Listado de equipos públicos
  * Métodos permitidos: GET

### Administración
* `/admin/` — Django Admin Site personalizado
  * Métodos permitidos: GET, POST

## Resumen parte obligatoria

PocketArena cubre aproximadamente el **75%** de los contenidos exigidos por la asignatura mediante las siguientes funcionalidades:

* **Arquitectura MVC con Django**: separación clara entre modelos (`myapp/models.py`), vistas (`myapp/views.py`) y plantillas (`templates/`). Sistema de plantillas con herencia desde `base.html`, bloques, etiquetas (`{% url %}`, `{% if %}`, `{% for %}`, `{% csrf_token %}`) y filtros.
* **Autenticación y perfiles de usuario**: sistema completo con registro (`CustomUserCreationForm`), inicio de sesión, cierre de sesión y página de perfil con estadísticas (equipos creados, combates jugados, victorias y derrotas). Decorador `@login_required` para proteger las vistas privadas.
* **CRUD de Equipos con permisos**: creación, listado, detalle, edición y borrado de equipos. La creación requiere estar autenticado, y la edición/borrado están restringidos al dueño. Cada equipo puede marcarse como público o privado a través del flag `is_public`.
* **Sistema de combate por turnos**: combates con IA local que selecciona movimientos aleatorios, cálculo de daño basado en las estadísticas de las pokémon, orden de ataque por velocidad y persistencia del estado del combate (HP, activo, log) en `request.session`.
* **Panel de administración Django mejorado**: inlines (`TeamCreatureInline`, `BattleTurnInline`), filtros avanzados por tipo y categoría, barra de búsqueda, `autocomplete_fields`, `date_hierarchy`, `list_editable` y columnas calculadas dinámicamente (duración, número de pokémon, miniaturas de sprites).
* **Integración con API externa**: consumo real de la **NVIDIA Build API** (`meta/llama-3.1-8b-instruct`) para generar recomendaciones estratégicas de equipos y consejos en combate, accesibles desde el menú "Asesor IA" de la barra de navegación.
* **Diseño responsive mobile-first**: maquetación con Bootstrap 5.3 y hojas de estilo CSS personalizadas (`static/css/style.css`) con variables de tema y paleta para los 18 tipos elementales. La interfaz se adapta dinámicamente: el menú se colapsa y las tarjetas se reorganizan en pantallas pequeñas.
* **Despliegue en la nube**: aplicación desplegada en Render (`https://final-ltaw.onrender.com`) con `gunicorn` como servidor WSGI y `whitenoise` para servir los archivos estáticos.

Todas las fases del desarrollo están documentadas paso a paso en el archivo `FASES.md`.

## Lista partes opcionales

* **HTMX para funcionalidades dinámicas**: integración de HTMX (cargado desde `base.html` por CDN) en el sistema de combate para procesar los turnos mediante actualizaciones parciales del DOM sin recargas completas. La barra de HP se anima progresivamente con transiciones CSS estilo Pokémon (`bg-success` → `bg-warning` → `bg-danger`), mejorando notablemente la experiencia de usuario.
* **Suite de pruebas automatizadas**: archivo `myapp/tests.py` organizado en 5 categorías diferenciadas que garantizan la estabilidad y seguridad del sistema:
  * Pruebas de modelos (`CreatureModelTests`, `TeamModelTests`, `MoveModelTests`)
  * Pruebas de autenticación (`AuthenticationTests`)
  * Pruebas de vistas protegidas (`ProtectedViewTests`)
  * Pruebas del sistema de combate (`CombatSystemTests`)
  * Pruebas de la API REST (`APITests`)

  Se ejecutan con `python3 manage.py test myapp`.
* **Integración con múltiples APIs externas en paralelo**:
  * **NVIDIA Build API** (`myapp/services/nvidia_service.py`): servicio aislado `NVIDIABuildService` con manejo de errores robusto, configuración mediante `.env` y persistencia de respuestas en el modelo `AIMessage`.
  * **PokéAPI**: importación masiva de pokémon reales mediante el management command `import_pokemon`, idempotente vía `update_or_create`, con flags `--start`, `--limit`, `--delay`, `--replace`.
* **API REST nativa con `JsonResponse`**: endpoints estructurados (`/api/creatures/`, `/api/creatures/<id>/`, `/api/teams/`) implementados exclusivamente con `JsonResponse` y el ORM de Django, sin depender de Django REST Framework para mantener el proyecto ligero.
* **Management commands personalizados**: comandos de consola creados expresamente para facilitar la configuración inicial y la carga automatizada de datos:
  * `import_pokemon`: importa Pokémon desde PokéAPI.
  * `import_moves`: importa los movimientos asociados desde PokéAPI.
  * `create_users`: crea los usuarios de demostración (`user` y `admin`).

Estas funcionalidades opcionales demuestran un dominio avanzado del ecosistema Django, buenas prácticas de desarrollo y una calidad técnica que va más allá de los requisitos mínimos.

## Instalación y ejecución local

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py import_pokemon            # importa los 151 originales desde PokéAPI
python3 manage.py createsuperuser           # opcional, para acceder al admin
python3 manage.py runserver
```

Variables de entorno en `.env` (opcional, solo para el Asesor IA):

```
NVIDIA_API_KEY=tu_clave
NVIDIA_API_URL=https://integrate.api.nvidia.com/v1/chat/completions
NVIDIA_API_MODEL=meta/llama-3.1-8b-instruct
```

## Tecnologías utilizadas

* **Backend**: Python 3, Django, SQLite3
* **Frontend**: HTML5, CSS3, Bootstrap 5.3, HTMX
* **APIs externas**: PokéAPI, NVIDIA Build (Llama 3.1 8B)
* **Despliegue**: Render, Gunicorn, WhiteNoise
* **Testing**: framework de tests nativo de Django
