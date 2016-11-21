import numpy as np
import scipy as sp
from numpy import linalg as LA
from ConsensusMethods import *
from mpi4py import MPI
from MNIST_Loader import *
from MainMethods import *


def start():
    print "here 1"
    '''Start running a debugging version of the Cloud K-SVD Algorithm'''
    ## Network and Global Variable Setup
    comm = MPI.COMM_WORLD
    print "here 2"
    comm1= MPI.Intracomm(comm)
    print "here 3"
    rank = MPI.COMM_WORLD.Get_rank()
    print "here 4"
    size = MPI.COMM_WORLD.Get_size()
    print "here 5"
    name = MPI.Get_processor_name()
    print "here 6"
    index = [4,8,12,16,20]
    print "here 7" 
    edges = [1,2,3,4,0,2,3,4,0,1,3,4,0,1,2,4,0,1,2,3] #fully connected network!
    print "here 8"
    c = comm1.Create_graph(index, edges, reorder = False) 
    print "here 9"
    np.set_printoptions(precision=3)
    print "here 10"
    node_names = list('ABCDE')
    print "here 11"
    transmissionTag = 4
    print "here 12"
    degrees = discoverDegrees(c,comm,node_names)
    print "here 13"
    time.sleep(0.5) #keeps node outputs clean
    print "here 14"
    weights = writeWeights(comm,c,degrees)
    print "here 15"

    tic = time.time()
    print "here 16"

    ##################################################
    ################ Debugging option ################
    option = ['transfer','consensus','power']
    print "here 17"
    # Choose an option to test here
    test = option[2]
    print "here 18"
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