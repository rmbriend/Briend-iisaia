# Plan de separación frontend / backend

## Objetivo

Reemplazar la interfaz renderizada en Flask por un frontend independiente en HTML, JavaScript y CSS, conservando SQLite, usuarios, proyectos y reglas funcionales.

## Implementación

1. Convertir blueprints Flask a API `/api`, con JSON, códigos HTTP y serialización explícita que excluye hashes.
2. Mantener cookies HttpOnly y CSRF; bootstrap de sesión y token por GET, renovación en login/logout/cambio de contraseña.
3. Crear frontend con módulos ES: cliente HTTP, componentes seguros y navegación/formularios. Mantener pantallas, permisos visibles y diseño adaptable.
4. Retirar plantillas Jinja y mover estilos al frontend. Servirlo como componente separado con proxy `/api` al backend, sin lógica de negocio.
5. Migrar pruebas funcionales al contrato JSON y agregar pruebas del cliente y del proxy.
6. Validar ambos componentes en navegador con base temporal; iniciar la aplicación real conservando la base existente.
7. Actualizar documentación de ejecución y contrato. No realizar operaciones Git que requieran la autorización rechazada anteriormente.

## Compatibilidad

No hay cambio de esquema ni reinicialización destructiva. La URL de la interfaz pasa al puerto 8000; el 5000 contiene solamente API. Cambiar SECRET_KEY al reiniciar invalida sesiones, pero mantiene cuentas, contraseñas y datos. Los endpoints HTML anteriores se reemplazan por el contrato documentado en API.md.
