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
        if self.path == '/':
            message = {"message": "Please specify the plugin to use."}
            self.wfile.write(json.dumps(message, indent=2).encode('utf8'))
        elif self.path == '/plugin.json':
            self.handle_plugin_request('source.py', 'plugin.json')
        elif self.path == '/plugin_multi.json':
            self.handle_plugin_request('source.py', 'plugin_multi.json')
        else:
            self.send_response(404)
            self.end_headers()

    def handle_plugin_request(self, source_file, plugin_file):
        try:
            with open(plugin_file, 'r', encoding='utf-8') as f:
                plugin = json.load(f)
                with open(source_file, 'r', encoding='utf-8') as f:
                    plugin['api']['python']['source'] = f.read()
                if 'usage_hint' in plugin['api']['python']:
                    with open('plugin_hint.txt', 'r') as f:
                        plugin['api']['python']['usage_hint'] = f.read()
            self.wfile.write(json.dumps(plugin, indent=2).encode('utf8'))
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()


with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print("serving at port", PORT)
    httpd.allow_reuse_address = True
    httpd.allow_reuse_port = True
    httpd.serve_forever()
