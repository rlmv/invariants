
# coding: utf-8

# In[27]:


import pyphi
import numpy as np
from utils import Experiment

# In[28]:


pyphi.config.MEASURE = 'BLD'


# In[3]:


# Weights matrix

ic = 0.95 # input connection
ei = 1 # external input
nc = -2 # inhibition
bc = 0.05 # backward connection
gc = 0.02 # grid lateral connection
sg = 1 # grid self-connection
sc = 0.01 # default self-connection
isc = 0.1 # invariant self-connection
all_weights = np.array([
                        [sg, gc, 0, 0, 0, 0, 0, 0, gc, 0, 0, 0, 0, 0, 0, bc, 0, 0, 0, 0, ei, 0, 0, 0, 0, 0, 0, 0], # A
                        [gc, sg, gc, 0, 0, 0, 0, 0, gc, gc, 0, 0, 0, 0, 0, bc, 0, 0, 0, 0, 0, ei, 0, 0, 0, 0, 0, 0], # B
                        [0, gc, sg, gc, 0, 0, 0, 0, 0, gc, gc, 0, 0, 0, 0, 0, bc, 0, 0, 0, 0, 0, ei, 0, 0, 0, 0, 0], # C
                        [0, 0, gc, sg, gc, 0, 0, 0, 0, 0, gc, gc, 0, 0, 0, 0, bc, 0, 0, 0, 0, 0, 0, ei, 0, 0, 0, 0], # D
                        [0, 0, 0, gc, sg, gc, 0, 0, 0, 0, 0, gc, gc, 0, 0, 0, 0, bc, 0, 0, 0, 0, 0, 0, ei, 0, 0, 0], # E
                        [0, 0, 0, 0, gc, sg, gc, 0, 0, 0, 0, 0, gc, gc, 0, 0, 0, bc, 0, 0, 0, 0, 0, 0, 0, ei, 0, 0], # F
                        [0, 0, 0, 0, 0, gc, sg, gc, 0, 0, 0, 0, 0, gc, gc, 0, 0, 0, bc, 0, 0, 0, 0, 0, 0, 0, ei, 0], # G
                        [0, 0, 0, 0, 0, 0, gc, sg, 0, 0, 0, 0, 0, 0, gc, 0, 0, 0, bc, 0, 0, 0, 0, 0, 0, 0, 0, ei], # H
                        [gc, gc, 0, 0, 0, 0, 0, 0, sg, gc, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ei, ei, 0, 0, 0, 0, 0, 0], # I
                        [0, gc, gc, 0, 0, 0, 0, 0, gc, sg, gc, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ei, ei, 0, 0, 0, 0, 0], # J
                        [0, 0, gc, gc, 0, 0, 0, 0, 0, gc, sg, gc, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ei, ei, 0, 0, 0, 0], # K
                        [0, 0, 0, gc, gc, 0, 0, 0, 0, 0, gc, sg, gc, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ei, ei, 0, 0, 0], # L
                        [0, 0, 0, 0, gc, gc, 0, 0, 0, 0, 0, gc, sg, gc, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ei, ei, 0, 0], # M
                        [0, 0, 0, 0, 0, gc, gc, 0, 0, 0, 0, 0, gc, sg, gc, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ei, ei, 0], # N
                        [0, 0, 0, 0, 0, 0, gc, gc, 0, 0, 0, 0, 0, gc, sg, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ei, ei], # O
                        [ic, ic, 0, 0, 0, 0, 0, 0, nc, nc, 0, 0, 0, 0, 0, sc, 0, 0, 0, bc, 0, 0, 0, 0, 0, 0, 0, 0], # P
                        [0, 0, ic, ic, 0, 0, 0, 0, 0, nc, nc, nc, 0, 0, 0, 0, sc, 0, 0, bc, 0, 0, 0, 0, 0, 0, 0, 0], # Q
                        [0, 0, 0, 0, ic, ic, 0, 0, 0, 0, 0, nc, nc, nc, 0, 0, 0, sc, 0, bc, 0, 0, 0, 0, 0, 0, 0, 0], # R
                        [0, 0, 0, 0, 0, 0, ic, ic, 0, 0, 0, 0, 0, nc, nc, 0, 0, 0, sc, bc, 0, 0, 0, 0, 0, 0, 0, 0], # S
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ic, ic, ic ,ic, isc, 0, 0, 0, 0, 0, 0, 0, 0], # T
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 , 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # a
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 , 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # b
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 , 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # c
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 , 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # d
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 , 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # e
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 , 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # f
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 , 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # g
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 , 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # h
                    ])  #A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R,  S, T, a, b, c, d, e, f, g, h

weights = []
for x in range(0,20):
    weights.append(all_weights[x][range(0,20)])
weights = np.array(weights)
# Gate function: nodes have threshold >= 1
                      #A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, a, b, c, d, e, f, g, h
thresholds = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,.9,.9,.9,.9,.9])
nN = len(thresholds)


# In[23]:


# Create the tpm
pset = pyphi.utils.powerset(np.arange(nN))

tpm = np.zeros([2**nN,nN])
#indslist = [[] for x in range(0,len(pset))]
for inds in pset:
    istate = np.zeros(nN)
    for y in range(0,len(inds)):
        istate[inds[y]] = 1
    inpt = istate
    sw = np.zeros(nN,dtype='f')
    swN = np.zeros(nN)
    for z in range(0,nN):
        sw[z] = sum(inpt*weights[z])
        
        swN[z] = .001 + .99*(sw[z]>=thresholds[z])


    #print(inpt,'\n',sw,'\n',swN, '\n''------''\n')
    V = 0;
    for v in range(0,nN):
        V = V + istate[v]*2**v
    tpm[int(V)] = tuple(swN)

# Create the connectivity matrix
cm = np.abs(np.where(weights != 0, 1, 0))

# Transpose our (receiving, sending) CM to use the PyPhi convention of (sending, recieving)
cm = np.transpose(cm)

# Create the network
subsystem_labels = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T')
network = pyphi.Network(tpm, cm, subsystem_labels)


# In[5]:


# Set state and create subsystem
        #A  B  C  D  E  F  G  H  I  J  K  L  M  N  O  P  Q  R  S  T#
state = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
subsystem = pyphi.Subsystem(network, state, range(network.size))
A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T = subsystem.node_indices

pyphi.config.REPR_VERBOSITY = 1


experiment = Experiment('largepyr', '2.1', network, state)
experiment.initialize()

