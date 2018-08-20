
# coding: utf-8

# In[24]:


import pyphi
import numpy as np
from tqdm import tqdm_notebook
import plotly.plotly as py
import plotly.graph_objs as go
import scipy.io
import pandas as pd
from pandas import DataFrame, Series
from collections import OrderedDict
import random
from matplotlib import pyplot as plt
from matplotlib import gridspec
import openpyxl
import string
import pickle
import os
from pathlib import Path


# In[2]:


def concept2row(concept):
    """Convert a concept into a Pandas Series."""
    return Series(OrderedDict({
        'mechanism':  concept.subsystem.indices2nodes(concept.mechanism),
        'phi': concept.phi,
        'cause_purview': concept.subsystem.indices2nodes(concept.cause_purview),
        'effect_purview': concept.subsystem.indices2nodes(concept.effect_purview),
        'cause_phi': concept.cause.phi,
        'effect_phi': concept.effect.phi,
    }))


def ces2df(ces):
    """Convert a CES to a Pandas DataFrame."""
    return DataFrame([concept2row(concept) for concept in ces])

def ces_comparison(ces1, ces2):
    """Convert two CESs to a Pandas DataFrame."""
    state1 = ces1[0].subsystem.state
    state2 = ces2[0].subsystem.state
    
    df1 = ces2df(ces1)
    df2 = ces2df(ces2)

    df1 = df1.assign(state=[state1]*len(df1))
    df2 = df2.assign(state=[state2]*len(df2))
    
    df = pd.concat([df1, df2]).sort_index().reset_index(drop=True)
    cols = list(df)
    cols = cols[-1:] + cols[:-1]
    df = df[cols]
    
    return df


# In[ ]:


def M1(inputs):
    return df_output_value if sum(inputs) >= 1 else 0 

def M2(inputs):
    return df_output_value if sum(inputs) >= 2 else 0 

def QXOR(inputs):
    return df_output_value if sum(inputs) == 1 else 0


GATE_FUN = {
    "M1": M1,
    "M2": M2,
    "QXOR": QXOR,
}


# In[4]:


def fill_tpm(gate_type, input_states, modulation_states,
             input_weights=None,
             modulation_weights=None,
             curr_node_state=None):
    """Return the probability of being ON for a gate with weighted input and modulation.
    
    The weighted input is used to obtain a probability of activation (depending on the type
    of gate) which is then modulated.
    
    Args:
        gate_type (str)
        input_states : array containing the state of elements that are actually connected to the logical gate
        modulation_states: array containing the state of the elements connected to the gate that modulate its output
    """
    # Make sure the states are all 0 or 1 and the modulations have the right length
    for states in [input_states, modulation_states]:
        assert states is None or len(states)==0 or all([s in [0, 1] for s in states])
    if input_weights is not None:
        assert len(input_weights) == len(input_states)
    if modulation_weights is not None:
        assert len(modulation_weights) == len(modulation_states)
    
    # Get the deterministic gate output and apply the modulation
    if input_states is None or len(input_states)==0:
        assert curr_node_state is not None
        assert not gate_type
        gate_output = 0
    else:
        assert gate_type in GATE_FUN.keys()
        gate_output = GATE_FUN[gate_type](input_states)
        
    if modulation_states is None or len(modulation_states)==0:
        return gate_output
    return modulate_output(gate_output, modulation_states,
                           modulation_weights=modulation_weights)
    
    
def modulate_output(gate_output, modulation_states, modulation_weights=None):
    
    n = len(modulation_states)

    if modulation_weights is None:
        modulation_weights = 0 
    modulation_values = [v * w for (v, w) in zip(modulation_states, modulation_weights)]
    return max(0, min(1, gate_output + np.sum(modulation_values))) # Bound modulated output by 0 and 1


# In[5]:


def find_le_index_by_label(on_nodes):
    """Return the le index of the state where nodes in on_nodes are on
    
    Args:
        on_nodes (list): a list of strings of nodes that are on in that state
    """
    temp = [0] * n_nodes
    for node in on_nodes:
        i = node_labels.index(node)
        temp[i] = 1
    return pyphi.convert.s2l(tuple(temp))

def find_label_by_le_index(index):
    """Return a list of nodes that are on in the input state
    
    Args:
        index (int)
    """
    on = []
    state = pyphi.convert.le_index2state(index, n_nodes)
    for n in range(len(state)):
        if state[n]==1:
            on.append(node_labels[n])
    return on


# In[6]:


