import time
import http.server
import os


HOST_NAME = '0.0.0.0' # Host name of the http server
# Gets the port number from $PORT0 environment variable
PORT_NUMBER = int(os.environ['PORT0'])


class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write("<html><head><title>Time Server</title></head>".encode())
        s.wfile.write("<body><p>The current time is {}</p>".format(time.asctime()).encode())
        s.wfile.write("</body></html>".encode())

if __name__ == '__main__':
    server_class = http.server.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print(time.asctime(), "Server Starts - {}:{}".format(HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - {}:{}".format(HOST_NAME, PORT_NUMBER))
