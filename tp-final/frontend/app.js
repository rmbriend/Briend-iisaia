import { request, APIError } from './api.js';
import { escapeHTML as e, fmt, link, field, select, progress, heading, removeButton,
  formShell, stats, consumptionTable } from './ui.js';

const view = document.querySelector('#view');
const notice = document.querySelector('#notice');
let user = null;
let renderVersion = 0;

function message(text, category = 'danger') {
  notice.textContent = text;
  notice.className = `alert alert-${category}`;
  notice.hidden = !text;
}
function navigation() {
  document.querySelector('#navigation').innerHTML = `
    <a data-link class="brand" href="/proyectos"><span class="brand-icon">P</span> Pulso <small>PROYECTOS</small></a>
    ${user ? `<nav aria-label="Navegación principal">${link('/proyectos', 'Proyectos')}${link('/consumos', 'Consumos')}
      ${user.es_admin ? link('/recursos', 'Recursos') + link('/roles', 'Roles') : ''}</nav>
      <div class="account">${link('/password', user.recurso_nombre)}
        <button class="btn btn-sm btn-outline-secondary" data-action="logout">Salir</button></div>` : ''}`;
}
function go(path, replace = false) {
  if (replace) history.replaceState(null, '', path);
  else history.pushState(null, '', path);
  return render();
}

