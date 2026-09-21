// The frontend only knows the HTTP contract; it never accesses SQLite.
let csrfToken = '';

export class APIError extends Error {
  constructor(message, status, code) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export async function request(path, { method = 'GET', data, signal } = {}) {
  const headers = { Accept: 'application/json' };
  const options = { method, credentials: 'same-origin', headers, signal };
  if (method !== 'GET') {
    headers['Content-Type'] = 'application/json';
    headers['X-CSRF-Token'] = csrfToken;
    options.body = JSON.stringify(data ?? {});
  }
  let response;
  try {
    response = await fetch(`/api${path}`, options);
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new APIError('No se pudo conectar con el servidor. Intentá nuevamente.', 0, 'network_error');
  }
  if (response.status === 204) return null;
  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new APIError('El servidor devolvió una respuesta inválida.', response.status, 'invalid_response');
  }
  if (!response.ok) {
    throw new APIError(payload.error?.message ?? 'No se pudo completar la solicitud.', response.status, payload.error?.code);
  }
  if (payload?.csrf_token) csrfToken = payload.csrf_token;
  return payload;
}
