# Especificación funcional

Aplicación local de seguimiento de proyectos, en español, con Flask, HTML, Bootstrap y SQLite.

## Entidades

- Proyecto: proyecto_id, proyecto_nombre, fecha_inicio, fecha_fin, horas_requeridas, owner_id, proyect_status, porcentaje_avance.
- Recurso/usuario: recurso_id, recurso_nombre único (login), password (hash), es_admin y debe_cambiar_password.
- Consumo: consumo_id, proyecto_id, recurso_id, fecha_inicio, fecha_fin, horas_consumidas, tarea y rol_id.
- Rol: rol_id y rol_descripcion única. Es una función laboral, no un permiso.

El responsable referencia un recurso registrado. Las referencias se protegen con claves foráneas y eliminación restrictiva. Se conserva el nombre `proyect_status` solicitado. Estados: pendiente, en curso, pausado y finalizado.

## Reglas de negocio

El avance real es manual de 0 a 100, independiente del estado y del consumo. Horas requeridas y consumidas: positivas y finitas. Fechas obligatorias, inicio no posterior al fin. Se permiten horas por encima de la estimación y fuera del período previsto. Saldo = requeridas − consumidas; exceso = máximo(consumidas − requeridas, 0); porcentaje de consumo = consumidas / requeridas × 100. Los totales se calculan desde los consumos actuales.

## Acceso

Todos los usuarios autenticados consultan proyectos y consumos; los usuarios comunes crean, editan y eliminan consumos propios. El responsable edita su proyecto salvo la asignación del responsable. El administrador administra todo, incluidos recursos y roles, creación/eliminación de proyectos y reasignaciones. Debe quedar al menos un administrador. Se verifican permisos en el servidor.

La inicialización de una base vacía crea admin / Proyecto1 y exige cambiar esa contraseña. Nuevos usuarios y contraseñas restablecidas también requieren cambio. La inicialización no sobrescribe cuentas. Contraseñas con hash scrypt de Werkzeug, mínimo 8 caracteres para nuevas contraseñas. Todas las mutaciones requieren POST y CSRF. Sin recuperación por correo ni despliegue público.

## Interfaz y aceptación

Tablero con filtros de estado/responsable, tarjetas, horas y avance real; detalle con consumos y totales por recurso/rol. Formularios con errores comprensibles y preservación de entradas no sensibles. Diseño adaptable a móvil. Aceptación: CRUD, login/logout, permisos directos, CSRF, integridad, porcentajes límite, recálculo, persistencia e inicialización repetible.