function loginView() {
  return `<section class="login-layout"><div class="login-copy"><p class="eyebrow">CADA HORA CUENTA</p>
    <h1>Una mirada clara<br>a tus proyectos.</h1><p class="lead">Registrá la dedicación de tu equipo y seguí el avance del trabajo en un mismo lugar.</p>
    <div class="login-art"><div><span>PLANIFICAR</span><b>01</b></div><div><span>REGISTRAR</span><b>02</b></div><div><span>AVANZAR</span><b>03</b></div></div></div>
    <div class="panel login-panel"><p class="eyebrow">BIENVENIDO A PULSO</p><h2>Iniciar sesión</h2><p class="muted">Ingresá con tu usuario registrado.</p>
    <form data-form="login">${field('recurso_nombre', 'Usuario', '', 'text', 'required autocomplete="username"')}
      ${field('password', 'Contraseña', '', 'password', 'required autocomplete="current-password"')}
      <button class="btn btn-primary w-100">Ingresar</button></form></div></section>`;
}
function passwordView() {
  return heading('Cambiar contraseña', '', '', 'MI CUENTA') + `<form class="panel editor" data-form="password">
    ${user.debe_cambiar_password ? '<div class="alert alert-info">Para continuar, reemplazá tu contraseña inicial por una propia.</div>' : ''}
    ${field('actual', 'Contraseña actual', '', 'password', 'required autocomplete="current-password"')}
    ${field('password', 'Nueva contraseña', '', 'password', 'required minlength="8" autocomplete="new-password"')}
    ${field('confirmacion', 'Confirmar nueva contraseña', '', 'password', 'required minlength="8" autocomplete="new-password"')}
    <p class="muted">Usá al menos 8 caracteres.</p><button class="btn btn-primary">Guardar contraseña</button></form>`;
}
async function projectsView() {
  const params = new URLSearchParams(location.search);
  const [projects, catalogs] = await Promise.all([request('/proyectos?' + params), request('/catalogos')]);
  const estimated = projects.reduce((sum, p) => sum + p.horas_requeridas, 0);
  const used = projects.reduce((sum, p) => sum + p.horas_consumidas, 0);
  return heading('Proyectos', 'El avance de tu equipo, en perspectiva.', user.es_admin
    ? link('/proyectos/nuevo', '+ Nuevo proyecto', 'btn btn-primary') : '', 'VISTA GENERAL')
    + stats([['Proyectos en vista', projects.length], ['Horas requeridas', fmt(estimated) + ' h'],
      ['Horas consumidas', fmt(used) + ' h'], ['Saldo de horas', fmt(estimated - used) + ' h']])
    + `<form class="filters panel" data-form="filters">
      ${select('estado', 'Estado', catalogs.estados.map(value => ({value})), 'value', 'value', params.get('estado'), 'Todos los estados', false)}
      ${select('responsable', 'Responsable', catalogs.recursos, 'recurso_id', 'recurso_nombre', params.get('responsable'), 'Todos los responsables', false)}
      <button class="btn btn-dark">Filtrar</button>${link('/proyectos', 'Limpiar')}</form>
      <div class="project-grid">${projects.map(p => `<article class="panel project-card">
        <div class="card-top"><span class="status status-${e(p.proyect_status.replaceAll(' ', '-'))}">${e(p.proyect_status)}</span><span class="muted">#${p.proyecto_id}</span></div>
        <h2>${link('/proyectos/' + p.proyecto_id, p.proyecto_nombre)}</h2><p class="muted">Responsable · ${e(p.responsable)}</p>
        ${progress(p.porcentaje_avance)}<div class="hours"><span><strong>${fmt(p.horas_consumidas)}</strong> / ${fmt(p.horas_requeridas)} h consumidas</span>
          <span>${fmt(p.porcentaje_consumo)} %</span></div><p class="${p.exceso > 0 ? 'overrun' : 'muted'}">Saldo: ${fmt(p.saldo)} h · Exceso: ${fmt(p.exceso)} h</p>
        <div class="card-bottom"><small>${e(p.fecha_inicio)} → ${e(p.fecha_fin)}</small>${link('/proyectos/' + p.proyecto_id, 'Ver proyecto →')}</div></article>`).join('')
        || '<div class="panel empty"><h2>No hay proyectos para mostrar</h2><p>Creá un proyecto o ajustá los filtros para comenzar.</p></div>'}</div>`;
}
async function projectDetail(id) {
  const data = await request('/proyectos/' + id);
  const p = data.proyecto;
  const editable = user.es_admin || user.recurso_id === p.owner_id;
  return link('/proyectos', '← Proyectos') + heading(p.proyecto_nombre,
    `${p.responsable} · ${p.fecha_inicio} → ${p.fecha_fin} · ${p.proyect_status}`,
    `<div class="actions">${editable ? link('/proyectos/' + id + '/editar', 'Editar proyecto', 'btn btn-outline-secondary') : ''}
      ${user.es_admin ? removeButton('/proyectos/' + id, '/proyectos') : ''}</div>`, 'DETALLE DEL PROYECTO')
    + stats([['Horas requeridas', fmt(p.horas_requeridas)], ['Horas consumidas · ' + fmt(p.porcentaje_consumo) + ' %', fmt(p.horas_consumidas)],
      ['Saldo / exceso de horas', `${fmt(p.saldo)} / ${fmt(p.exceso)}`], ['Avance real (manual)', fmt(p.porcentaje_avance) + ' %']])
    + `<section class="panel"><div class="section-heading"><h2>Consumos de horas</h2>
      ${link('/consumos/nuevo?proyecto_id=' + id, '+ Registrar consumo', 'btn btn-primary')}</div>
      ${consumptionTable(data.consumos, user, false, '/proyectos/' + id)}</section>
      <div class="summary-grid">${[['Horas por recurso', data.por_recurso], ['Horas por rol', data.por_rol]].map(([title, totals]) =>
        `<section class="panel"><h2>${title}</h2>${Object.entries(totals).map(([label, hours]) =>
          `<div class="summary-row"><span>${e(label)}</span><strong>${fmt(hours)} h</strong></div>`).join('')
          || '<p class="muted">Sin horas registradas.</p>'}</section>`).join('')}</div>`;
}
async function projectForm(id) {
  const [catalogs, data] = await Promise.all([request('/catalogos'), id ? request('/proyectos/' + id) : null]);
  const p = data?.proyecto ?? { porcentaje_avance: 0, proyect_status: 'pendiente' };
  if (!user.es_admin && (!id || p.owner_id !== user.recurso_id)) throw new APIError('No podés editar este proyecto.', 403);
  const body = field('proyecto_nombre', 'Nombre del proyecto', p.proyecto_nombre, 'text', 'required')
    + `<div class="form-grid">${field('fecha_inicio', 'Fecha de inicio', p.fecha_inicio, 'date', 'required')}
      ${field('fecha_fin', 'Fecha de fin prevista', p.fecha_fin, 'date', 'required')}
      ${field('horas_requeridas', 'Horas requeridas', p.horas_requeridas, 'number', 'required min="0" step="any"')}
      ${field('porcentaje_avance', 'Avance real (%)', p.porcentaje_avance, 'number', 'required min="0" max="100" step="any"')}</div>`
    + (user.es_admin ? select('owner_id', 'Responsable', catalogs.recursos, 'recurso_id', 'recurso_nombre', p.owner_id) : '')
    + select('proyect_status', 'Estado', catalogs.estados.map(value => ({value})), 'value', 'value', p.proyect_status)
    + '<p class="muted">El avance real es manual e independiente del consumo de horas y del estado.</p>';
  return formShell('project', id, id ? 'Editar proyecto' : 'Nuevo proyecto', body, '/proyectos');
}
async function consumptionForm(id) {
  const [catalogs, projects, c] = await Promise.all([request('/catalogos'), request('/proyectos'), id ? request('/consumos/' + id) : {}]);
  if (!user.es_admin && id && c.recurso_id !== user.recurso_id) throw new APIError('Solo podés modificar tus propios consumos.', 403);
  const unavailable = !projects.length || !catalogs.roles.length;
  const body = (unavailable ? '<div class="alert alert-warning">Se necesita al menos un proyecto y un rol para registrar horas. Contactá al administrador.</div>' : '')
    + select('proyecto_id', 'Proyecto', projects, 'proyecto_id', 'proyecto_nombre', c.proyecto_id ?? new URLSearchParams(location.search).get('proyecto_id'))
    + (user.es_admin ? select('recurso_id', 'Recurso', catalogs.recursos, 'recurso_id', 'recurso_nombre', c.recurso_id ?? user.recurso_id)
      : `<p>Recurso: <strong>${e(user.recurso_nombre)}</strong></p>`)
    + select('rol_id', 'Rol desempeñado', catalogs.roles, 'rol_id', 'rol_descripcion', c.rol_id)
    + field('tarea', 'Tarea realizada', c.tarea, 'text', 'required')
    + `<div class="form-grid">${field('fecha_inicio', 'Fecha de inicio', c.fecha_inicio, 'date', 'required')}
      ${field('fecha_fin', 'Fecha de fin', c.fecha_fin, 'date', 'required')}</div>`
    + field('horas_consumidas', 'Horas consumidas', c.horas_consumidas, 'number', 'required min="0" step="any"');
  return formShell('consumption', id, id ? 'Editar consumo' : 'Registrar consumo', body, '/consumos', unavailable);
}
async function consumptionsView() {
  const rows = await request('/consumos');
  return heading('Consumos', 'El registro de horas de todos los proyectos.',
    link('/consumos/nuevo', '+ Registrar consumo', 'btn btn-primary'), 'DEDICACIÓN')
    + `<section class="panel">${consumptionTable(rows, user, true)}</section>`;
}
async function resourcesView() {
  const rows = await request('/recursos');
  return heading('Recursos', 'Personas con acceso al sistema.', link('/recursos/nuevo', '+ Nuevo recurso', 'btn btn-primary'), 'EQUIPO')
    + `<section class="panel table-responsive"><table class="table"><thead><tr><th>Usuario</th><th>Acceso</th><th>Contraseña</th><th>Acciones</th></tr></thead><tbody>
      ${rows.map(r => `<tr><td>${e(r.recurso_nombre)}</td><td>${r.es_admin ? 'Administrador' : 'Usuario'}</td><td>${r.debe_cambiar_password ? 'Cambio pendiente' : 'Configurada'}</td>
        <td><div class="actions">${link('/recursos/' + r.recurso_id + '/editar', 'Editar', 'btn btn-sm btn-outline-secondary')}
          ${removeButton('/recursos/' + r.recurso_id, '/recursos')}</div></td></tr>`).join('')}</tbody></table></section>`;
}
async function resourceForm(id) {
  if (!user.es_admin) throw new APIError('Esta acción requiere permisos de administrador.', 403);
  const r = id ? await request('/recursos/' + id) : {};
  return formShell('resource', id, id ? 'Editar recurso' : 'Nuevo recurso',
    field('recurso_nombre', 'Nombre de usuario', r.recurso_nombre, 'text', 'required autocomplete="off"')
    + field('password', id ? 'Restablecer contraseña (opcional)' : 'Contraseña inicial', '', 'password', `${id ? '' : 'required'} minlength="8" autocomplete="new-password"`)
    + `<p class="muted">Mínimo 8 caracteres. El usuario deberá cambiarla en su próximo acceso.</p>
      <label class="checkbox"><input type="checkbox" name="es_admin" ${r.es_admin ? 'checked' : ''}> Acceso de administrador</label>`, '/recursos');
}
async function rolesView() {
  const rows = await request('/roles');
  return heading('Roles', 'Funciones desempeñadas al registrar horas.', link('/roles/nuevo', '+ Nuevo rol', 'btn btn-primary'), 'ORGANIZACIÓN')
    + `<section class="panel table-responsive"><table class="table"><thead><tr><th>Descripción</th><th>Acciones</th></tr></thead><tbody>
      ${rows.map(r => `<tr><td>${e(r.rol_descripcion)}</td><td><div class="actions">${link('/roles/' + r.rol_id + '/editar', 'Editar', 'btn btn-sm btn-outline-secondary')}
        ${removeButton('/roles/' + r.rol_id, '/roles')}</div></td></tr>`).join('')
        || '<tr><td colspan="2" class="empty">Agregá un rol para comenzar a registrar consumos.</td></tr>'}</tbody></table></section>`;
}
async function roleForm(id) {
  if (!user.es_admin) throw new APIError('Esta acción requiere permisos de administrador.', 403);
  const r = id ? await request('/roles/' + id) : {};
  return formShell('role', id, id ? 'Editar rol' : 'Nuevo rol', field('rol_descripcion', 'Descripción del rol', r.rol_descripcion, 'text', 'required'), '/roles');
}

