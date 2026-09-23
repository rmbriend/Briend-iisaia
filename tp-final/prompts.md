# Registro de prompts y acciones — Pulso (tp-final)

Registro cronológico de cada prompt enviado al asistente (Claude Code) y de las acciones que tomó en respuesta. Los prompts se transcriben textualmente. Complementa a [HISTORIAL_DESARROLLO.md](HISTORIAL_DESARROLLO.md), que resume las etapas anteriores (versión Flask/Jinja y separación frontend/backend).

Formato de cada entrada: prompt textual → acciones (lecturas, preguntas, decisiones, archivos modificados, comandos, resultados).

---

## Sesión 2026-09-23 — Revisión de arquitectura y replataforma

### Prompt 1 — Inicio de la revisión de arquitectura (modo plan)

> I am focusing on tp-final. Look through what's already done. I am planning on reviewing architecture to improve it. The project is a project management app with front and back end. It's main focus is to be simple and easy to use but also useful for project management. Let's start discussing technologies.

**Acciones:**

1. Se leyó el código y la documentación existentes sin modificar nada: `app/schema.sql`, `app/__init__.py`, `app/common.py`, `app/projects.py`, `frontend/index.html`, `frontend/app.js`, `frontend/api.js`, `frontend/server.py`, `frontend/styles.css`, `docs/PLAN.md`, `docs/ESPECIFICACION.md`, `docs/HISTORIAL_DESARROLLO.md`, `docs/Presentacion_de_idea.pdf` y `../FEATURE_PLAN.md`.
2. Diagnóstico presentado:
   - **Fortalezas:** CSRF, cookies HttpOnly, hash scrypt, contrato de errores JSON uniforme, permisos verificados en el servidor y buena cobertura de pruebas (pytest + node).
   - **Brechas:** no hay mecanismo de migraciones de esquema (`schema.sql` solo usa `CREATE TABLE IF NOT EXISTS`); el frontend arma las vistas con cadenas `innerHTML`, lo que no escala a Gantt ni reportes; el proxy `server.py` es artesanal; la especificación dice "local, sin despliegue público, sin correo", lo que choca con las alertas por mail del roadmap.
   - Se relacionó cada ítem de `FEATURE_PLAN.md` (reporting, Gantt, cargas masivas, alertas, proyecciones, desvíos) con la tecnología que necesita.
3. Primera ronda de preguntas al usuario:

| Pregunta | Respuesta |
|---|---|
| ¿Restricciones del curso sobre el stack? | Totalmente abierto |
| ¿Dónde se ejecuta Pulso? | Preparado para un equipo chico: hosteado y con despliegue real |
| ¿Dirección del frontend? | Vite + framework |
| ¿Qué funcionalidades primero? | Todas: reporting/desvíos/proyecciones, Gantt, cargas CSV, alertas por mail |

4. Segunda ronda:

| Pregunta | Respuesta |
|---|---|
| Framework backend | Migrar a FastAPI |
| Framework frontend | El usuario preguntó: *"how good is vue3 for complex components like gantts?"* |
| Base de datos e infraestructura | Postgres + Docker Compose |

5. Respuesta sobre Vue 3 y los Gantt: el framework influye poco, porque los Gantt serios son librerías JS con wrappers para cada framework. Se compararon frappe-gantt (MIT, simple), SVAR Gantt (núcleo MIT, con versión para Vue), vue-ganttastic (básico) y DHTMLX/Bryntum (licencia GPL o comercial). Se recomendó Vue 3 con un componente propio `<ProjectGantt>` que envuelva la librería, para poder reemplazarla después.
6. Tercera ronda:

| Pregunta | Respuesta |
|---|---|
| Framework frontend | Vue 3 + TypeScript |
| Autenticación | Sesión por cookie + CSRF (sesiones del lado del servidor) |

