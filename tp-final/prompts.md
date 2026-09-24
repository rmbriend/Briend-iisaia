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

#### Fase 3 — Paridad del frontend (Vue 3 + TypeScript)

1. Se leyó completo el frontend anterior (`app.js`, `ui.js` y `styles.css`) para reproducir pantallas, textos y reglas.
2. **Desviación del plan, justificada:** en esta fase de paridad **no** se incorporó PrimeVue. Se portó el diseño propio existente (CSS propio sobre Bootstrap, ahora empaquetado desde npm en lugar del CDN) para mantener la apariencia idéntica y un bundle chico. PrimeVue y ECharts quedan para la Fase 5, donde se necesitan tablas de datos, cargas de archivos y gráficos.
3. Proyecto Vite en `tp-final/frontend/`:
   - Dependencias: Vue 3.5, Vue Router 5, Pinia 4, TanStack Query, openapi-fetch y Bootstrap. De desarrollo: Vite 8, vue-tsc, Vitest, @vue/test-utils, jsdom, openapi-typescript y Playwright.
   - npm instaló TypeScript 7, pero openapi-typescript pide `^5.x`, así que se fijó **TypeScript ~5.9.3**.
4. **Contrato tipado:** `backend/pulso/openapi.py` exporta el esquema sin necesitar base de datos. `npm run gen:api` genera `openapi.json` y `src/api/schema.d.ts`. CI verifica que los tipos generados estén actualizados.
5. Código:
   - `src/api/client.ts`: cliente con token CSRF rotado solo en mutaciones y mapeo al contrato de errores. Los errores de red o de respuesta inválida tienen mensajes en español y nada se reintenta automáticamente.
   - `stores/session.ts` (Pinia).
   - `composables/notice.ts`: misma reacción a errores que antes (401 → login, `password_change_required` → cambio de contraseña, `csrf_invalid` → renovar el token sin reintentar).
   - `composables/submit.ts`: los formularios conservan lo ingresado si hay error.
   - `router.ts`: se relee la sesión en cada navegación y las reglas de redirección están en `redirectFor`.
   - Componentes: `AppHeader`, `PageHeading`, `StatGrid`, `ProgressBar`, `LoadState`, `TextField`, `SelectField`, `FormShell`, `DeleteButton` y `ConsumptionTable`.
   - 12 vistas con las mismas rutas que antes. Vue escapa todo el contenido y nunca se usa `v-html`.
6. Ajustes durante el trabajo:
   - Se quitó `novalidate` para conservar la validación nativa del navegador.
   - `DeleteButton` ahora navega antes de invalidar la caché, para no volver a pedir un registro ya eliminado.
   - El cliente usa como `baseUrl` el origen de la página, porque en Node `Request` exige URL absolutas.
   - `fetch` se resuelve en cada llamada, porque openapi-fetch lo capturaba al crearse y los tests no podían reemplazarlo.
7. **Pruebas:**
   - `vue-tsc` sin errores y `npm run build` OK (bundle principal de ~30 kB gzip).
   - Vitest: **9 passed**. Cubren el cliente (CSRF, 204, errores sin reintento, red y respuesta inválida), el escape de contenido hostil y los permisos en la tabla de consumos, y las reglas de navegación.
   - Playwright (Chromium headless) sobre el stack real: la API en el puerto 5001 con la base `pulso_e2e` recreada en cada corrida (`e2e/start-api.sh`) y Vite con proxy. Resultado: **5 passed**. Cubren cambio forzado de contraseña; alta de usuario, rol y proyecto (con nombre hostil escapado); usuario común registrando horas con un error de fechas que conserva el formulario, exceso de 5,5 h y avance manual intacto; redirección desde rutas de admin; logout; recarga de una URL profunda; eliminación, y login en móvil sin scroll horizontal.
   - Fallas en las propias pruebas, ya corregidas: Vite escuchaba en IPv6 (se agregó `--host 127.0.0.1`), un selector ambiguo "Nueva contraseña" (se usa `exact`) y una carrera en el helper de login (ahora espera la redirección).
