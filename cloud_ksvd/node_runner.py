import time
import sys
import json
from urllib.parse import urlparse
from configparser import ConfigParser
from multiprocessing import Process, Value
from flask import Flask, request
from cloud_comm import Communicator

app = Flask(__name__)
task_running = Value('i', 0, lock=True) # 0 == False, 1 == True
conf_file = 'params.conf'

@app.route("/start/consensus")
def run():
    '''Start running distributed consensus on a separate process.

    The server will not kick off a new consensus job unless the current consensus has already completed.

    Args:
        N/A

    Returns:
        str: A message detailing whether or not the consensus job was started or not.
    '''
    msg = ""
    global task_running
    if task_running.value != 1:
        p = Process(target=kickoff, args=(task_running,))
        p.daemon = True
        p.start()
        msg = "Started Running Consensus"
        with task_running.get_lock():
            task_running.value = 1
    else:
        msg = "Consensus Already Running. Please check logs"

    return msg

@app.route("/start/cloudksvd")
def run2():
    '''Placeholder for when we want to start running Cloud K-SVD using this paradigm.
    '''
    global task_running
    return "We can't run Cloud K-SVD quite yet. Please check back later."

def kickoff(task):
    '''The worker method for running distributed consensus. 
    '''
    # This the where we would need to do some node discovery, or use a pre-built graph
    # in order to notify all nodes they should begin running
    global conf_file
    print("Processing for 5 seconds......")
    config = ConfigParser()
    config.read(conf_file)
    port = config['consensus']['udp_port']
    c = Communicator('udp', int(port))
    c.listen()
    ########### Run Consensus Here ############
    time.sleep(7)
    ###########################################
    c.stop_listen()
    print("Finished Processing")
    with task.get_lock():
        task.value = 0

@app.route('/degree')
def get_degree():
    '''Get the degree of connections for this node.

    We assume the node is always connected to itself, so the number should always be atleast 1.
    '''
    global conf_file
    c = ConfigParser()
    c.read(conf_file)
    o = urlparse(request.url).hostname
    a = json.loads(c['graph']['nodes'])
    e = json.loads(c['graph']['edges'])
    try:
        i = a.index(o)
    except:
        i = -1
        pass
    cnt = 0
    i = int(request.args.get('ind'))

    # Print upper triangular matrix
    # for x in range(len(e)):
    #     print( x*3*' ' +  str(e[x]))

    for x in range(len(e)):
        if x < i and i < len(a):
            cnt += e[x][i-x]
            # print("added to count")
            # print("Added e[x][i-x] = {}".format(e[x][i-x]))

    if i < len(e):
        for d in e[i]:
            cnt += d

    return str(cnt)




if __name__ == "__main__":

    # Use a different config other than the default if user specifies
    global config_file
    config = ConfigParser()
    if len(sys.argv) > 1:
        conf_file = sys.argv[1]
    else:
        conf_file = "params.conf"
    config.read(conf_file)

    nr = config['node_runner']
    app.run(nr['host'], nr['port'])