7. Se redactó y aprobó el plan de replataforma (archivo de plan del asistente). Resumen:
   - **Backend:** FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic, psycopg 3, sesiones en Postgres, argon2 (con verificación de hashes scrypt heredados y re-hash al iniciar sesión), `uv` y ruff.
   - **Frontend:** Vue 3 + TS, Vue Router, Pinia, TanStack Query, cliente tipado generado desde OpenAPI, PrimeVue y ECharts, Gantt envuelto en un componente propio.
   - **Infraestructura:** Caddy (HTTPS, sirve el build y hace de proxy de `/api`, reemplaza a `server.py`), API en uvicorn, un worker para alertas, Postgres 16 con backups, Mailpit en desarrollo y GitHub Actions.
   - **Fases:** 1) fundamentos; 2) paridad del backend (mismo contrato de `docs/API.md`, pruebas portadas, script de importación SQLite → Postgres); 3) paridad del frontend; 4) despliegue; 5) funcionalidades (reporting → CSV → Gantt → alertas); 6) documentación.
8. Plan aprobado; empieza la Fase 1. Verificación de herramientas locales: `uv` 0.12.5, Python 3.14, Node 22, npm 10 y podman 5.8. No hay `docker`, y `podman compose` no tiene un proveedor de compose instalado. Se leyó `docs/API.md` completo como contrato a preservar.

### Prompt 2 — Registro obligatorio de prompts

> One important thing. this repo is for a tp-final so every prompt and step needs to be recorded. For this generate a markdown prompts.md with this information. reflect what we've done and update your instructions to log on that file for every action. Then, continue with the plan

**Acciones:**

1. Se creó este archivo, `tp-final/prompts.md`, con lo realizado hasta ahora.
2. Se agregó a `CLAUDE.md` (raíz del repo) la regla de registrar en este archivo cada prompt y cada acción.
3. Se guardó la misma regla en la memoria persistente del asistente, para que se aplique en sesiones futuras.
4. Se continúa con la Fase 1 del plan (ver entradas siguientes).

#### Fase 1 — Fundamentos (ejecutada a continuación del Prompt 2)

1. **Herramientas:** como no hay Docker, se usa podman en modo rootless. Se instaló `podman-compose` 1.6.0 como herramienta de usuario (`uv tool install podman-compose`).
2. **Proyecto backend** (`tp-final/backend/`), gestionado con `uv` (Python 3.13):
   - `pyproject.toml`: FastAPI, uvicorn, Pydantic v2, pydantic-settings, SQLAlchemy 2, psycopg 3 y Alembic; dependencias de desarrollo pytest, httpx y ruff (comillas simples, líneas de 110). También `uv.lock` y `.python-version`.
   - `pulso/config.py`: configuración por variables de entorno (`SECRET_KEY` de al menos 32 caracteres, `DATABASE_URL`, `COOKIE_SECURE`, duración de la sesión).
   - `pulso/db.py`: engine, sessionmaker y la dependencia `get_db` (una sesión por request).
   - `pulso/models.py`: modelos ORM que replican el esquema SQLite original con los mismos nombres en español, incluido `proyect_status`, y las mismas restricciones CHECK y claves foráneas RESTRICT. `COLLATE NOCASE` se reemplazó por índices únicos sobre `lower(...)`. Se agregó la tabla `sesion` para las sesiones del lado del servidor.
   - `pulso/main.py`: fábrica `create_app()` con los encabezados de seguridad, el contrato de errores `{"error": {code, message}}` (validación → 400, IntegrityError → 409, HTTP → `http_<código>`) y `GET /api/health`. OpenAPI en `/api/docs`. `pulso/asgi.py` es el punto de entrada de uvicorn.
   - Alembic: `alembic.ini` y `migrations/env.py`, que toma la URL de `DATABASE_URL` y no necesita `SECRET_KEY`. La migración base `0001_esquema_base.py` se autogeneró y se revisó.
   - Error corregido durante el trabajo: los índices case-insensitive se habían escrito con literales de texto en lugar de columnas. Se reescribieron después de cada clase.
