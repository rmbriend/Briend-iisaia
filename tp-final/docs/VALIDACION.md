# Validación

## Replataforma FastAPI + Vue + PostgreSQL (2026-09-23)

### Automatizada

- **Backend** (`cd backend && uv run pytest -q`): **78 pruebas aprobadas**, cada corrida sobre una base Postgres temporal.
  - Incluye toda la suite Flask portada: contrato JSON, login/logout, CSRF en POST/PUT/DELETE, permisos directos, CRUD, validaciones límite, integridad referencial, último administrador, duplicados sin distinguir mayúsculas, agregados, IDs no reutilizados, hashes nunca expuestos, JSON inválido o que no es un objeto, 415 e inicialización idempotente.
  - Pruebas nuevas:
    - flags de la cookie de sesión y login sin distinguir mayúsculas;
    - cierre de otras sesiones al cambiar la contraseña;
    - aceptación y re-hash de hashes werkzeug heredados;
    - mensajes de validación en español y orden de catálogos;
    - 404 por ID no numérico, 413 y 500 siempre como JSON;
    - que las migraciones Alembic coincidan con los modelos, y downgrade/upgrade.
- `ruff check` y `ruff format --check`: sin observaciones.
- **Frontend:** `vue-tsc` sin errores, `vite build` correcto y Vitest con **9 pruebas aprobadas**. Cubren el cliente HTTP (CSRF rotado solo en mutaciones, cookies del mismo origen, 204, errores sin reintento, errores de red y respuestas inválidas), el escape de nombres y tareas hostiles, las acciones según permisos y las reglas de navegación.
- **E2E** (`npm run test:e2e`, Playwright + Chromium, API real con una base `pulso_e2e` recreada en cada corrida): **5 pruebas aprobadas**.
  1. Cambio de contraseña obligatorio en el primer ingreso, con el bloqueo de otras rutas.
  2. El administrador crea un recurso, un rol y un proyecto; el nombre hostil se muestra escapado.
  3. Un usuario común registra horas: un error de fechas conserva el formulario, se registran 25,5 h sobre 20 h (exceso de 5,5 h) sin alterar el avance manual del 40 %, se lo redirige desde una ruta de admin y cierra sesión.
  4. Recarga de una URL profunda y eliminación de un consumo.
  5. Login en un teléfono (Pixel 7) sin scroll horizontal.

### Migración de datos

La base real `instance/proyectos.sqlite` se copió y se importó en una base Postgres descartable. Se importaron 1 recurso, 3 roles, 1 proyecto y 1 consumo. Los agregados coinciden: 560 h requeridas, 12 h consumidas y saldo de 548 h. La secuencia de IDs quedó ajustada y el hash heredado se conservó; un `init-db` posterior no creó otro administrador. Además, el frontend anterior funcionó sin cambios contra la API FastAPI.

### Stack de producción (local, podman)

`compose.prod.yaml` en los puertos 8080/8443 con dominio `localhost`:

- HTTPS con la CA local de Caddy.
- CSP, HSTS y `X-Frame-Options` en las páginas.
- Assets con caché inmutable y páginas con `no-cache`.
- Cookie `Secure`, 413 para cuerpos de más de 1 MB y `/api/docs` accesible.
- Backup diario generado.
- En Chromium: login y cambio de contraseña forzado sin errores de CSP ni de consola.

Los contenedores y volúmenes de prueba se eliminaron al terminar.

### Revisión visual

Capturas de login, listado y detalle de proyecto: el diseño coincide con la versión anterior.

---

## Versión anterior: separación frontend / API Flask (histórico)

### Automatizada

- `python -m pytest -q tests/test_app.py`: 66 pruebas aprobadas de API JSON, permisos, CRUD, validaciones, CSRF, hashes no expuestos, integridad, agregados y persistencia.
- `python -m pytest -q tests/test_frontend_server.py`: 2 pruebas aprobadas del servidor estático/proxy con llamadas HTTP reales, cookies, login, escrituras y API desconectada.
- `node --test tests/frontend.test.mjs`: 2 pruebas aprobadas del cliente JavaScript: escape de entradas, JSON, cookies, renovación CSRF, DELETE 204 y errores de red/servidor sin reintentar escrituras.
- Compilación Python y comprobación de sintaxis de los tres módulos JavaScript.

### Navegador

Revisión contra frontend y API separados en puertos de prueba, con SQLite temporal:

- Login desde HTML/JavaScript y carga del tablero mediante API.
- Creación de proyecto con 20 horas y 40 % de avance manual.
- Intento de consumo con cero horas: error visible sin perder datos del formulario.
- Consumo de 25,5 horas fuera del período previsto: exceso de 5,5 horas y avance manual conservado en 40 %.
- Recarga de URL de detalle: rutas del frontend y sesión siguen funcionando.
- Alta y edición de rol mediante POST y PUT JSON.
- Filtro por estado sin resultados y limpieza del filtro.
- Revisión a 390 × 844 píxeles: navegación, indicadores y filtros sin desbordamiento horizontal de página.

Los datos de prueba no se cargan en la base del usuario. No se cambia el esquema de SQLite ni se restablecen contraseñas existentes. La interfaz pasa al puerto 8000 y la API al 5000.

### Historial

La versión inicial Flask/Jinja tuvo 49 pruebas aprobadas; esa suite fue adaptada al contrato JSON, por lo que los conteos no se suman. En esta versión se retiran las plantillas y la navegación por formularios HTML del backend.
