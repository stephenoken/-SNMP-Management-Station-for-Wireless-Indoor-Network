import SocketServer
import socket
import random
import get_ip_address

class ThermometerHandler(SocketServer.BaseRequestHandler):
    # Collection of temperatures
    #temperatures = ["11","18","20","5","70"]
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print "{} wrote :".format(self.client_address[0])
        if self.data.upper() == "GET_DATA":
            temperature = str(random.randrange(0,22))
            #self.request.sendall(temperature,self.Heater)
            self.request.send(temperature)
        else:
            self.temperatures[0] = self.data
            self.request.send(self.temperatures[0])


if __name__ == "__main__":
    HOST, PORT = get_ip_address.get_lan_ip(), 8000

    server = SocketServer.TCPServer((HOST,PORT),ThermometerHandler)
    print("Server running http://{0}:{1}".format(HOST,PORT))
    server.serve_forever()
