import socket
import time
import struct
import threading
import random

from network_config import *

lock_print = threading.Lock()


class Server:

    def __init__(self):
        self.server_udp_port = SERVER_UDP_PORT
        self.server_tcp_port = SERVER_TCP_PORT
        self.is_active = True
        self.broadcasting_port = BROADCAST_PORT
        self.udp_sync_lock = threading.Lock()

    def thread_safe_print(self, message):
        with lock_print:
            print(message)

    def create_offer_packet(self):
        packet = struct.pack("!IBHH", MAGIC_COOKIE, OFFER_TYPE, SERVER_UDP_PORT, SERVER_TCP_PORT)
        return packet

    @property
    def ip_address(self):
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    def handel_requests(self):
        self.thread_safe_print("Waiting for client connections...")
        tcp_thread = threading.Thread(target=self.tcp_requ)
        udp_thread = threading.Thread(target=self.udp_requ)

        try:
            tcp_thread.start()
            udp_thread.start()
        except Exception as e:
            self.thread_safe_print("")

    def tcp_requ(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("", self.server_tcp_port))
            while self.is_active:
                sock.listen()
                client_conn, addr = sock.accept()
                threading.Thread(target=self.handle_tcp, args=(client_conn,addr)).start()

    def udp_requ(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("", self.server_udp_port))
            while self.is_active:
                packet, addr = sock.recvfrom(4096)
                try:
                    cookie, msg_typ, file_size = struct.unpack("!IBQ", packet[:13])
                    if cookie == MAGIC_COOKIE and msg_typ == REQUEST_TYPE:
                        threading.Thread(target=self.handel_udp, args=(sock, addr, file_size)).start()
                except Exception as e:
                    self.thread_safe_print("")

    def handle_tcp(self, conn, addr):
        """Process incoming TCP requests."""
        try:
            # Receive and unpack the request
            data = conn.recv(1024)
            magic, msg_type, file_size, endline_char = struct.unpack('!4sBQI', data[:14])

            # Validate the request
            if magic != MAGIC_COOKIE or msg_type != REQUEST_TYPE or endline_char != ord('\n'):
                raise ValueError("Invalid TCP request format")

            self.thread_safe_print(f"Received TCP request from {addr}, file size: {file_size} bytes")

            # Prepare the payload
            payload = struct.pack('!4sBQQ', MAGIC_COOKIE, PAYLOAD_TYPE, 1, 1) + b'x' * file_size

            # Send the payload to the client
            conn.sendall(payload)

            self.thread_safe_print(f"TCP transfer to {addr} completed successfully")
        except Exception as e:
            self.thread_safe_print(f"Error during TCP request from {addr}: {e}")
        finally:
            conn.close()

    def handel_udp(self,sock,client_addr,file_size):
        try:
            total_chunks = (file_size + 1023) // 1024
            remain_bytes = file_size

            for chunk  in range(total_chunks):
                payload = min(remain_bytes, 1024)
                packet = struct.pack("!IBQQ", MAGIC_COOKIE, PAYLOAD_TYPE, total_chunks, chunk+1) + b"x" * payload
                remain_bytes -= 1024
                with self.udp_sync_lock:
                    sock.sendto(packet, client_addr)
            self.thread_safe_print("")
        except Exception as e:
            self.thread_safe_print("")

    def broadcast_offer(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_sock:
            broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Change this line:
            broadcast_sock.bind(('0.0.0.0', self.broadcasting_port))

            while True:
                packet = self.create_offer_packet()
                # Use specific broadcast address
                broadcast_sock.sendto(packet, ('255.255.255.255', self.broadcasting_port))
                self.thread_safe_print(f"Sent offer to broadcast on port {self.broadcasting_port}")
                time.sleep(1)

    def run(self):
        print(f"Server started, listening on IP address {self.ip_address}")
        broadcast_thread = threading.Thread(target=self.broadcast_offer)
        broadcast_thread.start()

        self.handel_requests()

if __name__ == "__main__":
    server = Server()
    try:
        server.run()
    except KeyboardInterrupt:
        server.is_active = False
        print(f"\n Shutting down the server... Please wait.\n")
