import socket, threading, time, json

def get_mtu():
    '''Attempts to return the MTU for the network by finding the min of the first hop MTU and 576 bytes. i.e min(MTU_fh, 576)

    Note that the 576 byte sized MTU does not account for the checksum/ip headers so when sending data we need to take the IP/headers/checksum into account.
    '''
    return 576

def check_port(port):
    '''Checks if a port is valid.

    A port is restricted to be a 16 bit integer which is in the range 0 < port < 65535. Typically most application will use ports > ~5000

    Args:
        port (int): The port number. ValueError raised if it is not an int.

    Returns:
        bool: Only will return True. Anything invalid will result in a ValueError

    '''
    if type(port) != int: # Ensure we're dealing with real ports
        raise TypeError("port must be an int between 0 and 65535")
    elif port < 0 or port > 65535:
        raise ValueError("port must be an int between 0 and 65535")
    else:
        return True

def get_payload_size(payload):
    '''Take UDP payload and  calculate the size in bytes. Should be structured as a dict. Note this method is slightly expensive because it encodes a dictionary as a JSON string in order to calculate the length

    We also set the separators to exclude spaces in the interest of saving data due to spaces being unnecessary

    Args:
        payload(obj): A JSON serializable object representing the payload data

    Returns:
        int: The size of the data in bytes of the payload
    '''
    data = json.dumps(payload, separators=[':', ',']).encode('utf-8')
    return len(data)