3. **Infraestructura de desarrollo:** `tp-final/compose.yaml` con `db` (Postgres 16), `mailpit` y `api` (uvicorn con `--reload`, que corre `alembic upgrade head` al iniciar). También `backend/Dockerfile` (python:3.13-slim + uv) y `.dockerignore`.
   - Problema: `podman-compose` interpola todo el archivo, así que `${SECRET_KEY:?}` impedía levantar incluso `db`. Se cambió a `${SECRET_KEY:-}`; la API valida la clave al arrancar.
4. **Pruebas** (`backend/tests/`): cada corrida crea una base Postgres temporal, le aplica las migraciones y la elimina al terminar. Las pruebas verifican health, error 404 en JSON, que las migraciones coincidan con los modelos (`compare_metadata`), que se pueda hacer downgrade y upgrade, y la unicidad sin distinguir mayúsculas.
   - Resultado: `uv run pytest -q` → **5 passed**; `ruff check` y `ruff format --check` sin errores.
5. **Verificación con contenedores:** `podman compose up -d --build api`; `curl /api/health` → `{"status":"ok"}`; los logs muestran `Running upgrade -> 0001, esquema base` y `\dt` lista las tablas `consumo`, `proyecto`, `recurso`, `rol`, `sesion` y `alembic_version`.
6. **CI:** `.github/workflows/tp-final.yml` (en la raíz del repo) corre `uv sync`, `ruff check`, `ruff format --check` y pytest contra un servicio Postgres 16. Se agregó `.ruff_cache/` a `tp-final/.gitignore`.
7. El backend Flask original (`app/`) y el frontend actual siguen funcionando sin cambios. Se retirarán después de alcanzar la paridad (Fases 2–4).

#### Consulta sobre Git

Se preguntó al usuario cómo manejar la evidencia de Git que pide el curso (ramas, commits y PRs). Respuesta: **"Branch + commit per phase"**. Se crea la rama `replatform-fastapi-vue` y se hace al menos un commit por fase; el usuario abre los PR.

#### Fase 2 — Paridad del backend (en curso)

1. Se leyeron los módulos Flask que faltaban (`auth.py`, `resources.py`, `roles.py`, `consumptions.py`, `db.py`) y la suite `tests/test_app.py` con su `conftest.py`, que funcionan como especificación ejecutable.
2. Se corrió la suite Flask original como línea de base. Antes hubo que instalar `requirements-dev.txt` en `.venv`. Resultado: **66 passed**.
3. Se revisó qué espera el frontend actual: solo usa la veracidad de `es_admin` y `debe_cambiar_password` y los códigos `unauthorized`, `password_change_required` y `csrf_invalid`. Decisión: la API nueva devuelve booleanos JSON (`true`/`false`) en lugar de `1`/`0`.
4. Se agregaron las dependencias `pwdlib[argon2]` y `werkzeug`; esta última solo para verificar los hashes scrypt heredados.
5. Archivos nuevos en `backend/pulso/`:
   - `errors.py`: `APIError` y el formato de error.
   - `security.py`: argon2, verificación de hashes heredados con re-hash, y tokens.
   - `sessions.py`: sesiones del lado del servidor en la tabla `sesion`. La cookie `pulso_session` es HttpOnly y SameSite=Lax, y en la base se guarda solo el hash SHA-256 del token. Las sesiones anónimas duran 2 h y las vencidas se limpian al crear una nueva. El guard se aplica a nivel de router en el mismo orden que Flask: 401 → 403 por cambio de contraseña pendiente → 400 CSRF → 415 → 400 si el cuerpo no es un objeto. También define `current_user` y `require_admin`.
   - `schemas.py`: validadores Pydantic que reproducen las reglas de `common.py` con los mismos mensajes (rechazan booleanos, NaN e infinito y aceptan cadenas numéricas), más los modelos de entrada y salida para OpenAPI.
   - `queries.py`: consultas de proyectos con sus agregados y de consumos con nombres.
   - `routers/auth.py`, `routers/projects.py`, `routers/consumptions.py`, `routers/resources.py`, `routers/roles.py`: el mismo contrato de `docs/API.md`. Los permisos se chequean como dependencias antes de validar el cuerpo, para que un 403 tenga prioridad sobre un 400 (igual que en Flask). La regla del último administrador usa `SELECT … FOR UPDATE`. Cambiar o restablecer una contraseña cierra las otras sesiones de ese usuario.
   - `main.py`: registra los routers; también maneja los 500 no controlados (siempre como JSON), el límite de 1 MiB (413) y los errores de validación de Pydantic, que se traducen a los mensajes en español. Un parámetro de ruta inválido devuelve 404.
   - `cli.py`: `init-db` (migra y crea admin/Proyecto1 solo si la base está vacía) e `import-sqlite` (copia la base Flask conservando IDs y hashes, y ajusta las secuencias).