async function render() {
  const version = ++renderVersion;
  message('');
  view.innerHTML = '<p role="status">Cargando…</p>';
  try {
    const session = await request('/session');
    if (version !== renderVersion) return;
    user = session.user;
    navigation();
    const path = location.pathname;
    if (!user && path !== '/login') return go('/login', true);
    if (user?.debe_cambiar_password && path !== '/password') return go('/password', true);
    if (user && (path === '/' || path === '/login')) return go('/proyectos', true);
    let html;
    let match;
    if (path === '/login') html = loginView();
    else if (path === '/password') html = passwordView();
    else if (path === '/proyectos') html = await projectsView();
    else if (path === '/proyectos/nuevo') html = await projectForm();
    else if ((match = path.match(/^\/proyectos\/(\d+)\/editar$/))) html = await projectForm(match[1]);
    else if ((match = path.match(/^\/proyectos\/(\d+)$/))) html = await projectDetail(match[1]);
    else if (path === '/consumos') html = await consumptionsView();
    else if (path === '/consumos/nuevo') html = await consumptionForm();
    else if ((match = path.match(/^\/consumos\/(\d+)\/editar$/))) html = await consumptionForm(match[1]);
    else if (path === '/recursos') html = await resourcesView();
    else if (path === '/recursos/nuevo') html = await resourceForm();
    else if ((match = path.match(/^\/recursos\/(\d+)\/editar$/))) html = await resourceForm(match[1]);
    else if (path === '/roles') html = await rolesView();
    else if (path === '/roles/nuevo') html = await roleForm();
    else if ((match = path.match(/^\/roles\/(\d+)\/editar$/))) html = await roleForm(match[1]);
    else throw new APIError('No se encontró la página.', 404);
    if (version !== renderVersion) return;
    view.innerHTML = html;
    document.title = `${path === '/login' ? 'Ingresar' : view.querySelector('h1, h2')?.textContent ?? 'Proyectos'} · Pulso`;
    window.scrollTo(0, 0);
  } catch (error) {
    if (version !== renderVersion) return;
    if (error.status === 401) return go('/login', true);
    if (error.code === 'password_change_required') return go('/password', true);
    view.innerHTML = `<section class="panel empty"><h1>No se pudo cargar la página</h1>
      <p>${e(error.message)}</p><button class="btn btn-primary" data-action="retry">Reintentar</button>
      ${link('/proyectos', 'Volver al inicio', 'btn btn-outline-secondary')}</section>`;
  }
}

