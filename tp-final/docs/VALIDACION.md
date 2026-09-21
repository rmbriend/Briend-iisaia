# Validación de la separación frontend / API

## Automatizada

- `python -m pytest -q tests/test_app.py`: 66 pruebas aprobadas de API JSON, permisos, CRUD, validaciones, CSRF, hashes no expuestos, integridad, agregados y persistencia.
- `python -m pytest -q tests/test_frontend_server.py`: 2 pruebas aprobadas del servidor estático/proxy con llamadas HTTP reales, cookies, login, escrituras y API desconectada.
- `node --test tests/frontend.test.mjs`: 2 pruebas aprobadas del cliente JavaScript: escape de entradas, JSON, cookies, renovación CSRF, DELETE 204 y errores de red/servidor sin reintentar escrituras.
- Compilación Python y comprobación de sintaxis de los tres módulos JavaScript.

## Navegador

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

## Historial

La versión inicial Flask/Jinja tuvo 49 pruebas aprobadas; esa suite fue adaptada al contrato JSON, por lo que los conteos no se suman. En esta versión se retiran las plantillas y la navegación por formularios HTML del backend.
