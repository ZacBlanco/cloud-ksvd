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


class Communicator():
    '''This is a threaded class interface designed to send and receive messages 'asynchronously' via pythons threading interface. It was designed mainly designed for use in communication for the algorithm termed 'Cloud K-SVD'.

    This class provides the following methods

    - listen: Starts the threaded listener
    - send: sends data via the open socket
    - get: retrieve data from the data-store
    - stop: stop listening on the thread
    - receive: process and store information about received packets
    '''

    def __init__(self, protocol, listen_port, send_port=None):
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


        # Set the defaults for the thread and listening object
        self.is_open = True
        self.listen_thread = None
        self.is_listening = False # This tells the listening thread whether or not it need to continue looping to receive messages
        self.mtu = get_mtu()

    def close(self):
        if self.is_open == True:
            self.listen_sock.close()
            self.send_sock.close()
            self.is_open = False
    


    def listen(self):
        '''Start listening on port ``self.listen_port``. Creates a new thread where the socket will be created

        Args:
            N/A

        Returns:
            N/A

        '''
        if self.listen_thread == None: # Create thread if not already created
            self.listen_thread = threading.Thread(target=__run_thread__, args=(self, self.listen_sock, '', self.listen_port))
            self.is_listening = True
            self.listen_thread.start()
        

    def __run_listen__(self, _sock, host, port):
        '''Incurs the actual creation of the thread in order to listen for incoming messages. This is the worker method for the threaded listening interface.

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

