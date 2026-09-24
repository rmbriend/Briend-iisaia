# Pulso — Seguimiento de proyectos y dedicación

Aplicación web en español para registrar la dedicación del equipo y seguir el avance de los proyectos. Está pensada para un equipo chico y busca ser **simple de usar, pero útil** para gestionar proyectos.

Tiene dos componentes independientes:

- **Frontend** (`frontend/`): Vue 3 + TypeScript, compilado con Vite. Usa Vue Router, Pinia y TanStack Query, y un cliente HTTP **tipado a partir del esquema OpenAPI** de la API.
- **Backend** (`backend/`): API JSON con FastAPI, SQLAlchemy 2 y migraciones Alembic sobre **PostgreSQL 16**. No genera páginas HTML.

En producción, **Caddy** sirve el frontend compilado, termina HTTPS y reenvía `/api/*` a la API, de modo que el navegador trabaja con un solo origen (cookie de sesión + CSRF).

## Arquitectura

```text
Navegador (SPA Vue, archivos estáticos)
   │ mismo origen · cookie HttpOnly pulso_session · encabezado X-CSRF-Token
   ▼
Caddy — HTTPS automático, CSP, sirve dist/ y hace proxy de /api/*       (desarrollo: servidor Vite)
   ▼
API FastAPI (uvicorn, N workers) — autenticación, permisos, validación, agregados
   ▼
PostgreSQL 16 (+ backup diario con pg_dump)
```

- El frontend maneja la navegación, los formularios y los mensajes. Vue escapa todo el contenido; no se usa `v-html`. No se guardan credenciales ni tokens en `localStorage`.
- La API verifica **todos** los permisos, aunque se la llame directamente, y nunca devuelve hashes de contraseñas. Los totales (saldo, exceso, % de consumo) se calculan en el backend.
- **Sesiones** del lado del servidor, en la tabla `sesion`. La cookie solo lleva un token aleatorio; en la base se guarda su hash SHA-256. El token CSRF se renueva en login, logout y cambio de contraseña.
- **Contraseñas** con argon2id. Los hashes scrypt de la versión Flask se aceptan y se re-hashean automáticamente en el siguiente login.
- Contrato HTTP: [docs/API.md](docs/API.md). Documentación interactiva: `/api/docs`, y esquema en `/api/openapi.json`.

```text
backend/
  pulso/main.py          create_app(): routers, contrato de errores, límites y encabezados
  pulso/sessions.py      sesiones, CSRF y guard aplicado a cada router
  pulso/schemas.py       validación de entrada (Pydantic) y modelos de respuesta
  pulso/models.py        modelos ORM (nombres de tablas y columnas originales)
  pulso/routers/         auth, projects, consumptions, resources, roles
  pulso/cli.py           init-db, import-sqlite
  migrations/            Alembic
frontend/
  src/api/               cliente tipado (schema.d.ts se genera desde openapi.json)
  src/views/, components/, stores/, composables/, router.ts
  e2e/                   pruebas Playwright sobre el stack real
deploy/                  Caddyfile e imagen web
compose.yaml             entorno de desarrollo (Postgres, Mailpit, API)
compose.prod.yaml        stack de producción
```

## Desarrollo local

