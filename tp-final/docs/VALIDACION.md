# Validación de la primera entrega

## Automatizada

Resultado final: `python -m pytest -q` — **49 pruebas aprobadas**. Compilación Python y `git diff --check` sin errores.

Suite pytest con bases SQLite temporales: autenticación, cambio inicial obligatorio, CSRF, permisos directos GET/POST, CRUD, validación, referencias, protección del último administrador, filtros, agregados, escape HTML, persistencia e inicialización repetida.

Durante la primera ejecución se detectó que el comando init-db requería un contexto Flask. Se corrigió agregando with_appcontext y se verificó el comando con FlaskCliRunner.

## Navegador

Revisión realizada contra un servidor local con una base temporal separada de la base del usuario:

- Ingreso con la cuenta de prueba y visualización del tablero en escritorio.
- Creación de un proyecto con 40 horas requeridas y 35 % de avance manual.
- Registro de 12,5 horas desde el detalle del proyecto; comprobación de la preselección del proyecto.
- Confirmación del saldo de 27,5 horas y totales por recurso y rol, conservando el avance manual en 35 %.
- Revisión a 390 × 844 píxeles: navegación, tarjetas y resúmenes adaptables; tabla con desplazamiento horizontal. Se ajustó su ancho mínimo para evitar palabras excesivamente partidas.

La revisión visual usa datos descartables; no se agregaron esos proyectos ni consumos a instance/proyectos.sqlite. La contraseña inicial de la instalación real queda pendiente de cambio por el usuario.

## Limitación de entrega

Rama, commits y PR pendientes: la escritura de metadatos Git en el directorio padre no fue autorizada.
