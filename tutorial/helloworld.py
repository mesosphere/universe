import time
import BaseHTTPServer


HOST_NAME = '0.0.0.0' # Host name of the http server
PORT_NUMBER = 8000 # Port number of the http server

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write("<html><head><title>Time Server</title></head>")
        s.wfile.write("<body><p>The current time is %s</p>" % time.asctime())
        s.wfile.write("</body></html>")

    def do_POST(s):
        do_GET(s)

print "Server booting"

if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
