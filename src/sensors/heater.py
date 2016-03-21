import SocketServer
import socket
import random
import get_ip_address
class HeaterHandler(SocketServer.BaseRequestHandler):
    # Collection of temperatures
    heater = ["OFF"]
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print "{0} wrote :{1}".format(self.client_address[0],self.data)
        if self.data.upper() == "GET_DATA":
            self.request.send(self.heater[0])
        else:
            self.heater[0] = self.data
            self.request.send(self.heater[0])

if __name__ == "__main__":
    HOST, PORT = get_ip_address.get_lan_ip(), 8000

    server = SocketServer.TCPServer((HOST,PORT),HeaterHandler)
    print("Server running http://{0}:{1}".format(HOST,PORT))
    server.serve_forever()
