# speed_test

## Overview
This project implements a client-server architecture for testing network performance through concurrent TCP and UDP transfers. The server broadcasts its availability, and clients can connect to perform multiple simultaneous data transfers using both TCP and UDP protocols.

## Components

### Server
The server component provides the following functionality:
- Broadcasts its presence on the network
- Handles concurrent TCP and UDP connections
- Supports multiple simultaneous file transfers
- Provides colored console output for easy monitoring
- Implements thread-safe operations

### Client
The client component offers:
- Detection of server broadcasts
- Concurrent TCP and UDP transfer testing
- Performance measurements (speed, success rate)
- User-configurable number of connections and file sizes
- Colored console output for status monitoring

## Configuration
The network configuration is defined in `network_config.py` (not shown), which should contain the following constants:
```python
MAGIC_COOKIE = 0x12345678  # Packet identifier
OFFER_TYPE = 0x02          # Server offer message type
REQUEST_TYPE = 0x03        # Client request message type
PAYLOAD_TYPE = 0x04        # Data payload message type
SERVER_UDP_PORT = 13117    # Default server UDP port
SERVER_TCP_PORT = 13118    # Default server TCP port
BROADCAST_PORT = 13117     # Port for broadcast messages
RECEIVE_SIZE = 1024        # Default buffer size
PAYLOAD_HEADER_SIZE = 21   # Size of payload header
```

## Usage

### Starting the Server
```bash
python server.py
```
The server will start broadcasting its presence and listening for client connections.

### Running the Client
```bash
python client.py
```
When prompted:
1. Enter the desired file size in bytes
2. Specify the number of concurrent TCP connections
3. Specify the number of concurrent UDP connections

## Features

### Server Features
- Automatic IP detection and broadcast
- Thread-safe operations
- Concurrent connection handling
- Color-coded console output
- Graceful shutdown handling

### Client Features
- Automatic server discovery
- Configurable transfer parameters
- Performance metrics calculation
- Multiple concurrent connections
- Color-coded status messages

## Performance Metrics
The client measures and reports:
- Total transfer time
- Transfer speed (bits/second)
- Packet success rate (UDP only)
- Connection success/failure status

## Error Handling
Both client and server implement comprehensive error handling for:
- Network connection issues
- Invalid packets
- Timeout scenarios
- Resource allocation
- Invalid user input

## Console Output
The application uses color-coded console output:
- GREEN: Success messages
- RED: Error messages
- BLUE: Status updates
- YELLOW: Information messages
- RESET: Normal text

## Known Limitations
1. Broadcast messages only work on local network
2. Performance dependent on network conditions
3. Large file transfers may require additional memory
4. No encryption or security measures implemented

## Debugging
Both client and server provide detailed logging through colored console output. Key areas to monitor:
- Connection establishment
- Transfer progress
- Error messages
- Performance metrics

## Contributing
To contribute to this project:
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Submit a pull request

## Common Issues and Solutions
1. **Connection Refused**: Verify server is running and ports are available
2. **Broadcast Not Received**: Check network broadcast settings
3. **Performance Issues**: Adjust file size and connection counts
4. **Port Conflicts**: Modify port numbers in network_config.py
