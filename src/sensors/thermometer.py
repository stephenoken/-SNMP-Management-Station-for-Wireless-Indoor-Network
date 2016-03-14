import SocketServer
import socket
import random
class ThermometerHandler(SocketServer.BaseRequestHandler):
    # Collection of temperatures
    temperatures = ["11","18","20","5","70"]
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print "{} wrote :".format(self.client_address[0])
        print self.data
        if self.data.upper() == "GET_DATA":
            #self.request.sendall(str(random.randrange(1,100)))
            print self.temperatures[0]
            self.request.send(self.temperatures[0])
        else:
            self.temperatures[0] = self.data
            self.request.send(self.temperatures[0])


if __name__ == "__main__":
    HOST, PORT = "localhost", 8000

    server = SocketServer.TCPServer((HOST,PORT),ThermometerHandler)

    server.serve_forever()
