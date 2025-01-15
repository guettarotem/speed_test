import socket
import struct
import sys
import threading
import time
from network_config import *

lock_print = threading.Lock()

# ANSI color codes
class Colors:
    RESET = "\033[0m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    YELLOW = "\033[33m"

class Client:
    def __init__(self):
        self.serverIp = None
        self.sudp_port = None
        self.stcp_port = None
        self.tcp_connections = 0
        self.udp_connections = 0
        self.file_size = 0
        self.is_active = True
        self.bordacst = BROADCAST_PORT

    def thread_safe_print(self, message, color=Colors.RESET):
        with lock_print:
            print(f"{color}{message}{Colors.RESET}")

    def transfer_udp(self, thread_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                packet = struct.pack('!IBQ', MAGIC_COOKIE, REQUEST_TYPE, self.file_size)
                sock.sendto(packet, (self.serverIp, self.sudp_port))
                sock.settimeout(1.0)

                received_packets = 0
                total_packets = 0
                total_chunks = 1
                current_chunk = 0
                start_time = time.time()

                try:
                    while current_chunk < total_chunks:
                        packet, _ = sock.recvfrom(4096)
                        total_packets += 1
                        cookie, msg_typ, total_chunks, rec_chunk = struct.unpack('!IBQQ', packet[:PAYLOAD_HEADER_SIZE])

                        if cookie != MAGIC_COOKIE or msg_typ != PAYLOAD_TYPE:
                            raise ValueError

                        if rec_chunk == current_chunk + 1:
                            current_chunk = rec_chunk
                            received_packets += 1
                except socket.timeout:
                    pass

                total_time = time.time() - start_time
                speed = (received_packets * 8 * RECEIVE_SIZE) / total_time if total_time > 0 else 0
                success_rate = (received_packets / total_packets * 100) if total_packets > 0 else 0

                self.thread_safe_print(
                    f"UDP transfer #{thread_id} finished, total time: {total_time:.2f} seconds, "
                    f"total speed: {speed:.1f} bits/second, "
                    f"percentage of packets received successfully: {success_rate:.1f}%",
                    color=Colors.GREEN
                )

        except (ConnectionResetError, socket.error) as e:
            self.thread_safe_print(f"Error during UDP test #{thread_id}: {e}", color=Colors.RED)

    def transfer_tcp(self, thread_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.serverIp, self.stcp_port))

                request_packet = struct.pack('!IBQ', MAGIC_COOKIE, REQUEST_TYPE, self.file_size)
                sock.sendall(request_packet)

                current_chunk = 0
                total_chunks = 1
                bytes_received = 0
                start_time = time.time()

                while current_chunk < total_chunks:
                    data = sock.recv(self.file_size + PAYLOAD_HEADER_SIZE)
                    if not data:
                        break

                    cookie, msg_type, total_chunks, chunk_num = struct.unpack('!IBQQ', data[:PAYLOAD_HEADER_SIZE])

                    if cookie != MAGIC_COOKIE or msg_type != PAYLOAD_TYPE:
                        raise ValueError("Invalid TCP payload received")

                    if chunk_num != current_chunk + 1:
                        raise ValueError(f"Expected chunk {current_chunk + 1}, but got {chunk_num}")

                    current_chunk = chunk_num
                    bytes_received += len(data[PAYLOAD_HEADER_SIZE:])

                total_time = time.time() - start_time
                speed = (bytes_received * 8) / total_time if total_time > 0 else 0

                self.thread_safe_print(
                    f"TCP transfer #{thread_id} finished, total time: {total_time:.2f} seconds, "
                    f"total speed: {speed:.1f} bits/second",
                    color=Colors.GREEN
                )

        except (ConnectionRefusedError, socket.error) as e:
            self.thread_safe_print(f"TCP Connection {thread_id} failed: {str(e)}", color=Colors.RED)

    def handle_offer(self):
        threads = []
        self.thread_safe_print("Starting transfer tests...", color=Colors.BLUE)

        # Start UDP transfers
        for i in range(1, self.udp_connections + 1):
            thread = threading.Thread(target=self.transfer_udp, args=(i,))
            threads.append(thread)
            thread.start()

        # Start TCP transfers
        for i in range(1, self.tcp_connections + 1):
            thread = threading.Thread(target=self.transfer_tcp, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all transfers to complete
        for thread in threads:
            thread.join()

        self.thread_safe_print("All transfers complete, listening to offer requests", color=Colors.BLUE)

    def listen_for_offers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as offer_sock:
            offer_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            offer_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Bind to all interfaces
            offer_sock.bind(('0.0.0.0', self.bordacst))

            self.thread_safe_print("Client is active, listening for server offers...", color=Colors.YELLOW)

            while True:
                try:
                    packet, addr = offer_sock.recvfrom(RECEIVE_SIZE)
                    self.thread_safe_print(f"Received packet of length {len(packet)} from {addr}", color=Colors.YELLOW)

                    if len(packet) < 8:  # Minimum size for the expected packet
                        continue

                    magic_cookie, msg_type, udp_port, tcp_port = struct.unpack("!IBHH", packet)
                    self.thread_safe_print(f"Unpacked values: magic={hex(magic_cookie)}, type={msg_type}, "
                                           f"UDP={udp_port}, TCP={tcp_port}", color=Colors.YELLOW)

                    if magic_cookie == MAGIC_COOKIE and msg_type == OFFER_TYPE:
                        self.serverIp = addr[0]
                        self.sudp_port = udp_port
                        self.stcp_port = tcp_port
                        self.thread_safe_print(f"Received valid offer from {addr[0]}:{udp_port}", color=Colors.GREEN)
                        return
                    else:
                        self.thread_safe_print(f"Invalid packet: wrong magic cookie or message type", color=Colors.RED)

                except struct.error as e:
                    self.thread_safe_print(f"Error unpacking packet: {e}", color=Colors.RED)
                except Exception as e:
                    self.thread_safe_print(f"Error receiving broadcast: {e}", color=Colors.RED)
                time.sleep(0.1)

    def setup(self):
        try:
            self.file_size = int(input("Enter file size in bytes:"))
            if self.file_size <= 0:
                raise ValueError("File size must be a positive integer.")
            self.tcp_connections = int(input("Enter the number of concurrent TCP connections: "))
            if self.tcp_connections <= 0:
                raise ValueError("Number of TCP connections must be a positive integer.")
            self.udp_connections = int(input("Enter the number of concurrent UDP connections: "))
            if self.udp_connections <= 0:
                raise ValueError("Number of UDP connections must be a positive integer.")

        except ValueError as e:
            self.thread_safe_print(f"Invalid input: {e}. Please try again.", color=Colors.RED)
            self.setup()

    def run(self):
        self.setup()
        while self.is_active:
            self.listen_for_offers()
            self.handle_offer()


if __name__ == "__main__":
    client = Client()
    try:
        client.run()
    except KeyboardInterrupt:
        print(f"{Colors.RED}\nKeyboardInterrupt detected. Exiting gracefully...{Colors.RESET}\n")
        sys.exit(0)
    except ValueError as ve:
        print(f"{Colors.RED}\nError: {ve}. Exiting...{Colors.RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}\nAn unexpected error occurred: {e}. Exiting...{Colors.RESET}\n")
        sys.exit(1)
    finally:
        print(f"{Colors.GREEN}Thank you for using the Client!{Colors.RESET}")
