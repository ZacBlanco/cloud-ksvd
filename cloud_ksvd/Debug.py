import numpy as np
import scipy as sp
from numpy import linalg as LA
from ConsensusMethods import *
from mpi4py import MPI
from MNIST_Loader import *
from MainMethods import *


def start():
    '''Start running a debugging version of the Cloud K-SVD Algorithm'''
    ## Network and Global Variable Setup
    comm = MPI.COMM_WORLD
    comm1= MPI.Intracomm(comm)
    rank = MPI.COMM_WORLD.Get_rank()
    size = MPI.COMM_WORLD.Get_size()
    name = MPI.Get_processor_name()
    index = [4,8,12,16,20] 
    edges = [1,2,3,4,0,2,3,4,0,1,3,4,0,1,2,4,0,1,2,3] #fully connected network!
    c = comm1.Create_graph(index, edges, reorder = False) 
    np.set_printoptions(precision=3)
    node_names = list('ABCDE')
    transmissionTag = 4
    degrees = discoverDegrees(c,comm,node_names)
    time.sleep(0.5) #keeps node outputs clean
    weights = writeWeights(comm,c,degrees)

    tic = time.time()

    ##################################################
    ################ Debugging option ################
    option = ['transfer','consensus','power']
    # Choose an option to test here
    test = option[2]
    ##################################################

    # Various debug methods to test individual functions in "ConsensusMethods.py"

    if test == 'transfer': #Tes

        data_size = 2000 
        timeOut   = 0.100
        mat = np.matrix(np.floor(np.random.rand(data_size,1)*100))
        

        tic = time.time()
        data = transmitData(mat,comm,c,node_names,transmissionTag,timeOut)

        print("%s: Time(ms) taken= %d" % (node_names[rank],((time.time()-tic)*1000)))
        
        time.sleep(0.5)
        print("%s: data dropped= %d" % (node_names[rank],
            (size-len([i for x,i in enumerate(data) if i is not None]))))

    elif test == 'consensus':

        data_size = 10
        tc = 3
        CorrectiveSpacing = 1000
        timeOut =     0.100
        mat = np.matrix(np.floor(np.random.rand(data_size,1)*10))


        tic = time.time()
        average = correctiveConsensus(mat,tc,weights,comm,c,node_names,transmissionTag,
            CorrectiveSpacing,timeOut)

        print("%s: Time(ms) taken= %d" % (node_names[rank],((time.time()-tic)*1000)))

        time.sleep((rank+2)/2)
        print("%s: Average reached: " % (node_names[rank]), np.transpose(average))

    elif test == 'power':

        tc,tp = 2,2 #consensus, power ; iterations
        CorrectiveSpacing = 3
        defaultWait = 0.100
        timeOut =     0.100
        mat = np.floor(np.random.rand(2,2)*100)

        tic = time.time()
        average = powerMethod(mat,tc,tp,weights,comm,c,node_names,
            transmissionTag,CorrectiveSpacing,timeOut)

        print("%s: Time(ms) taken= %d" % (node_names[rank],((time.time()-tic)*1000)))

        time.sleep((rank+2)/2)
        print("%s: Eigenvector estimate reached: " % (node_names[rank]), (average))  

if __name__ == "__main__":
	start()