Requisitos: [uv](https://docs.astral.sh/uv/), Node 22+ y Docker o Podman con compose. Todo se ejecuta desde `tp-final/`.

```bash
# 1. Base de datos (Postgres en localhost:5432) y Mailpit (http://localhost:8025)
docker compose up -d db mailpit          # o: podman compose up -d db mailpit

# 2. API en http://127.0.0.1:5000 (migra y crea admin/Proyecto1 si la base está vacía)
cd backend
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
uv run python -m pulso.cli init-db
uv run uvicorn pulso.asgi:app --reload --port 5000

# 3. Frontend en http://127.0.0.1:5173 (el servidor de Vite reenvía /api a la API)
cd ../frontend
npm install
npm run dev
```

La API también puede correr en un contenedor: `SECRET_KEY=... docker compose up -d api`. En una instalación nueva el acceso es **admin / Proyecto1** y el sistema obliga a cambiar la contraseña en el primer ingreso. `init-db` es idempotente: aplica las migraciones pendientes y nunca borra datos ni restablece contraseñas.

Cuando cambia la API, hay que regenerar los tipos del frontend con `npm run gen:api`. CI falla si `openapi.json` o `src/api/schema.d.ts` quedaron desactualizados.

### Migrar los datos de la versión Flask/SQLite

```bash
cd backend
uv run python -m pulso.cli import-sqlite ../instance/proyectos.sqlite
```

El comando importa sobre una base vacía: conserva IDs, fechas y hashes y ajusta las secuencias. Si la base destino ya tiene datos, se niega a importar. El archivo SQLite se abre en modo solo lectura.

## Despliegue (equipo chico)

```bash
cp .env.example .env       # completar SECRET_KEY, POSTGRES_PASSWORD y PULSO_DOMAIN
docker compose -f compose.prod.yaml --env-file .env up -d --build
```

- `web`: Caddy obtiene el certificado HTTPS de `PULSO_DOMAIN` (los puertos 80 y 443 tienen que ser accesibles). Aplica CSP estricta, HSTS, límite de 1 MB para `/api` y caché inmutable para los assets con hash.
- `api`: aplica las migraciones al arrancar y usa cookies `Secure`. El número de procesos se ajusta con `API_WORKERS`.
- `db`: PostgreSQL con volumen persistente.
- `backup`: espera a que la API haya migrado la base, luego guarda un `pg_dump --clean --if-exists` comprimido por día en `./backups` y conserva `BACKUP_DAYS` días. Si un dump falla, se descarta y se registra `backup FAILED`.

Para restaurar (también sirve sobre una instalación nueva, ya inicializada por `init-db`):

```bash
docker compose -f compose.prod.yaml stop api
gunzip -c backups/pulso-AAAA-MM-DD.sql.gz | docker compose -f compose.prod.yaml exec -T db psql -U pulso pulso
docker compose -f compose.prod.yaml start api
```

Cambiar `SECRET_KEY` no invalida las sesiones, que viven en la base de datos. Para cerrar todas las sesiones, vaciar la tabla `sesion`.

## Permisos y reglas

| Acción | Usuario | Responsable del proyecto | Administrador |
|---|---|---|---|
| Consultar proyectos y consumos | Sí | Sí | Sí |
| Registrar/editar/eliminar consumo propio | Sí | Sí | Sí |
| Editar consumos ajenos | No | No | Sí |
| Editar datos, estado y avance de proyecto | No | Del propio proyecto | Sí |
| Crear/eliminar proyecto o reasignar responsable | No | No | Sí |
| Gestionar usuarios, contraseñas y roles | No | No | Sí |

- Cada recurso es una cuenta, y su nombre único (sin distinguir mayúsculas) es el usuario.
- El rol es la función desempeñada en cada consumo, no un permiso.
- El avance manual va de 0 a 100 y es independiente del estado y de las horas.
- Se admiten consumos por encima de la estimación o fuera de las fechas previstas.
- No se pueden eliminar registros con referencias ni al último administrador. Esta regla está protegida con bloqueos de fila frente a pedidos concurrentes.
- Al cambiar o restablecer una contraseña se cierran las otras sesiones de esa cuenta.

## Pruebas

```bash
docker compose up -d db                         # las pruebas del backend crean bases temporales en este Postgres
cd backend && uv run pytest -q                  # 78 pruebas: contrato, permisos, CSRF, validación, integridad, migraciones
uv run ruff check . && uv run ruff format --check .
cd ../frontend && npm test                      # Vitest: cliente HTTP, escape, permisos en tablas, navegación
npx playwright install chromium && npm run test:e2e   # Playwright: flujos completos sobre API + base e2e aislada
```

El workflow de CI `.github/workflows/tp-final.yml` corre todo lo anterior y además construye las imágenes.

## Qué funcionó y qué no

**Funcionó:**
- La suite Flask se portó completa y actuó como especificación ejecutable: el contrato JSON se mantuvo, y el frontend anterior funcionó sin cambios contra la API nueva antes de reemplazarlo.
- La importación de la base SQLite real reprodujo exactamente los agregados.
- El stack de producción se verificó localmente: HTTPS, CSP sin errores en el navegador, cookies `Secure`, 413 y backup.

**Limitaciones y pendientes:**
- Los booleanos de usuario ahora son `true`/`false` en lugar de `1`/`0`.
- Un JSON mal formado devuelve 400 antes que el 401 de sesión ausente.
- La **Fase 5** queda para más adelante: reporting (desvíos y proyecciones), cargas masivas por CSV, Gantt y alertas por correo (worker + SMTP; Mailpit ya está disponible en desarrollo). Ver [docs/PLAN.md](docs/PLAN.md).

## Documentación y proceso

- [docs/ESPECIFICACION.md](docs/ESPECIFICACION.md): especificación funcional.
- [docs/API.md](docs/API.md): contrato HTTP.
- [docs/PLAN.md](docs/PLAN.md): planes y decisiones de arquitectura.
- [docs/VALIDACION.md](docs/VALIDACION.md): resultados de validación.
- [HISTORIAL_DESARROLLO.md](HISTORIAL_DESARROLLO.md): historia de las etapas anteriores.
- [prompts.md](prompts.md): registro textual de cada prompt y cada acción de esta etapa.

**Evidencia Git:** la replataforma se hizo en la rama `replatform-fastapi-vue`, con un commit por fase. La copia `tp-final - Flask/` se conserva sin cambios como referencia histórica.
