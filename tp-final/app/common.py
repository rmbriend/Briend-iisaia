import math
import sqlite3
from datetime import date

from flask import abort, flash, g, request

from .db import get_db


def admin_required():
    if not g.user['es_admin']:
        abort(403, 'Esta acción requiere permisos de administrador.')


def record(table, key, identifier):
    # Identifiers are internal constants, never request values.
    row = get_db().execute(f'SELECT * FROM {table} WHERE {key}=?', (identifier,)).fetchone()
    if row is None:
        abort(404, 'No se encontró el registro.')
    return row


def required(name):
    value = request.form.get(name, '').strip()
    if not value:
        raise ValueError('Completá todos los campos obligatorios.')
    return value


def number(name, minimum=0, maximum=None, strict=True):
    try:
        value = float(required(name))
    except ValueError:
        raise ValueError('Ingresá valores numéricos válidos.') from None
    if not math.isfinite(value) or (value <= minimum if strict else value < minimum) or (maximum is not None and value > maximum):
        raise ValueError('Las horas deben ser positivas y el avance debe estar entre 0 y 100.')
    return value


def dates():
    try:
        start = date.fromisoformat(required('fecha_inicio'))
        end = date.fromisoformat(required('fecha_fin'))
    except ValueError:
        raise ValueError('Ingresá fechas válidas.') from None
    if end < start:
        raise ValueError('La fecha de fin no puede ser anterior al inicio.')
    return start.isoformat(), end.isoformat()


def reference(name, table, key):
    try:
        value = int(required(name))
    except ValueError:
        raise ValueError('Seleccioná una referencia válida.') from None
    if get_db().execute(f'SELECT 1 FROM {table} WHERE {key}=?', (value,)).fetchone() is None:
        raise ValueError('El recurso, proyecto o rol seleccionado no existe.')
    return value


def save(sql, values):
    db = get_db()
    try:
        db.execute(sql, values)
        db.commit()
        return True
    except sqlite3.IntegrityError:
        db.rollback()
        flash('No se pudo guardar: el nombre ya existe o hay referencias inválidas.', 'danger')
        return False


def delete(table, key, identifier):
    db = get_db()
    try:
        db.execute(f'DELETE FROM {table} WHERE {key}=?', (identifier,))
        db.commit()
        flash('Registro eliminado.', 'success')
    except sqlite3.IntegrityError:
        db.rollback()
        flash('No se puede eliminar: tiene proyectos o consumos asociados.', 'danger')
