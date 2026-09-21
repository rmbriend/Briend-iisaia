# Pulso — Frontend web y API de proyectos

Aplicación en español para registrar dedicación y avance de proyectos, dividida en dos componentes:

- **Frontend:** HTML, JavaScript nativo (módulos ES) y CSS en `frontend/`. Consume JSON con `fetch`; no utiliza plantillas Jinja ni necesita compilarse. Bootstrap aporta estilos base.
- **Backend:** API Flask en `app/`, sin páginas HTML. SQLite persiste los datos en `instance/proyectos.sqlite`.

## Ejecutar

Requiere Python 3.11 o posterior. Desde `tp-final`, preparar una vez:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Terminal 1 — API, puerto 5000:**

```powershell
$env:SECRET_KEY = & .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

**Terminal 2 — frontend, puerto 8000:**

```powershell
.\.venv\Scripts\python.exe frontend/server.py
```

Abrir **http://127.0.0.1:8000**. El puerto 5000 expone únicamente la API. En una instalación nueva el acceso es **admin / Proyecto1**, con cambio obligatorio de contraseña. Si ya tenías usuarios, contraseñas o proyectos, seguí utilizando los existentes: esta separación no cambia el esquema ni borra datos.

El servidor del frontend sirve archivos estáticos y reenvía `/api/*` al backend. Así el navegador usa un solo origen para la interfaz, cookies y CSRF. No hay acceso a SQLite ni reglas de negocio en ese servidor. En un futuro despliegue se puede sustituir por un servidor estático con proxy inverso; no hace falta reescribir el frontend. Ejecutar los servidores de desarrollo solo en localhost.

Puertos alternativos: `python frontend/server.py --port 8000 --api-port 5000`. Para el backend, usar `flask run --port PUERTO`. No abrir `index.html` mediante `file://`: necesita HTTP y el proxy de API.

## Configuración y persistencia

`SECRET_KEY` es obligatoria y no se guarda en Git. Conservar su valor entre reinicios mantiene las sesiones; generar uno nuevo obliga a iniciar sesión otra vez. Si se usa HTTPS en otro entorno, configurar `COOKIE_SECURE=1`. Bootstrap se carga desde CDN y requiere conexión para sus estilos completos.

La base sigue en `instance/proyectos.sqlite`. `init-db` es idempotente: no borra datos ni restablece contraseñas. No se requiere migración para esta versión. Para respaldar, detener el backend y copiar el archivo SQLite. No ejecutar simultáneamente la versión anterior y esta sobre la misma base durante la transición.

## Permisos y reglas

| Acción | Usuario | Responsable del proyecto | Administrador |
|---|---|---|---|
| Consultar proyectos y consumos | Sí | Sí | Sí |
| Registrar/editar/eliminar consumo propio | Sí | Sí | Sí |
| Editar consumos ajenos | No | No | Sí |
| Editar datos, estado y avance de proyecto | No | Del propio proyecto | Sí |
| Crear/eliminar proyecto o reasignar responsable | No | No | Sí |
| Gestionar usuarios, contraseñas y roles | No | No | Sí |

Cada recurso es una cuenta; su nombre único es el usuario. Rol es la función en cada consumo. El avance manual de 0 a 100 es independiente del estado y las horas. Se admiten consumos por encima de la estimación o fuera de las fechas previstas. No se eliminan registros con referencias ni al último administrador.

## Arquitectura

```text
Navegador: frontend/index.html + app.js + api.js + ui.js + styles.css
    │ fetch('/api/...'), JSON, cookie HttpOnly, X-CSRF-Token
    ▼
Servidor estático / proxy local :8000 (frontend/server.py)
    │ /api/*
    ▼
API Flask :5000 (app/)
    │ consultas parametrizadas, permisos, validación
    ▼
SQLite (instance/proyectos.sqlite)
```

El frontend controla navegación, formularios, mensajes y renderizado con valores escapados. Flask verifica todos los permisos aunque se invoque directamente la API; nunca devuelve hashes de contraseñas. No se almacenan credenciales ni tokens de sesión en localStorage.

Los módulos de Flask separan autenticación, proyectos, consumos, recursos y roles. `db.py` abre una conexión por solicitud con claves foráneas activas. Los totales se calculan en el backend. El contrato está en [docs/API.md](docs/API.md).

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
node --test tests/frontend.test.mjs
```

Node 20+ solo se necesita para ejecutar las pruebas de JavaScript, no para usar la aplicación. Python prueba contrato JSON, login/logout, CSRF, permisos, CRUD, integridad, validaciones, agregados, inicialización, persistencia y el proxy HTTP real. JavaScript prueba escape de entradas, cookies, CSRF y manejo de errores. Las pruebas utilizan bases temporales.

## Decisiones y contexto

La especificación funcional permanece en [docs/ESPECIFICACION.md](docs/ESPECIFICACION.md), la separación está documentada en [docs/PLAN.md](docs/PLAN.md) y los resultados en [docs/VALIDACION.md](docs/VALIDACION.md). La versión inicial usaba Flask/Jinja; esta versión retira las plantillas y reemplaza formularios POST/redirect por API REST JSON y navegación JavaScript.

Se mantiene Flask y SQLite para aprovechar los datos y reglas existentes. El proxy permite separar procesos sin guardar tokens en el navegador ni habilitar CORS amplio. Las contraseñas siguen usando scrypt de Werkzeug y los catálogos públicos para usuarios autenticados incluyen solo IDs y nombres necesarios para seleccionar recursos y roles.

## Evidencia Git

No se crearon ramas, commits ni PR desde esta sesión: la escritura de metadatos del repositorio padre no fue autorizada anteriormente. La copia externa `tp-final - Flask` no se modifica.