6. Errores corregidos durante la escritura: en `detail()` quedaba una expresión inválida (`if False else`) y un `filter_by` que apuntaba a la tabla equivocada. Además, `create` agregaba el proyecto a la sesión antes de validar la referencia, con riesgo de autoflush.

### Prompt 3 — Alcance (mensaje enviado durante el trabajo)

> Once we end phase 4 let's stop. Phase 5 will remain for future date. but do phase 6 (documentation)

**Acciones:** se ajustó el alcance. Se completan las Fases 2, 3 y 4 y luego la Fase 6 (documentación). La Fase 5 (reporting, CSV, Gantt y alertas) queda pendiente para más adelante.

#### Fase 2 — Resultados

1. Pruebas: `backend/conftest.py` suma el fixture `seeded`, con los mismos datos que la suite Flask, y los helpers `login`, `mutate`, `post` y `scalar`. `backend/tests/test_api.py` porta **todas** las pruebas de `tests/test_app.py` y agrega otras nuevas:
   - flags de la cookie de sesión y login sin distinguir mayúsculas;
   - cierre de las otras sesiones al cambiar la contraseña;
   - aceptación y re-hash a argon2 de un hash werkzeug heredado;
   - mensajes de validación en español;
   - orden de catálogos sin distinguir mayúsculas;
   - `responsable` no numérico → 400, e ID de ruta no numérico → 404;
   - límite de 413 y errores 500 no controlados siempre como JSON.
2. Resultado: `uv run pytest -q` → **78 passed** en el primer intento; `ruff check` y `ruff format` sin errores (tras ajustar tres líneas largas y usar la sintaxis de genéricos de Python 3.12).
3. Importación real: se copió `instance/proyectos.sqlite` al scratchpad (el original no se tocó) y se importó en una base Postgres descartable con `python -m pulso.cli import-sqlite`. Resultados:
   - Filas: 1 recurso, 3 roles, 1 proyecto y 1 consumo.
   - Agregados idénticos: 560 h requeridas, 12 h consumidas, saldo 548.
   - Las secuencias quedaron ajustadas (el próximo `rol_id` es 4) y el hash scrypt heredado se conservó.
   - `init-db` posterior no creó otro admin.
   - La base descartable se eliminó al terminar.
4. `compose.yaml` y el `Dockerfile` ahora ejecutan `python -m pulso.cli init-db` al arrancar (migración + admin inicial). Log del contenedor: "Base inicializada. Usuario inicial: admin / Proyecto1."
5. Compatibilidad: el frontend **actual** (`frontend/server.py`, puerto de prueba 8010) funcionó sin cambios contra la API FastAPI. Sesión, login y bloqueo por cambio de contraseña pendiente (`password_change_required`) respondieron igual que con Flask.
