'''This file contains functions for using distributed consensus methods such as
 Corrective Consensus[1] and Accelerated Corrective Consensus[2]



- [1] <http://vision.jhu.edu/assets/consensus-cdc10.pdf>
- [2] <http://www.vision.jhu.edu/assets/ChenACC11.pdf>


'''
import time
import math
import pickle
import socket
import struct
import fcntl
import requests
import configparser
import numpy as np
from numpy import linalg as LA
# Consensus Functions


def get_weights(neighbors, config="params.conf"):
    '''Calculate the Metropolis Hastings weights for the current node and its neighbors.

    Args:
            neighbors (iterable): An iterable of neighbor IP addresses to get degrees from

    Returns:
            dict: a dictionary mapping neighbors to Metropolis-Hastings Weights

    '''
    weights = {}
    degs = {}
    conf = configparser.ConfigParser()
    conf.read(config)
    port = conf['node_runner']['port']
    my_deg = len(neighbors)
    for neigh in neighbors:
        res = requests.get('http://{}:{}/degree'.format(neigh, port))
        if res.status_code == 200:
            degs[neigh] = int(res.text)
            weights[neigh] = 1 / (max(degs[neigh], my_deg) + 1)
        else:
            weights[neigh] = 0
            raise RuntimeError("One of the nodes could not be contacted")

    
    weights['self'] = 1 - sum(weights.values())
    return weights


def run(orig_data, tc, tag_id, neighbors, communicator, corr_spacing=5):
    '''Run run corrective consensus v.s. a list of nodes in order to converge on an agreed-upon
         average.

    Args:
            orig_data (matrix): The data which we want to find a consensus with (numpy matrix)
            tc (int): Number of consensus iterations
            tag_id (num): A numbered id for this consensus iteration. Used when sending tag info.abs
            neighbors (dict): an object outlining the neighbors of the current node and the weights
                         corresponding to each one.
            corrective_spacing (number): The spacing parameter for corrective consensus
            communicator (Communicator): The communicator object to send and receive messages.abs

    Returns:
            matrix: A numpy matrix with the agreed-upon consensus values.


    '''
    dim = orig_data.shape[0]  # rows
    print(dim)
    old_data = new_data = orig_data
    size = len(neighbors)
    phi = np.matrix(np.zeros((dim, size)))  # number of communicators
    corr_count = 1
    neigh_list = list(neighbors.keys())

    for i in range(tc):
        if i != corr_count * (corr_spacing + 1) - 1:
            # set q(t) = q(t-1), remember qnew is from last iteration
            old_data = new_data

            # transfer data
            tag = build_tag(tag_id, i)
            b_data = matrix_to_bytes(new_data)
            transmit(b_data, tag, neighbors, communicator)
            data = receive(tag, neighbors, communicator)

            # Consensus
            tempsum = 0  # used for tracking 'mass' transmitted
            for j in neighbors:
                if data[j] != None:  # if data was received, then...
                    t = matrix_from_bytes(data[j])
                    diff = t - old_data
                    tempsum += neighbors[j] * diff  # 'mass' added to itself
                    # print('Neighbors[j] = {}'.format(neighbors[j]))
                    # print("Diff {}".format(diff))
                    ind = neigh_list.index(j)
                    print(diff)
                    print(neighbors[j])
                    # phi[:,ind] += np.reshape(neighbors[j] * diff, (dim, 1))

            new_data = old_data + tempsum  # essentially doing consensus the long way

            # Corrective Iteration
        else:
            pass
            delta = np.matrix(np.zeros((dim, size)))
            v = np.zeros(size)

            # Mass distribution difference is transmitted
            tag = build_tag(tag_id + 1, i)  # 1 for corrective iteration
            p_data = matrix_to_bytes(phi[:, j])
            transmit(p_data, tag, neighbors, communicator)
            phi_data = receive(tag, neighbors, communicator)

            # Mass distribution should be equivalent sent and received
            for j in neighbors:
                if phi_data[j] != None:
                    phi_data[j] = matrix_from_bytes(phi_data[j])
                    ind = neigh_list.index(j)
                    delta[:, ind] = phi[:, ind] + phi_data[j]
                    v[j] = 1
                phi[:, ind] += (-0.5) * delta[:, ind] * v[j]
                # ensures stability if packet loss during corrective
                # transmission
                new_data += -(0.5) * np.reshape(np.sum(delta, 1), (dim, 1))

            corr_count += 1

        return new_data


def matrix_to_bytes(data):
    '''Convert a numpy matrix to an array of bytes to transfer
     over the network*

    *This is just a simple type of implementation. A reason one may
    have for not using something as simple as the pickle library is
     that unpickling data after it has been sent over the
     network can be maliciously modified to execute arbitrary code when
     being unpickled which inherntly presents a serious security hazard.
     Anyone using this code in a security-concious environment should
     replace the matrix_*_bytes pair of methods with a more suitable
    implementation.

    Args:
            data (obj): Data to convert to bytes

    Returns:
            bytes: The data in a byte representation
    '''
    pick = pickle.dumps(data)
    return pick


def matrix_from_bytes(data):
    '''Convert a byte array back into a numpy matrix.

    Please refer to the * note under ``matrix_to_bytes``
    about the security hazard that the pickling implementation
    leaves.

    Args:
            data (bytes): An array of bytes to convert to a numpy
             matrix

    Returns:
            obj: An numpy matrix which was originally represented as bytes.

    '''
    return pickle.loads(data)


