CREATE TABLE IF NOT EXISTS recurso (
 recurso_id INTEGER PRIMARY KEY AUTOINCREMENT,
 recurso_nombre TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK(length(trim(recurso_nombre)) > 0),
 password TEXT NOT NULL,
 es_admin INTEGER NOT NULL DEFAULT 0 CHECK(es_admin IN (0,1)),
 debe_cambiar_password INTEGER NOT NULL DEFAULT 1 CHECK(debe_cambiar_password IN (0,1))
);
CREATE TABLE IF NOT EXISTS rol (
 rol_id INTEGER PRIMARY KEY AUTOINCREMENT,
 rol_descripcion TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK(length(trim(rol_descripcion)) > 0)
);
CREATE TABLE IF NOT EXISTS proyecto (
 proyecto_id INTEGER PRIMARY KEY AUTOINCREMENT,
 proyecto_nombre TEXT NOT NULL CHECK(length(trim(proyecto_nombre)) > 0),
 fecha_inicio TEXT NOT NULL,
 fecha_fin TEXT NOT NULL CHECK(fecha_fin >= fecha_inicio),
 horas_requeridas REAL NOT NULL CHECK(horas_requeridas > 0),
 owner_id INTEGER NOT NULL REFERENCES recurso(recurso_id) ON DELETE RESTRICT,
 proyect_status TEXT NOT NULL CHECK(proyect_status IN ('pendiente','en curso','pausado','finalizado')),
 porcentaje_avance REAL NOT NULL DEFAULT 0 CHECK(porcentaje_avance BETWEEN 0 AND 100)
);
CREATE TABLE IF NOT EXISTS consumo (
 consumo_id INTEGER PRIMARY KEY AUTOINCREMENT,
 proyecto_id INTEGER NOT NULL REFERENCES proyecto(proyecto_id) ON DELETE RESTRICT,
 recurso_id INTEGER NOT NULL REFERENCES recurso(recurso_id) ON DELETE RESTRICT,
 fecha_inicio TEXT NOT NULL,
 fecha_fin TEXT NOT NULL CHECK(fecha_fin >= fecha_inicio),
 horas_consumidas REAL NOT NULL CHECK(horas_consumidas > 0),
 tarea TEXT NOT NULL CHECK(length(trim(tarea)) > 0),
 rol_id INTEGER NOT NULL REFERENCES rol(rol_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS consumo_proyecto ON consumo(proyecto_id);
CREATE INDEX IF NOT EXISTS consumo_recurso ON consumo(recurso_id);
CREATE INDEX IF NOT EXISTS consumo_rol ON consumo(rol_id);
