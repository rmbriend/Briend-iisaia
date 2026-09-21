// Escape every interpolated API value before placing it in HTML.
export const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
})[char]);
export const fmt = value => new Intl.NumberFormat('es-AR', { maximumFractionDigits: 2 }).format(value);
const e = escapeHTML;

export function link(href, label, css = '') {
  return `<a data-link href="${e(href)}" class="${e(css)}">${e(label)}</a>`;
}
export function field(name, label, value = '', type = 'text', options = '') {
  return `<div class="field"><label for="${e(name)}">${e(label)}</label>
    <input class="form-control" id="${e(name)}" name="${e(name)}" type="${e(type)}"
      value="${e(value)}" ${options}></div>`;
}
export function select(name, label, rows, key, labelKey, value = '', blank = 'Seleccionar…', required = true) {
  return `<div class="field"><label for="${e(name)}">${e(label)}</label>
    <select class="form-select" id="${e(name)}" name="${e(name)}" ${required ? 'required' : ''}>
      <option value="">${e(blank)}</option>${rows.map(row => `<option value="${e(row[key])}"
        ${String(row[key]) === String(value) ? 'selected' : ''}>${e(row[labelKey])}</option>`).join('')}
    </select></div>`;
}
export function progress(value) {
  const safe = Math.max(0, Math.min(100, Number(value) || 0));
  return `<div class="progress-label"><span>Avance real</span><strong>${fmt(safe)} %</strong></div>
    <div class="progress" role="progressbar" aria-label="Avance real" aria-valuenow="${safe}" aria-valuemin="0" aria-valuemax="100">
      <div class="progress-bar" style="width:${safe}%"></div></div>`;
}
export function heading(title, subtitle = '', action = '', eyebrow = '') {
  return `<div class="page-heading"><div><p class="eyebrow">${e(eyebrow)}</p><h1>${e(title)}</h1>
    <p class="muted">${e(subtitle)}</p></div>${action}</div>`;
}
export function removeButton(path, returnTo) {
  return `<button type="button" class="btn btn-sm btn-outline-danger" data-delete="${e(path)}"
    data-return="${e(returnTo)}">Eliminar</button>`;
}
export function formShell(kind, id, title, body, back, disabled = false) {
  return `<div class="form-heading">${link(back, '← Volver')}<h1>${e(title)}</h1></div>
    <form class="panel editor" data-form="${kind}" data-id="${id ?? ''}">${body}
    <div class="actions"><button class="btn btn-primary" ${disabled ? 'disabled' : ''}>Guardar</button>
    ${link(back, 'Cancelar', 'btn btn-outline-secondary')}</div></form>`;
}
export function stats(items) {
  return `<div class="stats">${items.map(([label, value]) => `<div class="stat"><span>${e(label)}</span>
    <strong>${e(value)}</strong></div>`).join('')}</div>`;
}
export function consumptionTable(rows, user, showProject = false, returnTo = '/consumos') {
  return `<div class="table-responsive"><table class="table"><thead><tr>${showProject ? '<th>Proyecto</th>' : ''}
    <th>Tarea / recurso</th><th>Rol</th><th>Período</th><th class="text-end">Horas</th><th>Acciones</th></tr></thead><tbody>
    ${rows.map(row => `<tr>${showProject ? `<td>${link('/proyectos/' + row.proyecto_id, row.proyecto_nombre)}</td>` : ''}
      <td><strong>${e(row.tarea)}</strong><small class="d-block muted">${e(row.recurso_nombre)}</small></td>
      <td>${e(row.rol_descripcion)}</td><td class="date-cell">${e(row.fecha_inicio)}<br>${e(row.fecha_fin)}</td>
      <td class="text-end">${fmt(row.horas_consumidas)}</td><td>${user.es_admin || user.recurso_id === row.recurso_id
        ? `<div class="actions">${link('/consumos/' + row.consumo_id + '/editar', 'Editar', 'btn btn-sm btn-outline-secondary')}
            ${removeButton('/consumos/' + row.consumo_id, returnTo)}</div>` : '<span class="muted">Solo lectura</span>'}</td></tr>`).join('')
      || `<tr><td colspan="${showProject ? 6 : 5}" class="empty">Todavía no hay consumos registrados.</td></tr>`}
    </tbody></table></div>`;
}
