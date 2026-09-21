# Pulso — Seguimiento de proyectos

Aplicación web en español para registrar dedicación y avance de proyectos. Backend Flask, SQLite persistente, interfaz HTML con Bootstrap y diseño adaptable. El avance real se registra manualmente; las horas consumidas se calculan desde los registros.

## Cómo se ejecuta

Requiere Python 3.11 o posterior. Desde `tp-final`, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SECRET_KEY = & .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

Abrir http://127.0.0.1:5000. Acceso inicial: **admin / Proyecto1**. El primer ingreso exige cambiar la contraseña. Luego crear recursos, roles y proyectos para comenzar a registrar consumos. No se cargan proyectos ficticios en la base real.

La base se guarda en `instance/proyectos.sqlite`. Reiniciar el servidor conserva los datos. Repetir `init-db` crea objetos faltantes sin borrar datos ni restablecer contraseñas; no es un sistema de migraciones para futuras versiones del esquema. Para respaldar, detener el servidor y copiar el archivo SQLite.

`SECRET_KEY` es obligatoria y no se guarda en Git. Conservar el mismo valor en el entorno si se desea mantener sesiones entre reinicios; cambiarlo invalida sesiones. En una instalación futura bajo HTTPS, configurar `COOKIE_SECURE=1`. El servidor de desarrollo se utiliza únicamente en localhost. Bootstrap se obtiene por CDN; requiere conexión para sus estilos completos.

## Uso y permisos

| Acción | Usuario | Responsable del proyecto | Administrador |
|---|---|---|---|
| Consultar proyectos y consumos | Sí | Sí | Sí |
| Registrar/editar/eliminar consumo propio | Sí | Sí | Sí |
| Editar consumos ajenos | No | No | Sí |
| Editar datos, estado y avance de proyecto | No | Del propio proyecto | Sí |
| Crear/eliminar proyecto o reasignar responsable | No | No | Sí |
| Gestionar usuarios, contraseñas y roles | No | No | Sí |

Cada recurso es una cuenta; su nombre único es el usuario de acceso. Rol representa la función desempeñada en cada consumo. No se puede eliminar un registro con referencias ni dejar al sistema sin administradores. El avance manual (0–100) no cambia al cargar horas o cambiar el estado. Las horas pueden superar la estimación y las fechas previstas; el tablero muestra el exceso.

## Arquitectura y contrato

Fábrica `app.create_app`, blueprints para autenticación, proyectos, recursos, roles y consumos. `app/db.py` abre una conexión SQLite por solicitud y habilita claves foráneas. `app/schema.sql` define las tablas. Jinja genera HTML con escape automático; los formularios usan `application/x-www-form-urlencoded` y token CSRF. No hay API JSON ni frontend separado.

| Rutas | Métodos y comportamiento |
|---|---|
| `/login` | GET formulario, POST autentica |
| `/logout` | POST cierra sesión |
| `/password` | GET formulario, POST cambia contraseña propia |
| `/proyectos`, `/consumos`, `/recursos`, `/roles` | GET listados |
| `/proyectos/<id>` | GET detalle y agregados |
| `/<entidad>/nuevo`, `/<entidad>/<id>/editar` | GET formulario, POST valida y guarda |
| `/<entidad>/<id>/eliminar` | POST elimina si permisos e integridad lo permiten |

`/proyectos` acepta filtros GET `estado` y `responsable`. Los formularios conservan los nombres de columna definidos en la especificación. POST válido redirige; errores de validación vuelven a mostrar el formulario con mensaje. Se utiliza 403 para permisos insuficientes, 404 para registros inexistentes y 400 para CSRF inválido. Accesos sin sesión redirigen al login.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Cada prueba utiliza SQLite temporal y no altera la base local. Se cubren autenticación, cambio obligatorio, CSRF, permisos por solicitudes directas, CRUD, referencias, último administrador, entradas inválidas, avance 0/100, exceso de horas, totales, escape HTML, persistencia e inicialización idempotente.

## Qué decidí yo

- Flask con plantillas permite ejecutar y defender una sola aplicación, sin compilación de frontend.
- SQLite es suficiente para la primera versión local; claves foráneas y consultas parametrizadas aseguran integridad.
- Se agregan `consumo_id`, `es_admin` y `debe_cambiar_password` para identificar consumos y administrar acceso. Contraseñas almacenadas con scrypt de Werkzeug.
- Las modificaciones del último administrador se protegen dentro de una transacción SQLite de escritura.
- El porcentaje real es manual; usar horas gastadas como avance podría dar una lectura engañosa del trabajo terminado.

## Cómo gestioné el contexto

La especificación está en [docs/ESPECIFICACION.md](docs/ESPECIFICACION.md), el plan en [docs/PLAN.md](docs/PLAN.md) y las pruebas automatizadas expresan las reglas acordadas. Los módulos separan cada área funcional. El README conserva el contrato y las decisiones para continuar en futuras sesiones.

## Qué salió mal

La raíz del repositorio Git está por encima de `tp-final`. La solicitud para crear la rama fue rechazada porque requiere escribir en los metadatos del repositorio padre; quedó pendiente la evidencia de rama, commits y PR. Los archivos de aplicación y documentación se conservan dentro del trabajo práctico.
