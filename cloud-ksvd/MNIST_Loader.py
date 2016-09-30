from mnist import MNIST
import numpy as np
import pickle, os
import Image

def resize(images,resolution):
    atoms = np.shape(images)[0]
    original_res = (int(np.sqrt(np.shape(images)[1])),int(np.sqrt(np.shape(images)[1])))
    image_length = resolution[0]*resolution[1]
    resized = np.array(np.zeros((image_length,atoms)))

    for k in xrange(0,atoms):
        temp = (images[k].astype('uint8')).reshape(original_res)
        imtemp = Image.fromarray(temp)
        imtemp.thumbnail(resolution,Image.ANTIALIAS)
        temp = np.array(imtemp).astype('int').reshape((image_length))
        resized[0:(image_length),k] = temp.reshape((image_length))

    return resized


def organize(samples,labels,classes,amount):
    count = np.zeros(len(classes))   #keeps track of amount of samples per class
    atoms = np.shape(samples)[1]                    #number of samples
    dimension = np.shape(samples)[0]                #dimension
    filtered_samples = np.array(np.zeros((dimension,len(classes)*amount)))      
    filtered_labels  = np.array(np.zeros((len(classes)*amount)))       #empty arrays to fill

    for k in np.random.permutation(atoms): #randomly select atoms

        label_selected = labels[k] == np.array(classes)

        if np.all(count==amount): #if we have the required samples for each class
            break
        elif np.any(label_selected) and count[label_selected] < amount: #if we require another sample
            filtered_samples[:,int(sum(count))] = samples[:,k].reshape(dimension)  #add the sample
            filtered_labels[int(sum(count))]  = labels[k].reshape(1)               #add the label
            count += np.array(label_selected,dtype=int) #add it to the count of samples collected

    organized_samples = filtered_samples[:,filtered_labels.argsort()]
    organized_labels  = np.sort(filtered_labels)
    return np.matrix(organized_samples),organized_labels


def importMNIST(folder,resolution,classes,amount,signals):
    print 'importing MNIST data...'
    if os.path.isfile('saved_DY.pkl'):
        print 'found file'
        f = open('saved_DY.pkl','r')
        D = pickle.load(f)
        D_labels = pickle.load(f)
        Y = pickle.load(f)
        Y_labels = pickle.load(f)

        return np.matrix(D),D_labels,np.matrix(Y),Y_labels

    mndata = MNIST(folder)
    train_ims,train_labels = mndata.load_training()
    print 'training loaded'
    test_ims,test_labels = mndata.load_testing()
    print 'testing loaded'

    training_samples = resize(np.array(train_ims),resolution)
    training_labels = np.array(train_labels)
    D,D_labels = organize(training_samples,training_labels,classes,amount)
    print 'dictionary, D, made'

    random_idx = np.array(np.random.permutation(10000))[0:signals] #10000 is total signals avail

    Y = (resize(np.array(test_ims),resolution))[:,random_idx]
    Y_labels = np.array(test_labels)[random_idx]
    print 'signals, Y, made'

    saveToFile(D,D_labels,Y,Y_labels)

    return np.matrix(D),D_labels,np.matrix(Y),Y_labels

def showImage(images,k,resolution):
    temp = (images[0:(resolution[1]*resolution[0]),k].astype('uint8'))
    imtemp = Image.fromarray(temp.reshape((resolution[0],resolution[1])))
    imtemp.show()

def saveToFile(D,D_labels,Y,Y_labels):
    f = open('saved_DY.pkl', 'w')
    pickle.dump(D,f)
    pickle.dump(D_labels,f)
    pickle.dump(Y,f)
    pickle.dump(Y_labels,f)
    f.close()

#from MNIST_Loader import *
#importMNIST('python-mnist/data',(28,28),[1,2,3],3,4)