def evolution(test_index, time=30, fix=True, label=True):
    """Return a list of following states starting with test_index for t times
    
    Args:
        test_index (int): the index of state to begin evolution with
        time (int): number of repetitions (length of time)
        fix (bool): fix test states to on at every time step
        label (bool): show label instead of state
    """
    curr_index = test_index
    curr_state = np.array(pyphi.convert.le_index2state(test_index, n_nodes))
    fixed_on = np.where(curr_state == 1)[0] # nodes that are on in the initial test state

    result = []   
    for t in range(time):
        next_state = []
        for i in range(n_nodes):
            curr_node_state = curr_state[i]
            inputs = input_indices[i]
            input_states = [curr_state[s] for s in inputs]
            input_weights = all_weights[i][inputs]
            mods = modulation_indices[i]
            mod_states = [curr_state[s] for s in mods]
            mod_weights = all_weights[i][mods]
            r = random.uniform(0, 1.0)
            prob = fill_tpm(gate_types[i], input_states, mod_states,
                               input_weights = input_weights,
                               modulation_weights = mod_weights,
                               curr_node_state=curr_node_state) * 0.99 + 0.001
            next_state.append(1) if prob >= r else next_state.append(0)
        if fix == True: # fix nodes to stay ON
            for f in fixed_on:
                next_state[f] = 1
        next_index = pyphi.convert.s2l(tuple(next_state))
        if label == True:
            result.append(find_label_by_le_index(next_index))
        else:
            result.append(next_state)
        curr_state = next_state
        curr_index = next_index
    return result


# In[7]:


def behavior(test_index, time=30, iteration=50, fix=True):
    d = pd.DataFrame(evolution(test_index, time=time, fix=fix, label=False), columns=node_labels)
    for i in range(iteration):
        d = d.add(pd.DataFrame(evolution(test_index, time=time, fix=fix, label=False), columns=node_labels))
    return d


# In[8]:


def find_blanket(node):
    parents = input_indices[node] + modulation_indices[node]
    children = []
    parents_of_children = []
    for n in range(n_nodes):
        if all_weights[n, node] != 0:
            children.append(n)
    for c in children:
        parents_of_children = parents_of_children + input_indices[c] + modulation_indices[c]
    return list(set(parents + children + parents_of_children))

def find_markov_blankets(relevant_nodes):
    markov_blankets = {}
    for node in relevant_nodes:
        markov_blankets[node] = find_blanket(node)
    return markov_blankets


# In[1]:


def built_tpm_for_subsys(relevant_nodes, markov_blankets):
    
    """Return a multidimensional state-by-node TPM of a subsystem, conditioning external nodes to OFF
    
    Args:
        relevant_nodes (list): nodes in the subsystem
        markov_blankets (dict): node index as key and list of nodes in the blanket as value
    """
    size = len(relevant_nodes)
    tpm = []
    for i in range(size):
        node = relevant_nodes[i]
        blanket = markov_blankets[node]
        external = [n for n in blanket if n not in relevant_nodes]
        external_indices = [n for n in range(len(blanket)) if blanket[n] not in relevant_nodes]

        shape = tuple([2 if relevant_nodes[x] in blanket else 1 for x in range(size)] + [1])
        node_tpm = np.ndarray(shape=shape)

        for s in range(2**len(blanket)): # row
            blanket_state = np.array(pyphi.convert.le_index2state(s, len(blanket))) # the state of each node in the blanket
            # conditioning external nodes to OFF
            for e in external_indices:
                if blanket_state[e]==1:
                    pass
            # calculate probability for the node in each state
            inputs = input_indices[node]
            input_states = [blanket_state[blanket.index(ipt)] for ipt in inputs]
            input_weights = all_weights[node][inputs]
            mods = modulation_indices[node]
            mod_states = [blanket_state[blanket.index(mod)] for mod in mods]
            mod_weights = all_weights[node][mods]
            prob = fill_tpm(gate_types[node], input_states, mod_states,
                               input_weights = input_weights,
                               modulation_weights = mod_weights,
                               curr_node_state=blanket_state[blanket.index(node)]) * 0.98 + 0.01
           # fill the node_tpm
            location = tuple([1 if (n in blanket) and blanket_state[blanket.index(n)]==1 else 0 for n in relevant_nodes] + [0])
            node_tpm[location] = prob
        # expand tpm
        node_tpm = pyphi.tpm.expand_tpm(node_tpm)
        tpm.append(node_tpm)
    tpm = np.concatenate(tpm, axis=-1)
    return tpm