8. Revisión visual con capturas de login, proyectos y detalle: el diseño coincide con la versión anterior.
9. Se eliminaron `frontend/app.js`, `api.js`, `ui.js` y `server.py` y sus pruebas (`tests/frontend.test.mjs` y `tests/test_frontend_server.py`). `styles.css` pasó a `src/styles/main.css`. CI suma el job `frontend` (tipos generados, build, Vitest y Playwright).

#### Fase 4 — Despliegue

1. Archivos nuevos:
   - `deploy/Caddyfile`: HTTPS automático (en `localhost` usa la CA local de Caddy) y proxy de `/api/*` a `api:5000` con límite de cuerpo de 1 MB. Sirve la SPA con `try_files` hacia `index.html` y los encabezados CSP (sin scripts en línea), HSTS, `X-Frame-Options` y `nosniff`. Los assets con hash llevan caché inmutable y las páginas `no-cache`.
   - `deploy/web.Dockerfile`: build de Vue con Node 22 y resultado copiado a una imagen `caddy:2-alpine`.
   - `compose.prod.yaml` con cuatro servicios:
     - `web` (Caddy);
     - `api`: `init-db` + uvicorn con `--workers` y `--proxy-headers`, `COOKIE_SECURE=1`, y `SECRET_KEY`/`POSTGRES_PASSWORD` obligatorios;
     - `db` (Postgres 16 con healthcheck);
     - `backup`: `pg_dump` diario comprimido en `./backups` con retención de `BACKUP_DAYS` días.
   - `.env.example` (plantilla de secretos y dominio) y `.dockerignore`. Se agregaron `backups/`, `frontend/node_modules/` y `frontend/dist/` a `.gitignore`.
   - El servicio `worker` para las alertas se difiere a la Fase 5, junto con la funcionalidad que lo necesita.
2. **Verificación local del stack de producción** con podman (proyecto `pulso-prod`, puertos 8080/8443 y un `.env` descartable en el scratchpad):
   - Las cuatro imágenes y contenedores levantaron.
   - `/proyectos/1` → 200 con CSP, HSTS y `X-Frame-Options: DENY`; `/assets/*.js` → `immutable`.
   - Login por HTTPS → cookie `pulso_session` con `HttpOnly; SameSite=lax; Secure`. Cuerpo de 1,1 MB → **413**; `/api/docs` → 200.
   - El servicio de backup generó `pulso-2026-09-24.sql.gz`.
   - Chromium (Playwright) sobre `https://localhost:8443`: redirección a login, login y cambio de contraseña forzado, estilos cargados y **sin errores de CSP ni de consola**.
   - Hallazgo corregido: las URL profundas de la SPA no recibían `Cache-Control: no-cache`, porque el matcher evaluaba la ruta original. Se cambió a `not path /assets/*`. Además `podman-compose up --build` no recreaba el contenedor y hubo que usar `--force-recreate`.
   - Al terminar se eliminaron los contenedores, volúmenes y el backup de prueba.
3. **Retiro de la versión Flask** (ya verificada la paridad): se eliminaron `app/`, `requirements.txt`, `requirements-dev.txt` y `tests/` (la suite Flask ya está portada en `backend/tests/`). Siguen disponibles en el historial de Git y en la copia congelada `tp-final - Flask/`. **No** se tocó `instance/proyectos.sqlite`, que son datos del usuario y la fuente para `import-sqlite`. El `.venv` viejo de la raíz de tp-final quedó sin usar y no se borró.
4. CI suma el job `images`, que construye las imágenes de la API y la web después de backend y frontend.
5. La suite del backend sigue en **78 passed** sin el paquete Flask.
6. Aparte: se detectó que `FEATURE_PLAN.md` (en la raíz del repo) tiene cambios del usuario, con estados de avance. No se incluyeron en los commits del asistente.

#### Fase 6 — Documentación