class Communicator():
    '''This is a threaded class interface designed to send and receive messages 'asynchronously' via pythons threading interface. It was designed mainly designed for use in communication for the algorithm termed 'Cloud K-SVD'.

    This class provides the following methods

    - listen: Starts the threaded listener
    - send: sends data via the open socket
    - get: retrieve data from the data-store
    - stop: stop listening on the thread
    - receive: process and store information about received packets
    '''

    def __init__(self, protocol, listen_port, send_port=None, use_compression=True):
        '''Constructor

        Args:
            protocol (str): A string. One of 'UDP' or 'TCP' (case insensistive)
            listen_port(int): A port between 0 and 65535
            send_port(int): (Optional) Defaults to value set for listen_port, otherwise must be set to a valid port number.
            use_compression (bool): A boolean representing the whether or not to use compression on packet transmission and decompression on received packets. 
        '''
        protocol = protocol.upper()
        if protocol not in ['TCP', 'UDP']:
            raise ValueError('Protocol must be one of "TCP" or "UDP"')
        else:
            self.protocol = protocol # The protocol an upper case string 'TCP' or 'UDP'
        
        if protocol == 'TCP':
            raise NotImplementedError('TCP not yet implemented. Please use UDP instead')

        # Check and create sockets
        if send_port != None and check_port(send_port):
            self.send_port = send_port
            self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        if check_port(listen_port):
            self.listen_port = listen_port
            self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if send_port == None: # If the port and socket were not set
                self.send_port = self.listen_port
                self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.use_compression = True

        # Set the defaults for the thread and listening object
        self.is_open = True
        self.listen_thread = None
        self.is_listening = False # This tells the listening thread whether or not it need to continue looping to receive messages
        self.mtu = get_mtu()

    def close(self):
        '''Closes both listening sockets and the sending sockets

        The sockets may only be closed once. After closing a new object must be created.

        Args:
            N/A
        
        Returns:
            N/A
        
        Raises:
            BrokenPipeError: If close was already called previously.

        '''
        if self.is_open == True:
            self.stop_listen()
            self.listen_sock.close()
            self.send_sock.close()
            self.is_open = False
        else:
            raise BrokenPipeError('Cannot close. Sockets were previously closed.')
    


    def start_listen(self):
        '''Start listening on port ``self.listen_port``. Creates a new thread where the socket will be created

        Args:
            N/A

        Returns:
            N/A

        '''
        if self.is_open != True:
            raise BrokenPipeError('Cannot listen. Sockets were previously closed.')

        if self.listen_thread == None: # Create thread if not already created
            self.listen_thread = threading.Thread(target=__run_thread__, args=(self, self.listen_sock, '', self.listen_port))
            self.is_listening = True
            self.listen_thread.start()
        

    def __run_listen__(self, _sock, host, port):
        '''Worker method for the threaded listener in order to retrieve incoming messages

        Args:
            _sock (sockets.socket): A socket object to bind to
            host (str): The hostname/IP that we should bind the socket to. Use empty string '' for senders who wish to contact you outside the network.
            port (int): The port as an integer

        Returns:
            N/A

        '''
        
        _sock.bind((host, port))

        while self.is_listening:
            data, addr = _sock.recv(1024) # Receive at max 1024 bytes
            self.receive(data, addr)


        _sock.close()


    def create_packets(self, data, tag):
        '''Segments a chunk of data (payload) into separate packets in order to send in sequence to the desired address.

        The messages sent using this class are encoded JSON objects, that include metadata, so in order to segment into the correct number of packets we also need to calculate the size of the packet overhead (metadata) as well as subtract the IP headers in order to find the maximal amount of payload data we can send in a single packet.

        We need to use the MTU in this case which we'll take as typically a minimum of 576 bytes. According to RFC 791 the maximum IP header size is 60 bytes (typically 20), and according to RFC 768, the UDP header size is 8 bytes. This leaves the bare minimum payload size to be 508 bytes. (576 - 64 - 8).

        The packet payloads are implemented as JSON objects

        ```
        payload = {
            't': ...,
            'd': ...,
            's': ...,
            'n': ...
        }
        ```

        The different fields are defined as follows:

        - ``t`` is the tag for the data
        - ``d`` is the actual data we wish to send
        - ``s`` is the number total number of sequence packets
        - ``n`` is the sequence number of the packet.

        Args:
            data (str): The data as a string which is meant to be sent to its destination
        
        Returns
            list: A list containing the payload for the packets which should be sent to the destination.
        '''
        packets = []
        max_payload = self.mtu - 60 - 8 # conservative estimate to prevent IP fragmenting
        
        # Typical non-sequenced payload metadata
        payload = {'t': tag,
                    'd': ''}
        
        # First check the data size
        payload_size = get_payload_size(payload)
        data_bytes = str(data).encode('utf-8') # Could definitely be more efficient. Lots of whitespace esp. with lists/dicts also terrible with floats...we should find a better way to do this....
        data_size = len(data_bytes)
        # print(payload_size)
        # print(data_size)
        # print(payload_size + data_size)
        # print(max_payload)

        # TWO CASES
        # We can send everything in 1 packet
        # We must break into multiple packets which will require sequencing
        
        if(data_size + payload_size <= max_payload):
            # Assemble the packet, no sequencing
            payload['d'] = data_bytes
            packets.append(payload)
        else:
            # we need to add some more metadata for sequencing
            payload['s'] = 0 # number of packets to 0
            payload['n'] = 0 # sequence number to 0

            # Next step  --> Calculate number of packets req'd and build them

            # payload_size = get_payload_size(payload)
            # print(payload_size)
            # print(payload_size + data_size)
            # print(max_payload)


        return packets




    def send(self, ip, data, tag):
        '''Send a chunk of data with a specific tag to an ip address

        Args:
            ip (str): The hostname/ip to send to
            data (obj): The data object to send
            tag (str): An identifier for the 
        '''

        msg = str(d)
        data = {
            'tag': tag,
            'content': msg
        }
        m = json.dumps(data)
        bts = m.encode('utf-8')
        print(len(bts))
        #s.sendto(msg, (ip, self.send_port))

        
    
    def get(self, label, sender_name):
        '''Get a key/tag combi value from the data store
        '''
        pass

    def stop_listen(self):
        '''Stop listening for new messages and close the socket.

        This will terminate the thread and join it back in.

        '''
        if self.listen_thread !=  None:
            self.is_listening = False
            self.listen_thread.join()
            self.listen_thread = None



    def receive(self, data, addr):
        '''Take a piece of data received over the socket and process the data and attempt to combine packet sequences together, passing them to the data store when ready.

        Args:
            data (bytes): a packet of data received over the socket to process
            addr (str): The ip address or hostname of the sending host

        Returns:
            N/A
        '''
        pass

