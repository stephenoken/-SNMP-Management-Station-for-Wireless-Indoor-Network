import SocketServer
import socket
import random
class HeaterHandler(SocketServer.BaseRequestHandler):
    # Collection of temperatures
    heater = ["OFF"]
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print "{} wrote :".format(self.client_address[0])
        if self.data.upper() == "GET_DATA":
            self.request.send(self.heater[0])
        else:
            self.heater[0] = self.data
            self.request.send(self.heater[0])

if __name__ == "__main__":
    HOST, PORT = "localhost", 8001

    server = SocketServer.TCPServer((HOST,PORT),HeaterHandler)

    server.serve_forever()
