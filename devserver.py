import json
import http.server
import socketserver

PORT = 5003

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_headers(self):
        self.send_response(200)
        self.send_header('content-type', 'application/json')
        self.send_header('access-control-allow-origin', '*')
        self.send_header('access-Control-Allow-Private-Network', 'true')
        self.send_header('access-control-allow-methods', 'GET, OPTIONS')
        self.end_headers()
    def do_OPTIONS(self):
        return self.do_headers()
    def do_GET(self):
        self.do_headers()
        with open('plugin.json', 'r') as f:
            plugin = json.load(f)
            with open('source.py', 'r') as f:
                plugin['api']['python']['source'] = f.read()
            if 'usage_hint' in plugin['api']['python']:
                with open('plugin_hint.txt', 'r') as f:
                    plugin['api']['python']['usage_hint'] = f.read()

        self.wfile.write(json.dumps(plugin, indent=2).encode('utf8'))

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print("serving at port", PORT)
    httpd.allow_reuse_address = True
    httpd.allow_reuse_port = True
    httpd.serve_forever()
