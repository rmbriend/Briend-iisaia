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

---

# Plan de replataforma (2026-09-23): FastAPI + Vue + PostgreSQL

## Motivo

La versión anterior se diseñó como una aplicación local. El nuevo objetivo es hostearla para un equipo chico y sumar las funcionalidades del roadmap (`FEATURE_PLAN.md`): reporting de plan vs. ejecución, desvíos y proyecciones, cargas masivas, Gantt y alertas por correo. El stack tenía tres limitaciones para eso:

- no había migraciones de esquema (solo `CREATE TABLE IF NOT EXISTS`);
- el frontend se armaba concatenando `innerHTML`, lo que no escala a vistas complejas;
- SQLite y un proxy artesanal no alcanzan para un despliegue real.

## Decisiones (acordadas con el usuario)

| Tema | Decisión | Motivo |
|---|---|---|
| Backend | FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic | Tipos y OpenAPI automáticos (cliente tipado para el frontend) y migraciones versionadas |
| Base de datos | PostgreSQL 16 | Escrituras concurrentes con varios workers, bloqueos de fila y backups con `pg_dump` |
| Frontend | Vue 3 + TypeScript + Vite, Pinia y TanStack Query | Componentes para vistas complejas (Gantt, reportes) con una curva de aprendizaje suave |
| Autenticación | Sesión por cookie en el servidor + CSRF | Es lo más seguro para una SPA del mismo origen; mantiene el diseño anterior |
| Infraestructura | Docker Compose + Caddy | HTTPS automático, un solo origen y portable a cualquier VPS |
| Estilos | Se mantuvo el CSS propio + Bootstrap | Paridad visual; PrimeVue y ECharts se evaluarán en la Fase 5 |
| Gantt (Fase 5) | Componente propio `<ProjectGantt>` que envuelve SVAR Gantt o frappe-gantt | Poder cambiar de librería sin tocar las páginas |

## Fases

1. **Fundamentos:** `backend/` con uv, compose de desarrollo, migración base de Alembic y CI. ✔
2. **Paridad del backend:** el mismo contrato de API.md, la suite Flask portada, `init-db` e `import-sqlite`. ✔
3. **Paridad del frontend:** las mismas pantallas y reglas en Vue, con pruebas Vitest y Playwright. ✔
4. **Despliegue:** Caddy, `compose.prod.yaml` y backups; se retira la versión Flask. ✔
5. **Funcionalidades:** reporting → CSV → Gantt → alertas (worker + SMTP). **Pendiente para una fecha futura.**
6. **Documentación:** README, API, especificación, este plan y la validación. ✔

## Compatibilidad

- Se conservan los nombres de tablas, columnas y rutas de la API.
- Cambios visibles en el contrato:
  - `es_admin` y `debe_cambiar_password` son booleanos JSON;
  - `responsable` no numérico devuelve 400;
  - un ID de ruta no numérico devuelve 404;
  - los 500 siempre se devuelven como JSON.
- Los datos existentes se importan con `import-sqlite`, conservando IDs y contraseñas.
- La interfaz de desarrollo pasa al puerto 5173 (Vite) y la API sigue en el 5000.
