"""Local static frontend server with a same-origin /api reverse proxy.

Run separately from Flask: python frontend/server.py
No business logic or database access belongs in this server.
"""
import argparse
import http.client
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
ASSETS = {
    '/styles.css': 'text/css; charset=utf-8',
    '/app.js': 'text/javascript; charset=utf-8',
    '/api.js': 'text/javascript; charset=utf-8',
    '/ui.js': 'text/javascript; charset=utf-8',
}
PAGES = re.compile(r'^/(?:login|password|(?:proyectos|consumos|recursos|roles)(?:/(?:nuevo|[0-9]+(?:/editar)?))?)?/?$')
HOP_HEADERS = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
               'te', 'trailer', 'transfer-encoding', 'upgrade', 'content-length', 'server', 'date'}


class FrontendHandler(BaseHTTPRequestHandler):
    api_host = '127.0.0.1'
    api_port = 5000

    def send_body(self, status, body, content_type):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def error_json(self, status, message):
        body = json.dumps({'error': {'code': 'proxy_error', 'message': message}}).encode()
        self.send_body(status, body, 'application/json')

    def proxy(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.error_json(400, 'Longitud de solicitud inválida.')
        if length < 0 or length > 1024 * 1024:
            return self.error_json(413, 'La solicitud es demasiado grande.')
        if self.headers.get('Transfer-Encoding'):
            return self.error_json(400, 'Enviá solicitudes con Content-Length.')
        body = self.rfile.read(length) if length else None
        # Forward only needed client headers. The upstream destination is fixed.
        headers = {name: self.headers[name] for name in
                   ('Content-Type', 'Accept', 'Cookie', 'X-CSRF-Token') if name in self.headers}
        connection = http.client.HTTPConnection(self.api_host, self.api_port, timeout=15)
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            payload = response.read()
            self.send_response(response.status)
            for name, value in response.getheaders():
                if name.lower() not in HOP_HEADERS:
                    self.send_header(name, value)
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(payload)
        except (OSError, http.client.HTTPException):
            self.error_json(502, 'La API no está disponible. Iniciá el backend Flask.')
        finally:
            connection.close()

    def dispatch(self):
        path = urlsplit(self.path).path
        if path == '/api' or path.startswith('/api/'):
            return self.proxy()
        if self.command not in ('GET', 'HEAD'):
            return self.error_json(405, 'Método no permitido para archivos estáticos.')
        if path in ASSETS:
            return self.send_body(200, (ROOT / path.lstrip('/')).read_bytes(), ASSETS[path])
        if path == '/index.html' or PAGES.fullmatch(path):
            return self.send_body(200, (ROOT / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        self.send_body(404, b'Not found', 'text/plain')

    do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = dispatch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--api-port', type=int, default=5000)
    args = parser.parse_args()
    FrontendHandler.api_port = args.api_port
    server = ThreadingHTTPServer(('127.0.0.1', args.port), FrontendHandler)
    print(f'Frontend: http://127.0.0.1:{args.port} | API: http://127.0.0.1:{args.api_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
