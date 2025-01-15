import socket
import time
import struct
import threading

from network_config import *

lock_print = threading.Lock()


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"


class Server:

    def __init__(self):
        self.server_udp_port = SERVER_UDP_PORT
        self.server_tcp_port = SERVER_TCP_PORT
        self.is_active = True
        self.broadcasting_port = BROADCAST_PORT
        self.udp_sync_lock = threading.Lock()

    def thread_safe_print(self, message, color=Colors.RESET):
        """Print messages with thread safety and color."""
        with lock_print:
            print(f"{color}{message}{Colors.RESET}")

    def create_offer_packet(self):
        packet = struct.pack("!IBHH", MAGIC_COOKIE, OFFER_TYPE, SERVER_UDP_PORT, SERVER_TCP_PORT)
        return packet

    @property
    def ip_address(self):
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    def handle_requests(self):
        self.thread_safe_print("Waiting for client connections...", Colors.CYAN)
        tcp_thread = threading.Thread(target=self.tcp_requests)
        udp_thread = threading.Thread(target=self.udp_requests)

        try:
            tcp_thread.start()
            udp_thread.start()
        except Exception as e:
            self.thread_safe_print(f"Error starting threads: {e}", Colors.RED)

    def tcp_requests(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("", self.server_tcp_port))
            while self.is_active:
                sock.listen()
                client_conn, addr = sock.accept()
                threading.Thread(target=self.handle_tcp, args=(client_conn, addr)).start()

    def udp_requests(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("", self.server_udp_port))
            while self.is_active:
                packet, addr = sock.recvfrom(4096)
                try:
                    cookie, msg_type, file_size = struct.unpack("!IBQ", packet[:13])
                    if cookie == MAGIC_COOKIE and msg_type == REQUEST_TYPE:
                        threading.Thread(target=self.handle_udp, args=(sock, addr, file_size)).start()
                except Exception as e:
                    self.thread_safe_print(f"Error handling UDP request: {e}", Colors.RED)

    def handle_tcp(self, conn, addr):
        try:
            data = conn.recv(1024)
            magic, msg_type, file_size, endline_char = struct.unpack('!4sBQI', data[:14])

            if magic != MAGIC_COOKIE or msg_type != REQUEST_TYPE or endline_char != ord('\n'):
                raise ValueError("Invalid TCP request format")

            self.thread_safe_print(f"Received TCP request from {addr}, file size: {file_size} bytes", Colors.GREEN)

            payload = struct.pack('!4sBQQ', MAGIC_COOKIE, PAYLOAD_TYPE, 1, 1) + b'x' * file_size
            conn.sendall(payload)

            self.thread_safe_print(f"TCP transfer to {addr} completed successfully", Colors.BLUE)
        except Exception as e:
            self.thread_safe_print(f"Error during TCP request from {addr}: {e}", Colors.RED)
        finally:
            conn.close()

    def handle_udp(self, sock, client_addr, file_size):
        try:
            total_chunks = (file_size + 1023) // 1024
            remain_bytes = file_size

            for chunk in range(total_chunks):
                payload = min(remain_bytes, 1024)
                packet = struct.pack("!IBQQ", MAGIC_COOKIE, PAYLOAD_TYPE, total_chunks, chunk + 1) + b"x" * payload
                remain_bytes -= 1024
                with self.udp_sync_lock:
                    sock.sendto(packet, client_addr)
            self.thread_safe_print(f"UDP transfer to {client_addr} completed successfully", Colors.BLUE)
        except Exception as e:
            self.thread_safe_print(f"Error during UDP transfer to {client_addr}: {e}", Colors.RED)

    def broadcast_offer(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_sock:
            broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            broadcast_sock.bind(('0.0.0.0', self.broadcasting_port))

            while True:
                packet = self.create_offer_packet()
                broadcast_sock.sendto(packet, ('255.255.255.255', self.broadcasting_port))
                self.thread_safe_print(f"Sent offer to broadcast on port {self.broadcasting_port}", Colors.YELLOW)
                time.sleep(1)

    def run(self):
        self.thread_safe_print(f"Server started, listening on IP address {self.ip_address}", Colors.GREEN)
        broadcast_thread = threading.Thread(target=self.broadcast_offer)
        broadcast_thread.start()

        self.handle_requests()


if __name__ == "__main__":
    server = Server()
    try:
        server.run()
    except KeyboardInterrupt:
        server.is_active = False
        print(f"{Colors.MAGENTA}\nShutting down the server... Please wait.{Colors.RESET}")
