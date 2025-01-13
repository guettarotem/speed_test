import socket
import struct
import threading
import time


MAGIC_COOKIE = 0xabcddcba
MSG_TYPE_OFFER = 0x2
MSG_TYPE_REQUEST = 0x3
MSG_TYPE_PAYLOAD = 0x4


class Server:
    def __init__(self, udp_port, tcp_port):
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.running = True

    def start(self):
        threading.Thread(target=self.send_offers).start()
        threading.Thread(target=self.listen_tcp).start()

    def send_offers(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        offer_message = struct.pack('!IBHH', MAGIC_COOKIE, MSG_TYPE_OFFER, self.udp_port, self.tcp_port)
        while self.running:
            udp_socket.sendto(offer_message, ('<broadcast>', self.udp_port))
            time.sleep(1)

    def listen_tcp(self):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.bind(('0.0.0.0', self.tcp_port))
        tcp_socket.listen(5)
        print(f"Server started, listening on TCP port {self.tcp_port}")
        while self.running:
            client_socket, address = tcp_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(1024).decode().strip()
            file_size = int(data)
            client_socket.sendall(b'A' * file_size)
        finally:
            client_socket.close()
