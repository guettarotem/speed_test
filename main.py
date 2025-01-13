from Server import Server
from Client import Client

if __name__ == "__main__":
    choice = input("Start as (s)erver or (c)lient? ").lower()
    if choice == 's':
        udp_port = int(input("Enter UDP port: "))
        tcp_port = int(input("Enter TCP port: "))
        server = Server(udp_port, tcp_port)
        server.start()
    elif choice == 'c':
        client = Client()
        client.start()
