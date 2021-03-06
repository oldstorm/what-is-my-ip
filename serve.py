import json
from string import capwords
import sys

from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import urllib.request


class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    def __tabulate_results(self, json_obj):
        col_width = len(max(json_obj, key=len))
        table = ''

        for k, v in json_obj.items():
            table += '{:{width}} : {}\n'.format(
                capwords(' '.join(k.split('_'))),
                v,
                width=col_width
            )

        return table

    def __query_freegeoip(self, ip_address):
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_OPTIONAL

        data = urllib.request.urlopen(
            'http://freegeoip.net/json/{}'.format(ip_address),
            context=ssl_ctx,
        ).read().decode()

        return data

    def do_GET(self):

        # Get the client IP. This is why this program exists.
        client_ip = self.client_address[0]

        # Casual check for proxied requests
        if client_ip == '127.0.0.1' and 'X-Real-IP' in self.headers:
            client_ip = self.headers['X-Real-IP']

        data = None
        response_code = 200

        # Use freegeoip.net to query for more details if requested
        if '?full' in self.path or '?f' in self.path:
            try:
                data = self.__tabulate_results(
                    json.loads(
                        self.__query_freegeoip(client_ip)
                    )
                )
            except Exception as e:
                response_code = 500
                data = str(e)
        else:
            data = client_ip

        # Prepare and deliver response
        self.send_response(response_code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(bytes(data + '\n', 'utf8'))

        return


def run(port):
    try:
        server = HTTPServer(('', port), MyHTTPRequestHandler)
        print('Started service on 0.0.0.0:{}'.format(port))
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()


if __name__ == '__main__':
    try:
        run(int(sys.argv[1]) if len(sys.argv) == 2 else 9000)
    except ValueError:
        print('Ports must be integers', file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print('Are you using that port? ({})'.format(str(e)), file=sys.stderr)
        sys.exit(2)
