'''Run with flask as an HTTP server to communicate starting points of CloudK-SVD and Consensus
'''
import sys
import json
import requests
import numpy as np
import consensus
from urllib.parse import urlparse
from configparser import ConfigParser
from multiprocessing import Process, Value
from flask import Flask, request
from cloud_comm import Communicator


APP = Flask(__name__)
TASK_RUNNING = Value('i', 0, lock=True)  # 0 == False, 1 == True
CONF_FILE = 'params.conf'


def data_loader(filename):
    '''Reads in data line by line from file. and stores in Numpy array

    Each line of the file is a new vector with the format 1, 2, 3, ..., n where
     n is the length of the vector

    Args:
        str: name of data file

    Returns:
        Numpy array: vectors read from each line of file

    '''

    vectors = []
    with open(filename, 'r') as f:
        for line in f:
            v = list(map(lambda x: int(x), line.split(' ')))
            vectors.append(v)
        data = np.array(vectors)

    return data


def get_neighbors():
    '''Gets IP addresses of neigbors for given node

    Args:
            N/A

    Returns:
            (iterable): list of IP addresses of neighbors
    '''

    global CONF_FILE
    con = ConfigParser()
    con.read(CONF_FILE)
    v = json.loads(con['graph']['nodes'])
    e = json.loads(con['graph']['edges'])

    ip = consensus.get_ip_address('wlan0')

    try:
        i = v.index(ip)
        print("Index of my node {}".format(i))
    except:
        i = -1
     # Print upper triangular matrix
     # for x in range(len(e)):
     #     print( x*3*' ' +  str(e[x]))

    n = []

    for x in range(len(e)):
        if x < i and i < len(a):
            if e[x][i - x] == 1:
                n.append(v[x + i])
                print("1 at Index: {}".format(x))

    if i < len(e):
        for d in e[i]:
            if d == 1:
                n.append(v[d+i])
                # print("indexes of n: {}".format(d))

    return n


@APP.route("/start/consensus")
def run():
    '''Start running distributed consensus on a
    separate process.

    The server will not kick off a new consensus
     job unless the current consensus has already completed.

    Args:
        N/A

    Returns:
        str: A message detailing whether or not the consensus
         job was started.
    '''
    msg = ""
    global TASK_RUNNING
    if TASK_RUNNING.value != 1:
        p = Process(target=kickoff, args=(TASK_RUNNING,))
        p.daemon = True
        p.start()
        msg = "Started Running Consensus"
        with TASK_RUNNING.get_lock():
            TASK_RUNNING.value = 1
    else:
        msg = "Consensus Already Running. Please check logs"

    return msg


@APP.route("/start/cloudksvd")
def run2():
    '''Placeholder for when we want to start running Cloud K-SVD using this paradigm.
    '''
    global TASK_RUNNING
    return "We can't run Cloud K-SVD quite yet. Please check back later."


def kickoff(task):
    '''The worker method for running distributed consensus.

        Args:
            task (int): The process-shared value denoting whether the taks is running or not.

        Returns
            N/A
    '''
    # This the where we would need to do some node discovery, or use a pre-built graph
    # in order to notify all nodes they should begin running
    global CONF_FILE
    # print("Processing for 5 seconds......")
    config = ConfigParser()

    config.read(CONF_FILE)
    port = config['consensus']['udp_port']
    c = Communicator('udp', int(port))
    c.listen()
    ####### Notify Other Nodes to Start #######
    port = config['node_runner']['port']
    for node in json.loads(config['graph']['nodes']):
        req_url = 'http://{}:{}/start/consensus'.format(node, port)
        requests.get(req_url)
    ########### Run Consensus Here ############
    # Load parameters:
        # Load original data
        # get neighbors and weights get_weights()
        # Pick a tag ID (doesn't matter) --> 1
        # communicator already created
    # weights = consensus.get_weights()
    # with open(filename) as f:
        # data = f.read()
    # consensus_data = consensus.run(data, 150, 1, weights, c)
    # Log consensus data here
    ###########################################
    c.close()
    # print("Finished Processing")
    with task.get_lock():
        task.value = 0


@APP.route('/degree')
def get_degree():
    '''Get the degree of connections for this node.

    We assume the node is always connected to itself, so the number should always be atleast 1.
    '''
    global CONF_FILE
    c = ConfigParser()
    c.read(CONF_FILE)
    # req_url = urlparse(request.url)
    # host = o.hostname
    host = request.args.get('host')
    a = json.loads(c['graph']['nodes'])
    e = json.loads(c['graph']['edges'])
    host_index = a.index(host)
    cnt = 0
    for j in e[host_index]:
        cnt += j
    
    cnt -= 1
    # minus one to exlude no self-loops from count
    return str(cnt)


if __name__ == "__main__":

    # Use a different config other than the default if user specifies
    global config_file
    config = ConfigParser()
    if len(sys.argv) > 1:
        CONF_FILE = sys.argv[1]
    else:
        CONF_FILE = "params.conf"
    config.read(CONF_FILE)

    nr = config['node_runner']
    APP.run(nr['host'], nr['port'])
