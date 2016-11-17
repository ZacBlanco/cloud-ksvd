import socket
import threading
import time
import json
import math
import struct

TAG_SIZE = 4
SEQ_SIZE = 2

def get_mtu():
    '''Attempts to return the MTU for the network by finding the min of the first hop MTU and 576 bytes. i.e min(MTU_fh, 576)

    Note that the 576 byte sized MTU does not account for the checksum/ip headers so when sending data we need to take the IP/protocol headers into account.

    The current implementation just assumes the default minimum of 576. We should try to implement something to actually calculate min(MTU_fh, 576)

    Returns:
        int: 576
    '''
    return 576

def check_port(port):
    '''Checks if a port is valid.

    A port is restricted to be a 16 bit integer which is in the range 0 < port < 65535. Typically most applications will use ports > ~5000

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

def get_payload(payload):
    '''Take data payload and return a byte array of the object. Should be structured as a dict/list object. Note this method is slightly expensive because it encodes a dictionary as a JSON string in order to get the bytes

    We also set the separators to exclude spaces in the interest of saving data due to spaces being unnecessary. This is a primitive way to convert data into bytes and you can load it 

    Args:
        payload(obj): A JSON serializable object representing the payload data

    Returns:
        bytes: The object as a utf-8 encoded string
    '''
    data = json.dumps(payload, separators=[':', ',']).encode('utf-8')
    return data

def decode_payload(payload):
    '''Takes a byte array and converts it into an object using ``json.loads``

    Args:
        payload (bytearray): An array of bytes to decode and convert into an object.

    Returns:
        dict/list: A dictionary or list object depending on the JSON that was encoded
    '''

    data = json.loads(payload.decode('utf-8'), separator([':', ',']))
    return data

class Communicator():
    '''This is a threaded class interface designed to send and receive messages 'asynchronously' via python's threading interface. It was designed mainly designed for use in communication for the algorithm termed 'Cloud K-SVD'.

    This class provides the following methods for users

    - listen: Starts the threaded listener
    - send: sends data via the open socket
    - get: retrieve data from the data-store
    - stop: stop listening on the thread

    The typical sequence will be something like the following:

    1. Take the object you wish to send. Encode it to bytes. i.e. ``my_bytes = str([1, 2, 3, 4, 5]).encode('utf-8')``
    2. After encoding to bytes and creating a communicator, use ``send()`` in order to send it to the listening host. The methods here will take care of packet fragmenting and makes sure messages are reassembled correctly. You must also add a 'tag' to the data. It should be a 4-byte long identifier. For strings this is limited to 4 characters. Anything longer than 4 is truncated
    
      - ``comm.send('IP_ADDRESS', my_bytes, 'tag1')``
    

    3. After sending, there's nothing else for the client to do'
    4. When the packet reaches the other end, each packet is received and catalogged. Once all of the pieces of a message are received, the message is transferred as a whole to the data store where it can be retrieved
    5. Use ``get()`` to retrieve the message from the sender and by tag. ``comm.get('ip', 'tag1')``

    As simple as that!

    Notes:
    
    - A limitation (dependent upon python implementation) is that threaded there may only be a single python thread running at one time due to GIL (Global Interpreter Lock)

    - There is an intermediate step between receiving data and making it available to the user. The object must receive all packets in order to reconstruct the data into its original form in bytes. This is performed by the ``receive`` method.

    - Data segments which have not been reconstructed lie within ``self.tmp_data``. Reconstructed data is within ``self.data_store``
         
    Constructor Docs

    Args:
        protocol (str): A string. One of 'UDP' or 'TCP' (case insensistive)
        listen_port(int): A port between 0 and 65535
        send_port(int): (Optional) Defaults to value set for listen_port, otherwise must be set to a valid port number. 

    '''

    def __init__(self, protocol, listen_port, send_port=None):
        '''Constructor'''
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

        self.listen_sock.setblocking(False) # Set to nonblocking in order to get our threaded server to work :) (We should investigate the performance impact of this)
        # Set the defaults for the thread and listening object
        self.is_open = True
        self.listen_thread = None
        self.is_listening = False # This tells the listening thread whether or not it need to continue looping to receive messages
        self.tmp_data = {}
        self.data_store = {}
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
    


    def listen(self):
        '''Start listening on port ``self.listen_port``. Creates a new thread where the socket will be created

        Args:
            N/A

        Returns:
            N/A

        '''
        if self.is_open != True:
            raise BrokenPipeError('Cannot listen. Sockets were previously closed.')

        if self.listen_thread == None: # Create thread if not already created
            self.listen_thread = threading.Thread(target=self.__run_listen__, args=(self.listen_sock, '', self.listen_port))
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
            try:
                data, addr = _sock.recvfrom(1024) # Receive at max 1024 bytes
                self.receive(data, addr[0])
            except BlockingIOError:
                pass


        _sock.close()

    def build_meta_packet(self, seq_num, seq_total, tag):
        '''Create a bytearray which returns a sequence of bytes based on the metadata

        Args:
            seq_num(int): The packet's sequence number
            seq_total(int): The

        Returns:
            bytearray: A bytearray with the metadata
        '''
        if type(seq_total) != int or type(seq_num) != int:
            raise TypeError("Sequence number and total must be integer") 
        packet = bytearray()
        packet += struct.pack('H', seq_total)
        packet += struct.pack('H', seq_num)
        packet += tag.encode('utf-8')[0:4]
        return packet

    def create_packets(self, data, tag):
        '''Segments a chunk of data (payload) into separate packets in order to send in sequence to the desired address.

        The messages sent using this class are simple byte arrays, which include metadata, so in order to segment into the correct number of packets we also need to calculate the size of the packet overhead (metadata) as well as subtract the IP headers in order to find the maximal amount of payload data we can send in a single packet.

        We need to use the MTU in this case which we'll take as typically a minimum of 576 bytes. According to RFC 791 the maximum IP header size is 60 bytes (typically 20), and according to RFC 768, the UDP header size is 8 bytes. This leaves the bare minimum payload size to be 508 bytes. (576 - 60 - 8).

        We will structure packets as such (not including IP/UDP headers)

        +---------------------+--------------------+---------------+
        | Seq.Total (2 bytes) | Seq. Num (2 bytes) | Tag (4 bytes) | 
        +---------------------+--------------------+---------------+
        |                      Data (500 Bytes)                    |
        +----------------------------------------------------------+

        A limitation is that we can only sequence a total of 2^16 packets which, given a max data size of 500 bytes gives us a maximum data transmission of (2^16)*500 ~= 33MB for a single request.

        Also note that the Seq Num. is zero-indexed so that the maximum sequence number (and the sequence total) will go up to ``len(packets) - 1``. Or in other words, 1 less than the number of packets.

        Args:
            data (bytes): The data as a string which is meant to be sent to its destination
            tag (str): A tag. Only the first 4 bytes (chars) are added as the tag.
        
        Returns
            list: A list containing the payload for the packets which should be sent to the destination.
        '''
        packets = []
        max_payload = self.mtu - 60 - 8 # conservative estimate to prevent IP fragmenting
        metadata_size = 8 # 8 bytes         
        data_size = len(data)
        max_data = max_payload - metadata_size

        # TWO CASES
        # - We can send everything in 1 packet
        # - We must break into multiple packets which will require sequencing
        if(data_size <= max_data):
            # Assemble the packet, no sequencing
            payload = self.build_meta_packet(0, 0, tag)
            payload += data
            packets.append(payload)
        else:
            total_packets = math.floor(data_size/max_payload)
            tp1 = total_packets - 1
            for i in range(total_packets): # [0, total_packets-1]
                p1 = self.build_meta_packet(i, total_packets, tag)

                # Slice data into ~500 byte packs 
                d1 = data[i*max_data:(i+1)*max_data]
                p1 += d1
                packets.append(p1)
            # Build the  final packet 
            p1 = self.build_meta_packet(total_packets, total_packets, tag)
            min_bound = (total_packets) * max_data
            d1 = data[min_bound:]
            p1 += d1
            packets.append(p1)
            
        return packets


    def send(self, ip, data, tag):
        '''Send a chunk of data with a specific tag to an ip address. The packet will be automatically chunked into N packets where N = ceil(bytes/(MTU-68))

        Args:
            ip (str): The hostname/ip to send to
            data (bytes): The bytes of data which will be sent to the other host.
            tag (str): An identifier for the 

        Returns:
            bool: True if all packets were created and sent successfully.
        '''

        # As simple as just creating the packets and sending each one individually
        if self.is_open != True:
            raise BrokenPipeError('Socket was already closed by user')

        ret = True
        packets = self.create_packets(data, tag)
        for packet in packets:
            if (self.send_sock.sendto(packet, (ip, self.send_port)) < 0 ):
                ret = False
        return ret

        
    
    def get(self, ip, tag):
        '''Get a key/tag value from the data store. 

        The data is only going to be located in the data store if every single packet for the given tag was received and able to be reassembled. Otherwise the incomplete data will reside in ``self.tmp_data``.

        The ``self.data_store`` object has the following structure:

        .. code-block:: javascript
        
            {
                ip_address: {
                    tag_1: data,
                    tag_2: data2
                }
            }
        
        
        Args:
            ip (str): The ip address of the host we wish get data from
            tag (str): The data tag for the message which is being received

        Returns:
            bytes: ``None`` if complete data is not found, Otherwise if found will return the data
        
        '''
        data = None
        if ip not in self.data_store:
            data = None
        elif tag not in self.data_store[ip]:
            data = None
        else:
            data = self.data_store[ip][tag]

        return data

    def stop_listen(self):
        '''Stop listening for new messages and close the socket.

        This will terminate the thread and join it back in.

        Args:
            N/A

        Returns:
            N/A

        '''
        if self.listen_thread !=  None:
            self.is_listening = False
            self.listen_thread.join()
            self.listen_thread = None



    def receive(self, data, addr):
        '''Take a piece of data received over the socket and processes the data and attempt to combine packet sequences together, passing them to the data store when ready.

        ``self.tmp_data`` is an object with the structure

        .. code-block:: javascript
        
            {
                ip_address: {
                    tag_1: {
                        'seq_total': Max_num_packets,
                        'packets' = {
                            1: packet_data_1,
                            2: packet_data_2,
                            ...
                            ...
                        }
                    },
                    tag_2: {
                        ...
                    }
                },
                ip_address_2 : {
                    ...
                }
            }

        Args:
            data (bytes): a packet of data received over the socket to process
            addr (str): The ip address or hostname of the sending host

        Returns:
            N/A
        '''
        if addr not in self.tmp_data:
            self.tmp_data[addr] = {}
        
        # disassemble the packet
        seq_total = struct.unpack('H', data[0:2])[0]
        seq_num = struct.unpack('H', data[2:4])[0]
        data_tag = data[4:8].decode('utf-8')
        dat = data[8:]

        # Create an entry for data_tag
        if data_tag not in self.tmp_data[addr]:
            self.tmp_data[addr][data_tag] = {}
            self.tmp_data[addr][data_tag]['packets'] = {}
            self.tmp_data[addr][data_tag]['seq_total'] = seq_total

        if seq_total != self.tmp_data[addr][data_tag]['seq_total'] or self.tmp_data[addr][data_tag]['seq_total'] == None:
            # If the tag existed, make sure the sequence total is equal to the current, otherwise throw away any packets we've already collected
            self.tmp_data[addr][data_tag]['seq_total'] = seq_total
            self.tmp_data[addr][data_tag]['packets'] = {}

        self.tmp_data[addr][data_tag]['packets'][seq_num] = dat

        num_packets = len(self.tmp_data[addr][data_tag]['packets']) 
        # print(self.tmp_data[addr][data_tag]['packets'].keys())
        if  num_packets == seq_total + 1: # seq_total is max index of 0-index based list.
            # Reassmble the packets in order
            reassembled = bytes()
            for i in range(num_packets):
                reassembled += self.tmp_data[addr][data_tag]['packets'][i]
            if addr not in self.data_store:
                self.data_store[addr] = {}
            self.data_store[addr][data_tag] = reassembled
            self.tmp_data[addr][data_tag]['packets'] = {}
            self.tmp_data[addr][data_tag]['seq_total'] = {}



            

        
        


