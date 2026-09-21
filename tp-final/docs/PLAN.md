# Plan de implementación

1. Crear fábrica Flask, conexión SQLite por solicitud, esquema con restricciones y comando init-db idempotente.
2. Implementar autenticación, hashes, CSRF, cambio obligatorio y permisos con lectura del usuario actual desde la base.
3. Implementar recursos y roles; proteger referencias y al último administrador con transacción de escritura.
4. Implementar proyectos, consumos, filtros y agregados, separando avance manual del consumo de horas.
5. Construir interfaz en español con Bootstrap y estilos adaptables a escritorio/móvil.
6. Probar reglas, errores, permisos, CRUD, persistencia y recorrido visual; documentar ejecución y decisiones.
7. Conservar cambios en rama codex/seguimiento-proyectos, commits y PR si los permisos del repositorio lo permiten.

## Decisiones acordadas

Flask con plantillas, SQLite local, usuarios en recurso, rol laboral por consumo, administrador inicial, porcentaje manual y permisos según responsabilidad. Sin API JSON, entidad tarea separada ni publicación en Internet. El navegador envía formularios al mismo servidor.

## Restricción del entorno

La raíz Git es el directorio padre del trabajo práctico. La solicitud para crear la rama fue rechazada; no se modifican metadatos Git sin autorización. La implementación y sus verificaciones permanecen en tp-final.
