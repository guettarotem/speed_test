import random


#magic cookie ( 4 bytes)
MAGIC_COOKIE = 0xABCDDCBA

# Message types
OFFER_TYPE = 0x02     # Server offer message
REQUEST_TYPE = 0x03   # Client request message
PAYLOAD_TYPE = 0x04   # Server payload message

# Default ports for UDP and TCP communication
SERVER_UDP_PORT =  random.randint(25000, 35000)  # Default UDP port
SERVER_TCP_PORT = random.randint(35001, 45000)  # Default TCP port
BROADCAST_PORT = 13117
PAYLOAD_HEADER_SIZE = 21

RECEIVE_SIZE = 1024
