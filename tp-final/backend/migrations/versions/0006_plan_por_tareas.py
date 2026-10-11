"""Task estimates define project hours and dates; preserve existing plans on migration."""
from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tarea', sa.Column('horas_requeridas', sa.Double(), nullable=True))
    # Preserve the previous estimate, proportionally to inclusive task duration.
    op.execute("""
        WITH weights AS (
            SELECT tarea_id, proyecto_id, (fecha_fin-fecha_inicio+1)::double precision AS days,
                SUM(fecha_fin-fecha_inicio+1) OVER (PARTITION BY proyecto_id) AS total
            FROM tarea
        )
        UPDATE tarea t SET horas_requeridas=p.horas_requeridas*w.days/w.total
        FROM weights w, proyecto p WHERE t.tarea_id=w.tarea_id AND p.proyecto_id=w.proyecto_id
    """)
    op.execute("""
        INSERT INTO tarea (proyecto_id,tarea_nombre,fecha_inicio,fecha_fin,horas_requeridas,porcentaje_avance,recurso_id)
        SELECT p.proyecto_id,'Planificación inicial (migrada)',p.fecha_inicio,p.fecha_fin,
            p.horas_requeridas,p.porcentaje_avance,p.owner_id
        FROM proyecto p WHERE NOT EXISTS (SELECT 1 FROM tarea t WHERE t.proyecto_id=p.proyecto_id)
    """)
    op.alter_column('tarea', 'horas_requeridas', nullable=False)
    op.create_check_constraint('tarea_horas_positivas', 'tarea', 'horas_requeridas > 0')
    op.alter_column('proyecto', 'fecha_inicio', nullable=True)
    op.alter_column('proyecto', 'fecha_fin', nullable=True)
    op.alter_column('proyecto', 'horas_requeridas', server_default='0')
    op.drop_constraint('proyecto_horas_positivas', 'proyecto', type_='check')
    op.create_check_constraint('proyecto_horas_positivas', 'proyecto', 'horas_requeridas >= 0')
    op.create_check_constraint('proyecto_fechas_coherentes', 'proyecto',
        '(fecha_inicio IS NULL AND fecha_fin IS NULL) OR (fecha_inicio IS NOT NULL AND fecha_fin IS NOT NULL)')
    op.execute("""
        UPDATE proyecto p SET horas_requeridas=tot.hours, fecha_inicio=tot.start, fecha_fin=tot.finish
        FROM (SELECT proyecto_id,SUM(horas_requeridas) hours,MIN(fecha_inicio) start,MAX(fecha_fin) finish
              FROM tarea GROUP BY proyecto_id) tot WHERE tot.proyecto_id=p.proyecto_id
    """)
    # This applies to ordinary API writes, bulk imports and direct SQL imports alike.
    op.execute("""
        CREATE FUNCTION lock_task_project() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP='UPDATE' THEN
                PERFORM 1 FROM proyecto WHERE proyecto_id IN (OLD.proyecto_id,NEW.proyecto_id)
                    ORDER BY proyecto_id FOR UPDATE;
            ELSIF TG_OP='DELETE' THEN
                PERFORM 1 FROM proyecto WHERE proyecto_id=OLD.proyecto_id FOR UPDATE;
            ELSE
                PERFORM 1 FROM proyecto WHERE proyecto_id=NEW.proyecto_id FOR UPDATE;
            END IF;
            IF TG_OP='DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER task_project_lock BEFORE INSERT OR UPDATE OR DELETE ON tarea
            FOR EACH ROW EXECUTE FUNCTION lock_task_project();
        CREATE FUNCTION refresh_task_project() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE ids integer[];
        BEGIN
            IF TG_OP='DELETE' THEN ids := ARRAY[OLD.proyecto_id];
            ELSIF TG_OP='INSERT' THEN ids := ARRAY[NEW.proyecto_id];
            ELSE ids := ARRAY[OLD.proyecto_id,NEW.proyecto_id]; END IF;
            UPDATE proyecto p SET
                horas_requeridas=(SELECT COALESCE(SUM(t.horas_requeridas),0) FROM tarea t WHERE t.proyecto_id=p.proyecto_id),
                fecha_inicio=(SELECT MIN(t.fecha_inicio) FROM tarea t WHERE t.proyecto_id=p.proyecto_id),
                fecha_fin=(SELECT MAX(t.fecha_fin) FROM tarea t WHERE t.proyecto_id=p.proyecto_id)
            WHERE p.proyecto_id=ANY(ids);
            RETURN NULL;
        END $$;
        CREATE TRIGGER task_project_totals AFTER INSERT OR UPDATE OR DELETE ON tarea
            FOR EACH ROW EXECUTE FUNCTION refresh_task_project();
    """)


def downgrade():
    # The old schema cannot represent a project without a plan. Refuse rather than invent dates/hours.
    op.execute("""DO $$ BEGIN
        IF EXISTS(SELECT 1 FROM proyecto WHERE fecha_inicio IS NULL OR horas_requeridas <= 0) THEN
            RAISE EXCEPTION 'No se puede volver al esquema anterior con proyectos sin planificación';
        END IF; END $$""")
    op.execute('DROP TRIGGER task_project_totals ON tarea; DROP FUNCTION refresh_task_project(); '
               'DROP TRIGGER task_project_lock ON tarea; DROP FUNCTION lock_task_project();')
    op.drop_constraint('proyecto_fechas_coherentes', 'proyecto', type_='check')
    op.drop_constraint('proyecto_horas_positivas', 'proyecto', type_='check')
    op.create_check_constraint('proyecto_horas_positivas', 'proyecto', 'horas_requeridas > 0')
    op.alter_column('proyecto', 'fecha_inicio', nullable=False)
    op.alter_column('proyecto', 'fecha_fin', nullable=False)
    op.alter_column('proyecto', 'horas_requeridas', server_default=None)
    op.drop_constraint('tarea_horas_positivas', 'tarea', type_='check')
    op.drop_column('tarea', 'horas_requeridas')