1. `README.md` reescrito: stack, diagrama y mapa de carpetas; desarrollo local (compose + uv + Vite); importación desde SQLite; despliegue con `compose.prod.yaml` (incluida la restauración de backups); matriz de permisos; pruebas; qué funcionó y qué no; enlaces a la documentación y evidencia Git.
2. `docs/API.md`:
   - proxy Caddy/Vite, OpenAPI en `/api/docs`, sesiones en el servidor con su duración, y cierre de las demás sesiones al cambiar la contraseña;
   - booleanos JSON, `/api/health`, `responsable` no numérico → 400, ID de ruta no numérico → 404, 500 siempre como JSON, y nota sobre los 502 del proxy;
   - el orden de las verificaciones (por qué 403 gana sobre 400).
   - Autocorrección: primero se había escrito que un 502 se informa como error de conexión, pero el cliente muestra el mensaje genérico. Se corrigió el texto.
3. `docs/ESPECIFICACION.md`: aplicación web hosteada, argon2 con migración de hashes, secciones nuevas de Despliegue y "Próximas funcionalidades (Fase 5, pendiente)".
4. `docs/PLAN.md`: se agregó el plan de replataforma (motivo, tabla de decisiones, fases con su estado y compatibilidad). El plan anterior se conserva como historia.
5. `docs/VALIDACION.md`: resultados nuevos (78 + 9 + 5 pruebas, migración de datos, stack de producción y revisión visual). La validación anterior queda en una sección histórica.
6. `HISTORIAL_DESARROLLO.md` y `docs/HISTORIAL_DESARROLLO.md` (hay dos copias idénticas): sección 19, que resume esta etapa y remite a `prompts.md`.
7. `CLAUDE.md` en la raíz del repo, ignorado por Git y por lo tanto solo local: se reescribieron la arquitectura, la ejecución y las pruebas de tp-final para el stack nuevo.
8. **Estado final:** Fases 1, 2, 3, 4 y 6 completas. La Fase 5 (reporting, CSV, Gantt y alertas) queda pendiente, según lo pedido en el Prompt 3.

#### Revisión final — Verificación real de los backups

1. La revisión final (advisor) señaló que el backup se había dado por verificado sin estarlo. El primer dump (370 bytes) probablemente corrió antes de que la API migrara la base; en `pg_dump | gzip && echo ok` el `&&` solo evalúa gzip, así que un fallo quedaba oculto; y la restauración documentada chocaría con las tablas y el admin que crea `init-db`.
2. Corrección en `compose.prod.yaml`: el servicio `backup` espera a que exista `alembic_version`, usa `set -o pipefail`, escribe a un `.tmp` y lo renombra solo si el dump tuvo éxito (si no, registra `backup FAILED`), y usa `pg_dump --clean --if-exists`.
3. Verificación con un stack de producción descartable:
   - El primer dump automático contiene las 6 tablas.
   - Por la API se cambió la contraseña del admin a `Respaldo123` y se crearon un rol y un proyecto; el dump (el mismo comando que el loop) incluye sus datos.
   - `down -v`, stack nuevo (con `init-db` sembrando su propio admin) y restauración con el comando del README: **sin errores**. El login con `Respaldo123` dio 200, el proyecto "Proyecto respaldado" volvió y quedó 1 solo recurso.
4. Se actualizaron la sección de restauración del README (detener `api`, restaurar, iniciar `api`) y `docs/VALIDACION.md`, que ahora refleja lo realmente verificado. Luego se eliminaron los contenedores, volúmenes, backups y el `.env` de prueba.
5. Notas para el usuario (sin acción): el workflow de CI nunca se ejecutó, porque la rama no se subió; siguen corriendo los contenedores de desarrollo (`db`, `mailpit` y `api` en :5000); quedaron instalados `podman-compose` (herramienta de uv) y Chromium de Playwright (~114 MB); el `.venv` viejo de tp-final quedó sin uso; `SECRET_KEY` sigue siendo obligatoria, pero la API actual no la usa porque las sesiones viven en la base.
