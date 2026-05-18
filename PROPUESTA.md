# PROPUESTA.md

# PocketArena – Simulador web de combates por turnos

## Descripción general

PocketArena será una aplicación web desarrollada con Django inspirada en los simuladores de combate por turnos como Pokémon Showdown. La aplicación permitirá a los usuarios registrarse, crear equipos de pokémon y participar en combates contra equipos controlados por la aplicación.

Además del sistema de combate, la plataforma incluirá funcionalidades sociales básicas, como compartir equipos públicamente, consultar perfiles de usuario y visualizar el historial de partidas.

El objetivo del proyecto es aplicar los contenidos de la asignatura en una aplicación interactiva y dinámica que combine gestión de usuarios, persistencia de datos, arquitectura web y consumo de APIs externas.

---

## Tecnologías y herramientas

* Python 3
* Django
* SQLite3
* HTML5 + CSS + Bootstrap
* HTMX para actualización dinámica de contenido
* JSON para intercambio de datos
* Sistema de autenticación y sesiones de Django

### API externa

Se utilizará la plataforma NVIDIA Build para integrar funcionalidades de inteligencia artificial generativa, como:

* recomendaciones estratégicas,
* sugerencias de equipos,
* análisis simple de combates,
* generación de comentarios automáticos.

---

## Funcionalidades principales

* Registro e inicio de sesión de usuarios.
* Creación y gestión de equipos.
* Sistema de combate por turnos.
* Historial de combates.
* Página de perfil de usuario.
* Visualización pública de equipos compartidos.
* Panel de administración mediante Django Admin Site.

---

## Modelo de datos preliminar

### Usuario

Información de autenticación y perfil del jugador.

### Pokémon

Datos básicos de cada pokémon:

* nombre,
* tipo,
* estadísticas,
* movimientos.

### Equipo

Conjunto de pokémon asociadas a un usuario.

### Movimiento

Ataques disponibles para las pokémon.

### Combate

Registro de partidas realizadas:

* participantes,
* resultado,
* fecha,
* estadísticas básicas.

### MensajeIA

Recomendaciones o comentarios generados mediante la API externa.

---

## Objetivos técnicos

El proyecto buscará cubrir entre el 70 % y el 80 % de los contenidos vistos en la asignatura, incluyendo:

* arquitectura MVC,
* desarrollo web con Django,
* uso de plantillas y herencia,
* autenticación y sesiones,
* persistencia con bases de datos,
* consumo de APIs externas,
* generación dinámica de contenido,
* diseño responsive.
