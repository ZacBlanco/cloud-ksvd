'''This file contains functions for using distributed consensus methods such as Corrective Consensus[1] and Accelerated Corrective Consensus[2]



- [1] <http://vision.jhu.edu/assets/consensus-cdc10.pdf>
- [2] <http://www.vision.jhu.edu/assets/ChenACC11.pdf>


'''

from mpi4py import MPI
from random import randint
import numpy as np
from numpy import linalg as LA
import csv
import time

#Consensus Functions

def writeWeights(comm,c,degrees):
	#Writes Metropolis-Hastings weights to a file
	#Weights needed for consensus
	rank = comm.Get_rank()
	size = comm.Get_size()
	weights = np.zeros(size)
	for x in (c.Get_neighbors(rank)):
		weights[x] = 1/(max(degrees[x],degrees[rank])+1)
		
	weights[rank] = 1 - sum(weights[:])
		
	#with open('MHweights.csv','wb') as csvfile:
	#	datawriter = csv.writer(csvfile,delimiter=',')
	#	datawriter.writerow(weights)
	return weights

def transmitData(z,comm_worldObject,graphObject,node_names,transmissionTag,timeOut):
	#Transmits data with time outs for messaging (only for data_size<=100)
	comm,c = comm_worldObject,graphObject
	size = comm.Get_size()
	rank = comm.Get_rank()
	data_size = np.shape(z)[0] #data_size refers to its dimension
	data = [None]*size

	if data_size<=100:
		#transmits data repeatedly over the "timeOut" value 
		transmit_data = z
		status = [False]*size
		receiver = [MPI.REQUEST_NULL]*size
		retry = []
		tic = time.time()
		#sends out data and stores receiver objects
		for j in c.Get_neighbors(rank):
			comm.send(transmit_data,j,tag=transmissionTag)
		for j in c.Get_neighbors(rank):
			rectemp = comm.irecv(source=j,tag=transmissionTag)
			receiver[j] = (rectemp)
		#receiver objects constantly check for incoming data over timeOut period
		time.sleep(0.050) #waits 50 ms for data by default
		for j in c.Get_neighbors(rank):
			status[j],data[j] = receiver[j].test() #status and data values
		#list of neighbors that data has not been downloaded from yet
		retry = [i for i, node_status in enumerate(status) if (node_status==False)]	

		intialTime = time.time()
		while (retry != []): #while there are receivers needing retries
			for j in retry:
				if (time.time()-intialTime) > timeOut:
					#print "%s timing out on %s" % node_names[rank],node_names[j]
					retry.remove(j) #remove from retry list after timeOut
					break
				else: 
					status[j],data[j] = receiver[j].test()
					if status[j]: #status will be rue if data was succesfully recv'd
						retry.remove(j) #remove from retry list after receiving data
			

	else: #breaks up data into peices for transmitting, necesary for MPI transmissions
		#recursive function, should only call itself (z_pieces) times in total
		data = [ np.matrix(np.zeros((data_size,1))) ] * size #deals with none assignment
		z_pieces = int(np.ceil(data_size/100))
		working_nodes = c.Get_neighbors(rank)
		for piece in xrange(0,z_pieces): #sends out data for each peice
			data_fragment = z[piece*100:(piece+1)*100]
			node_fragments = transmitData(data_fragment,comm_worldObject,graphObject,
				node_names,transmissionTag,timeOut) #recursion with fragment
			for j in working_nodes: #only checks 'working' nodes
				if node_fragments[j] is None: #if one transmission from a node is messed up
					working_nodes.remove(j)   #remove it from the working nodes list
					data[j] = None 			  #'drop' the data whole
				else: #otherwise just add the node's data fragment
					data[j][piece*100:(piece+1)*100] = node_fragments[j]

	data[rank] = z #its own data
	return data


def correctiveConsensus(z,tc,weights,comm_worldObject,graphObject,node_names,
						transmissionTag,CorrectiveSpacing,timeOut):
	#Detailed in the paper- the proof presented in the paper is somewhat simple
	#Figure it out, because this code is definitely not simple
	datadim = z.shape[0]
	rank = comm_worldObject.Get_rank()
	size = comm_worldObject.Get_size()
	q,qnew = (z),(z)
	phi = np.matrix(np.zeros((datadim,size)))
	CorrCount = 1

	for consensusIteration in xrange(0,tc):

		#Regular Iteration 
		if (consensusIteration != CorrCount*(CorrectiveSpacing+1)-1): 
		    #set q(t) = q(t-1), remember qnew is from last iteration
			q = qnew 
			#transfer data
			data = transmitData(qnew,comm_worldObject,graphObject,node_names,
				transmissionTag,timeOut)
			#Consensus
			tempsum = 0 #used for tracking 'mass' transmitted
			for j in graphObject.Get_neighbors(rank):
				if (data[j] is not None): #if data was received, then...
					difference = data[j]-q 
					tempsum += weights[j]*(difference) #'mass' added to itself
					phi[:,j] += np.reshape((weights[j]*(difference)),(datadim,1))
			#update local data
			qnew = q + tempsum #essentially doing consensus the long way
			#Corrective Iteration
		else:
			Delta = np.matrix(np.zeros((datadim,size)))
			v = (np.zeros(size))
			#Mass distribution difference is transmitted
			phidata = transmitData(phi[:,j],comm_worldObject,graphObject,node_names,
				transmissionTag,timeOut)
			#Mass distribution should be equivalent sent and received
			for j in graphObject.Get_neighbors(rank):
				if (phidata[j] != None): #if 'mass disr.' transmision was succesful
					Delta[:,j] = phi[:,j] + phidata[j]
					v[j] = 1
			#ensures stability if packet loss during corrective transmission
			phi[:,j] += (-0.5)*Delta[:,j]*v[j]
			qnew += -(0.5)*np.reshape(np.sum(Delta,1),(datadim,1))

			CorrCount += 1

	return qnew  #q(t) after processing

def powerMethod(M,tc,tp,weights,comm_worldObject,graphObject,node_names,
						transmissionTag,CorrectiveSpacing,timeOut):
    #Calls on a Consensus method to figure out top eigenvector
    datadim = M.shape[0]
    rank = comm_worldObject.Get_rank()
    size = comm_worldObject.Get_size()
    q = np.matrix(np.ones((datadim,1)))
    qnew = q
    phi = np.matrix(np.zeros((datadim,size)))
    CorrCount = 1

    for powerIteration in range(0,tp,1):
        qnew = (M*qnew) #We use corrective consensus here, regular consensus works too
        qnew = correctiveConsensus(qnew,tc,weights,comm_worldObject,graphObject,node_names,
						transmissionTag,CorrectiveSpacing,timeOut)
        if LA.norm(qnew) != 0:
        	qnew /= LA.norm(qnew) #normalize

    return qnew.reshape(datadim) #returns eigenvector in 1d
    
