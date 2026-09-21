import http.client
import json
import threading
from contextlib import contextmanager
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer

from werkzeug.serving import make_server
from frontend.server import FrontendHandler


@contextmanager
def running(server):
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_static_frontend_and_real_proxy_cookie_roundtrip(app):
    backend = make_server('127.0.0.1', 0, app)
    class Handler(FrontendHandler):
        api_port = backend.server_port
        def log_message(self, *args):
            pass
    with running(backend), running(ThreadingHTTPServer(('127.0.0.1', 0), Handler)) as port:
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
        cookies = SimpleCookie()
        def send(method, path, data=None, token=None):
            headers = {'Cookie': '; '.join(f'{key}={value.value}' for key,value in cookies.items())}
            if data is not None:
                headers['Content-Type'] = 'application/json'
            if token:
                headers['X-CSRF-Token'] = token
            connection.request(method,path,json.dumps(data) if data is not None else None,headers)
            response = connection.getresponse()
            for name,value in response.getheaders():
                if name.lower() == 'set-cookie':
                    cookies.load(value)
            payload = response.read()
            return response.status, response.getheader('Content-Type'), payload
        status,mime,html=send('GET','/proyectos/1/editar')
        assert status==200 and 'text/html' in mime and b'type="module"' in html
        assert b'{{' not in html  # Static file, no template expansion.
        assert send('GET','/server.py')[0]==404
        assert send('GET','/../instance/proyectos.sqlite')[0]==404
        assert 'javascript' in send('GET','/app.js')[1]
        status,_,body=send('GET','/api/proyectos')
        assert status==401 and json.loads(body)['error']['code']=='unauthorized'
        _,_,body=send('GET','/api/session')
        token=json.loads(body)['csrf_token']
        status,_,body=send('POST','/api/login',{'recurso_nombre':'admin','password':'Proyecto1'},token)
        assert status==200
        token=json.loads(body)['csrf_token']
        assert send('GET','/api/proyectos')[0]==200
        status,_,body=send('POST','/api/roles',{'rol_descripcion':'Prueba proxy'},token)
        assert status==201
        identifier=json.loads(body)['rol_id']
        assert send('DELETE',f'/api/roles/{identifier}',{},token)[0]==204
        assert send('POST','/api/logout',{},token)[0]==200
        assert send('GET','/api/proyectos')[0]==401
        connection.close()


def test_frontend_reports_backend_unavailable():
    class Handler(FrontendHandler):
        api_port = 0
        def log_message(self,*args):
            pass
    with running(ThreadingHTTPServer(('127.0.0.1',0),Handler)) as port:
        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
        connection.request('GET','/api/session')
        response=connection.getresponse()
        assert response.status==502
        assert json.loads(response.read())['error']['code']=='proxy_error'
        connection.close()
