import numpy as np 
import scipy as sp
import time
from numpy import linalg as LA
from ConsensusMethods import *
from mpi4py import MPI

#Main Functions

def time_sync(tic,wait_period): #Simpler to use MPI barrier command, but that's sorta cheating
    #Use as follows:
    #tic = time.time() sets the tic to the current time
    #function(x,y,z) is called that takes variable amount of time to run
    #time_sync(tic,wait_period) makes sure each node waits until (wait_period)
    #seconds after the tic time; so, every node is given at most (wait_period)
    #time before the network continues with the rest of its commands
    current = time.time()
    while current<(tic+wait_period): 
        # print 'waiting...'
        time.sleep(0.1)
        current = time.time()  

def discoverDegrees(c,comm,node_names):
    #Figures out the degree matrix of the network by contacting neighbors
    #Necesary to know degrees of neighbors for Metropolis-Hastings Weights
    rank = MPI.COMM_WORLD.Get_rank()
    size = MPI.COMM_WORLD.Get_size()
    print "I am %s, my degree is: %d" % (node_names[rank], 
        c.Get_neighbors_count(rank)) , " and my neighbors are: ", c.Get_neighbors(rank)

    #Degree matrix
    degrees = np.zeros(size)
    tempedges = (c.Get_neighbors(rank))
    tempedges.append(rank)

    for x in (tempedges):
        comm.send(c.Get_neighbors_count(rank)+1,x, tag=7)
        degrees[x] = comm.recv(source=x, tag=7)

    print "I am %s, my degree matrix is: " % (node_names[rank]) , degrees

    return degrees


def OMP(D,Y,L):
    #Occasionally has a convergence issue with pinv function
    N = D.shape[0]
    K = D.shape[1]
    P = Y.shape[1]
    A = np.matrix('')

    if(N != Y.shape[0]):
        print "Feature-size does not match!"
        return

    for k in range(0,P):

        a = []
        x = Y[:,k]
        residual = x
        indx = [0]*L

        for j in range(0,L):
            proj = np.dot(np.transpose(D),residual)
            k_hat = np.argmax(np.absolute(proj))
            indx[j] = k_hat
            t1 = D[:,indx[0:j+1]]
            a = np.dot(np.linalg.pinv(t1),x)
            residual = x - np.dot(D[:,indx[0:j+1]],a) 
            if(np.sum(np.square(residual)) < 1e-6):    #1e-6 = magic number to quit pursuit
                break
        temp = np.zeros((K,1))
        temp[indx[0:j+1]] = a;

        if (A.size == 0):
            A = temp
        else:
            A = np.column_stack((A,temp))

    return A


def CloudKSVD(D,Y,refvec,tD,t0,tc,tp,weights,comm,c,node_names,Tag,
    CorrectiveSpacing,timeOut): #comm = MPI.COMM_World, c = Create_graph
    #I hope you know what this does :^)

    rank = MPI.COMM_WORLD.Get_rank()
    size = MPI.COMM_WORLD.Get_size()
    ddim = np.shape(D)[0]
    K = np.shape(D)[1]
    S = np.shape(Y)[1]
    x = np.matrix(np.zeros((K,S)))
    rerror = np.zeros(tD)

    for t in xrange(0,tD): #iterations of kSVD

        if rank == 0:
            print '=================Iteration %d=================' % (t+1)

        for s in xrange(0,S):
            x[:,s] = OMP(D,Y[:,s],t0)

        for k in xrange(0,K):
            if rank == 0:
                print 'Updating atom %d' % (k+1)
            #Error matrix
            wk = [i for i,a in enumerate((np.array(x[k,:])).ravel()) if a!=0]
            Ek = (Y-np.dot(D,x)) + (D[:,k]*x[k,:])
            ERk = Ek[:,wk]

            #Power Method
            if np.size(wk) == 0: #if empty
                M = np.matrix(np.zeros((ddim,ddim)))
            else:
                M = ERk*ERk.transpose()
            q = powerMethod(M,tc,tp,weights,comm,c,node_names,
                            Tag,CorrectiveSpacing,timeOut)

            #Codebook Update
            if np.size(wk) != 0: #if not empty
                refdirection = np.sign(np.array(q*refvec)[0][0])
                if LA.norm(q) != 0:
                    D[:,k] = (refdirection*(q/(LA.norm(q)))).reshape(ddim,1)
                else:
                    D[:,k] = q.reshape(ddim,1)
                x[k,:] = 0
                x[k,wk]= np.array(D[:,k].transpose()*ERk).ravel()

        #Error Data
        rerror[t] =np.linalg.norm(Y-np.dot(D,x))
        print "Node %s Iteration %d error:" % (node_names[rank],t+1) , rerror[t]
        time.sleep(0.2)

    return D,x,rerror


def ActiveDictionaryFilter(D,Y,NewSignals,T0): 
    #Based on "Active dictionary learning for image representation" - Wu, Sawarte, & Bajwa
    #Rather than calling K-SVD or Cloud K-SVD, the function simply returns a new matrix 
    #with the "worst" represented signal added on. After calling this, you can call either 
    #Cloud or Local K-SVD with the new training pool P that includes the worst represented
    #sample. Repeat this process until a desired number of samples are added

    #Variables set to same names as paper!
    Yt = NewSignals
    N  = np.shape(Yt)[1] #number of new signals
    Theta = OMP(D,Yt[:,i],T0)
    Yhat = np.matrix(D*Theta) #sparse representation of new signals with given dictionary
    rep_error = np.matrix(np.zeros(N))

    for i in xrange(1,N): #Determines worst represented signal
        rep_error[i] = LA.norm(Y[:,i]-Yhat[:,i])**2 #L2 Norm Squared

    S = Yt[:,np.argmax(rep_error)] #pick the worst represented signal
    P = np.concatenate((P,S),1)    #add it to the training pool

    return P,np.argmax(rep_error)  #returns training pool and index of signal from batch




