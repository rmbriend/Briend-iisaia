# API JSON de Pulso

Prefijo `/api`. Respuestas JSON excepto DELETE exitoso (204 sin cuerpo). El backend no renderiza HTML ni redirige al login. El frontend llama rutas relativas a su origen; el proxy reenvía a Flask.

## Autenticación y CSRF

1. `GET /api/session` devuelve `{ "user": null, "csrf_token": "..." }` y establece cookie de sesión.
2. `POST /api/login` recibe `{ "recurso_nombre": "admin", "password": "..." }`. Enviar cookie, `Content-Type: application/json` y `X-CSRF-Token` obtenido en el paso anterior.
3. La respuesta contiene `user` y un nuevo `csrf_token`. Actualizar el token tras login, logout y cambio de contraseña.
4. Todas las mutaciones (POST, PUT, DELETE) requieren cookie, token y objeto JSON. Para DELETE/logout, enviar `{}`.
5. `user` expone únicamente `recurso_id`, `recurso_nombre`, `es_admin`, `debe_cambiar_password`. Si el cambio está pendiente, solo se permiten session, login, logout y password.

| Método | Ruta | Entrada / salida |
|---|---|---|
| GET | `/api/session` | Usuario actual o null y token CSRF |
| POST | `/api/login` | Usuario/contraseña → sesión |
| POST | `/api/logout` | `{}` → usuario null y token nuevo |
| PUT | `/api/password` | `actual`, `password`, `confirmacion` → sesión actualizada |
| GET | `/api/catalogos` | `estados`, recursos (ID/nombre), roles (ID/descripción) |
| GET | `/api/proyectos` | Array; filtros opcionales `estado`, `responsable` |
| GET | `/api/proyectos/<id>` | `proyecto`, `consumos`, `por_recurso`, `por_rol` |
| POST | `/api/proyectos` | Crear, devuelve proyecto (201) |
| PUT | `/api/proyectos/<id>` | Reemplazar campos editables, devuelve proyecto (200) |
| DELETE | `/api/proyectos/<id>` | Eliminar (204) |
| GET | `/api/consumos` | Array de consumos con nombres de proyecto/recurso/rol |
| GET | `/api/consumos/<id>` | Consumo individual |
| POST / PUT / DELETE | `/api/consumos`, `/api/consumos/<id>` | Crear (201), actualizar (200), eliminar (204) |
| GET | `/api/recursos`, `/api/recursos/<id>` | Lista o recurso sin hash; solo administrador |
| POST / PUT / DELETE | `/api/recursos`, `/api/recursos/<id>` | Crear (201), actualizar (200), eliminar (204); solo administrador |
| GET | `/api/roles`, `/api/roles/<id>` | Lista o rol; solo administrador |
| POST / PUT / DELETE | `/api/roles`, `/api/roles/<id>` | Crear (201), actualizar (200), eliminar (204); solo administrador |

POST usa la colección; PUT y DELETE usan un ID. PUT recibe todos los campos editables; no es una actualización parcial.

## Cuerpos de escritura

- Proyecto: `proyecto_nombre`, `fecha_inicio`, `fecha_fin`, `horas_requeridas`, `owner_id`, `proyect_status`, `porcentaje_avance`. El responsable no administrador no puede cambiar owner_id; se conserva el actual.
- Consumo: `proyecto_id`, `recurso_id`, `fecha_inicio`, `fecha_fin`, `horas_consumidas`, `tarea`, `rol_id`. Para un usuario común, recurso_id siempre se obtiene de la sesión, ignorando el valor enviado.
- Recurso: `recurso_nombre`, `es_admin` (booleano, por defecto false), `password`. Al editar, omitir password o enviar cadena vacía conserva la contraseña; proporcionar una nueva exige cambio en el próximo acceso.
- Rol: `rol_descripcion`.

Fechas ISO `YYYY-MM-DD`. Horas positivas finitas. Avance 0–100. Los números e IDs pueden enviarse como números JSON o cadenas numéricas; no se aceptan booleanos, objetos o listas como valores numéricos. Textos obligatorios no pueden estar vacíos.

Las lecturas de proyectos incluyen `responsable`, `horas_consumidas`, `saldo`, `exceso` y `porcentaje_consumo`. El detalle agrega `por_recurso` y `por_rol` como objetos de nombre → horas. No se modifica porcentaje_avance al registrar horas.

## Errores

Formato uniforme: `{ "error": { "code": "validation_error", "message": "Mensaje legible" } }`.

- 400: validación, JSON malformado o CSRF inválido (`csrf_invalid`).
- 401: sesión ausente (`unauthorized`) o credenciales incorrectas (`invalid_credentials`).
- 403: permisos insuficientes, o cambio inicial pendiente (`password_change_required`).
- 404: registro/ruta inexistente. 405: método no permitido.
- 409: duplicados/referencias (`conflict`) o protección del último administrador (`last_admin`).
- 413: solicitud demasiado grande; límite 1 MiB. 415: falta Content-Type JSON.
- 502: el proxy no puede conectar con la API (`proxy_error`).

Los errores no generan reintentos automáticos de escritura. El frontend conserva el formulario para corregirlo, informa desconexiones y redirige al login o al cambio de contraseña según corresponda.
