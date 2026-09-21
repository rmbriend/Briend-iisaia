import test from 'node:test';
import assert from 'node:assert/strict';
import { escapeHTML, field, consumptionTable } from '../frontend/ui.js';
import { request } from '../frontend/api.js';

test('untrusted names and tasks are escaped in text and attributes', () => {
  const attack = '<img src=x onerror="alert(1)">';
  assert.equal(escapeHTML(attack), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
  assert.ok(!field('name', 'Name', attack).includes('<img'));
  const html = consumptionTable([{tarea:attack,recurso_nombre:attack,rol_descripcion:attack,horas_consumidas:1}], {recurso_id:2});
  assert.ok(!html.includes('<img'));
  assert.ok(html.includes('&lt;img'));
});

test('API client uses JSON, cookies, rotated CSRF, handles 204 and errors without retries', async () => {
  const previous = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({url, options});
    if (url.endsWith('/session')) return new Response(JSON.stringify({csrf_token:'first',user:null}));
    if (url.endsWith('/login')) return new Response(JSON.stringify({csrf_token:'second',user:{recurso_id:1}}));
    if (options.method === 'DELETE') return new Response(null,{status:204});
    return new Response(JSON.stringify({error:{message:'Conflicto',code:'conflict'}}),{status:409});
  };
  try {
    await request('/session');
    await request('/login',{method:'POST',data:{password:'test'}});
    assert.equal(calls[1].options.headers['X-CSRF-Token'],'first');
    assert.equal(calls[1].options.credentials,'same-origin');
    assert.equal(calls[1].options.headers['Content-Type'],'application/json');
    assert.equal(JSON.parse(calls[1].options.body).password,'test');
    assert.equal(await request('/consumos/1',{method:'DELETE'}),null);
    assert.equal(calls[2].options.headers['X-CSRF-Token'],'second');
    await assert.rejects(request('/roles',{method:'POST',data:{}}), error => error.status === 409 && error.code === 'conflict');
    assert.equal(calls.length,4);
    globalThis.fetch = async () => {throw new TypeError('offline');};
    await assert.rejects(request('/session'), error => error.code === 'network_error');
  } finally {
    globalThis.fetch = previous;
  }
});