async function handleError(error, login = false) {
  if ((error.status === 401 && !login) || error.code === 'password_change_required') {
    await go(error.status === 401 ? '/login' : '/password', true);
  } else if (error.code === 'csrf_invalid') {
    await request('/session').catch(() => {}); // Refresh token; never retry a mutation automatically.
  }
  message(error.message);
}

document.addEventListener('click', async event => {
  const anchor = event.target.closest('a[data-link]');
  if (anchor && event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
    event.preventDefault();
    await go(anchor.getAttribute('href'));
    return;
  }
  const button = event.target.closest('button[data-action], button[data-delete]');
  if (!button) return;
  if (button.dataset.action === 'retry') return render();
  if (button.dataset.delete && !confirm('¿Eliminar este registro? Esta acción no se puede deshacer.')) return;
  button.disabled = true;
  try {
    if (button.dataset.action === 'logout') {
      await request('/logout', {method: 'POST'});
      await go('/login');
    } else if (button.dataset.delete) {
      await request(button.dataset.delete, {method: 'DELETE'});
      await go(button.dataset.return);
      message('Registro eliminado.', 'success');
    }
  } catch (error) {
    await handleError(error);
  } finally {
    button.disabled = false;
  }
});

document.addEventListener('submit', async event => {
  const form = event.target.closest('form[data-form]');
  if (!form) return;
  event.preventDefault();
  const kind = form.dataset.form;
  const data = Object.fromEntries(new FormData(form));
  if (kind === 'filters') return go('/proyectos?' + new URLSearchParams(data));
  const button = form.querySelector('button[type="submit"], button:not([type])');
  button.disabled = true;
  message('');
  try {
    if (kind === 'login') {
      await request('/login', {method: 'POST', data});
      await go('/proyectos');
    } else if (kind === 'password') {
      await request('/password', {method: 'PUT', data});
      await go('/proyectos');
      message('Contraseña actualizada.', 'success');
    } else {
      const endpoints = { project: '/proyectos', consumption: '/consumos', resource: '/recursos', role: '/roles' };
      const endpoint = endpoints[kind];
      const id = form.dataset.id;
      if (kind === 'resource') data.es_admin = form.elements.es_admin.checked;
      const result = await request(endpoint + (id ? '/' + id : ''), {method: id ? 'PUT' : 'POST', data});
      const target = kind === 'consumption' ? '/proyectos/' + result.proyecto_id
        : kind === 'project' ? '/proyectos/' + result.proyecto_id : endpoint;
      await go(target);
      message('Cambios guardados.', 'success');
    }
  } catch (error) {
    await handleError(error, kind === 'login');
  } finally {
    button.disabled = false;
  }
});
window.addEventListener('popstate', render);
render();
