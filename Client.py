import socket
import struct
import threading
import time


MAGIC_COOKIE = 0xabcddcba
MSG_TYPE_OFFER = 0x2
MSG_TYPE_REQUEST = 0x3
MSG_TYPE_PAYLOAD = 0x4


class Client:
    def __init__(self):
        self.running = True

    def start(self):
        while self.running:
            print("Client started, listening for offer requests...")
            self.listen_for_offers()

    def listen_for_offers(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_socket.bind(('', 13117))
        while self.running:
            data, server_address = udp_socket.recvfrom(1024)
            magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IBHH', data[:9])
            if magic_cookie == MAGIC_COOKIE and msg_type == MSG_TYPE_OFFER:
                print(f"Received offer from {server_address[0]}:{udp_port}")
                self.handle_offer(server_address[0], udp_port, tcp_port)

    def handle_offer(self, server_ip, udp_port, tcp_port):
        file_size = int(input("Enter file size in bytes: "))
        tcp_conn = threading.Thread(target=self.tcp_transfer, args=(server_ip, tcp_port, file_size))
        tcp_conn.start()
        udp_conn = threading.Thread(target=self.udp_transfer, args=(server_ip, udp_port, file_size))
        udp_conn.start()
        tcp_conn.join()
        udp_conn.join()

    def tcp_transfer(self, server_ip, tcp_port, file_size):
        start_time = time.time()
        with socket.create_connection((server_ip, tcp_port)) as s:
            s.sendall(f"{file_size}\n".encode())
            data = s.recv(file_size)
        end_time = time.time()
        print(f"TCP transfer finished, total time: {end_time - start_time:.2f} seconds")

    def udp_transfer(self, server_ip, udp_port, file_size):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        request_packet = struct.pack('!IBQ', MAGIC_COOKIE, MSG_TYPE_REQUEST, file_size)
        udp_socket.sendto(request_packet, (server_ip, udp_port))

        start_time = time.time()
        udp_socket.settimeout(1)
        received_segments = 0

        while True:
            try:
                data, _ = udp_socket.recvfrom(1024)
                received_segments += 1
            except socket.timeout:
                break

        end_time = time.time()
        print(f"UDP transfer finished, total time: {end_time - start_time:.2f} seconds, segments received: {received_segments}")