def transmit(data, tag, neighbors, communicator):
    '''Send the data to every neighbor.

    Args:
            data (bytes): The bytes to transmit
            tag (bytes): The bytes representing the tag for the data
            neighbors (iterable): An iterable item containing the neighbors which we
                         want to send data to
            communicator (Communicator): The object used in sending and receiving data

    Returns:
            N/A
    '''
    for n in neighbors:
        communicator.send(n, data, tag)


def receive(tag, neighbors, communicator):
    '''Attempt to retrieve the data from a set of neighbors

    Args:
            tag (bytes): a set of bytes identifying the data tag to retrieve
            neighbors (iterable): a list or dictionary of neighbors to retrieve data from
            communicator (Communicator): The communicator object which can access the data.

    Returns:
            dict: A dictionary mapping each neighbor to the data which is sent.
    '''
    d = {}
    missing = 0
    chk = []
    for n in neighbors:
        tmp = communicator.get(n, tag)
        if tmp == None:
            missing += 1
            chk.append(n)
        else:
            d[n] = tmp

    time.sleep(missing * .1) # Only attempt at synchronization we have so far
    for n in chk:
        d[n] = communicator.get(n, tag)

    return d


def build_tag(tag_id, num):
    tag = (tag_id % 256).to_bytes(1, byteorder='little')
    if num > 0:
        bts = math.log(num, 2)  # number of bits required
        bts = math.ceil(bts / 8)  # number of bytes required
    else:
        bts = 3
    bts = max(3, bts)  # Should always give us at least 3 bytes to work with.
    tag += num.to_bytes(bts, byteorder='little')[0:3]
    return tag


# def correctiveConsensus(z, tc, weights, comm_world_obj, graph_obj, node_names,
#                         trans_tag, corr_spacing, timeout):
#     '''Run a version of distributed consensus
#     '''

#     # Detailed in the paper- the proof presented in the paper is somewhat simple
#     # Figure it out, because this code is definitely not simple
#     datadim = z.shape[0]
#     rank = comm_world_obj.Get_rank()
#     size = comm_world_obj.Get_size()
#     q, qnew = (z), (z)
#     phi = np.matrix(np.zeros((datadim, size)))
#     corr_count = 1

#     for cons_iter in range(tc):

#         # Regular Iteration
#         if cons_iter != corr_count * (corr_spacing + 1) - 1:
#             # set q(t) = q(t-1), remember qnew is from last iteration
#             q = qnew
#             # transfer data
#             data = transmit_data(qnew, comm_world_obj, graph_obj, node_names,
#                                  trans_tag, timeout)
#             # Consensus
#             tempsum = 0  # used for tracking 'mass' transmitted
#             for j in graph_obj.Get_neighbors(rank):
#                 if data[j] != None:  # if data was received, then...
#                     difference = data[j] - q
#                     # 'mass' added to itself
#                     tempsum += weights[j] * (difference)
#                     phi[:, j] += np.reshape((weights[j]
#                                              * (difference)), (datadim, 1))
#             # update local data
#             qnew = q + tempsum  # essentially doing consensus the long way
#             # Corrective Iteration
#         else:
#             Delta = np.matrix(np.zeros((datadim, size)))
#             v = np.zeros(size)
#             # Mass distribution difference is transmitted
#             phidata = transmit_data(phi[:, j], comm_world_obj, graph_obj, node_names,
#                                     trans_tag, timeout)
#             # Mass distribution should be equivalent sent and received
#             for j in graph_obj.Get_neighbors(rank):
#                 if phidata[j] != None:  # if 'mass disr.' transmision was succesful
#                     Delta[:, j] = phi[:, j] + phidata[j]
#                     v[j] = 1
#             # ensures stability if packet loss during corrective transmission
#             phi[:, j] += (-0.5) * Delta[:, j] * v[j]
#             qnew += -(0.5) * np.reshape(np.sum(Delta, 1), (datadim, 1))

#             corr_count += 1

#     return qnew  # q(t) after processing


def get_ip_address(ifname):
    '''Returns the IP Address

    Should be friendly with python2 and python3. Tested using a Raspberry Pi running Linux.
    Will not work with windows. Possibly with OS X/MacOS

    Args:
            ifname (str): Name of the network interface

    Returns:
            str: A string representing the 4x8 byte IPv4 address assigned to the interface.

    Throws:
            err: Will throw error if the interface doesn't exist. Use with method within try/catch.
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname.encode('utf-8')))[20:24])
    return ip


def power_method(M, tc, tp, weights, comm_world_obj, graph_obj, node_names,
                 trans_tag, corr_spacing, timeout):
    # Calls on a Consensus method to figure out top eigenvector
    datadim = M.shape[0]
    rank = comm_world_obj.Get_rank()
    size = comm_world_obj.Get_size()
    q = np.matrix(np.ones((datadim, 1)))
    qnew = q
    phi = np.matrix(np.zeros((datadim, size)))
    corr_count = 1

    for powerIteration in range(0, tp, 1):
        # We use corrective consensus here, regular consensus works too
        qnew = (M * qnew)
        qnew = correctiveConsensus(qnew, tc, weights, comm_world_obj, graph_obj, node_names,
                                   trans_tag, corr_spacing, timeout)
        if LA.norm(qnew) != 0:
            qnew /= LA.norm(qnew)  # normalize

    return qnew.reshape(datadim)  # returns eigenvector in 1d
