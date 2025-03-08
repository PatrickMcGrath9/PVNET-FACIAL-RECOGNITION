import http.server

PORT = 9994

class facialRecHandler(http.server.ThreadingHTTPServer):
    def do_POST():
        pass

    def do_GET():
        pass


if __name__ == '__main__':
    server = http.server.ThreadingHTTPServer(('', PORT), facialRecHandler)
    print("Listening on port:", PORT)
    server.serve_forever()