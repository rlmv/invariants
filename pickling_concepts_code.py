
# coding: utf-8

# ## Pickling concepts

# In[23]:


import pyphi
import pickle
import os
import string
from pathlib import Path
import pandas as pd
from pandas import DataFrame, Series
from collections import OrderedDict


# In[ ]:


def create_directory(name, vers, state):
# Create/select diretory with network info (name, version, state) to save and identify results
    curr_dir = os.getcwd()
    
    directory = f"{curr_dir}/{name}_{vers}_{state}"
    if not os.path.exists(directory):
        os.mkdir(directory)
    new_dir_dict = {f'curr_dir': curr_dir, 'name': name, 'vers': vers, 'state': state}
    return new_dir_dict


# In[34]:


def concept2pickle(concept):
    # Pickles a concept
    pandas_concept = Series(OrderedDict({
        'mechanism':  concept.subsystem.indices2nodes(concept.mechanism),
        'phi': concept.phi,
        'cause_purview': concept.subsystem.indices2nodes(concept.cause_purview),
        'cause_phi': concept.cause.phi,
        'cause_mip': concept.cause.mip,
        'effect_purview': concept.subsystem.indices2nodes(concept.effect_purview),
        'effect_phi': concept.effect.phi,
        'effect_mip': concept.effect.mip,
    }))
 
    # Eliminates punctuation and white spaces for file name
    concept_name = str(concept.subsystem.indices2nodes(concept.mechanism))
    translator = str.maketrans('', '', string.punctuation)
    file_name_no_punct = concept_name.translate(translator)
    file_name = file_name_no_punct.replace(' ','')
    
    pickled_concept = pandas_concept.to_pickle(f'{new_dir}/{network_name}_{network_version}_{network_state}_{file_name}.file', compression=None)
       
    return pickled_concept


# In[53]:


def pickle_concepts(nodes=None, orders=None, phi_lower_bound=None):
        
    if nodes is None:
        nodes = subsystem.node_indices
        
    if orders is None:
        orders = (1,)
        
    if phi_lower_bound is None:
        phi_lower_bound = -1
    
    excel_path = (f'{new_dir}/{network_name}_{network_version}_{network_state}.xlsx')
    
    if not os.path.exists(excel_path):
        wb = openpyxl.workbook.Workbook()
        wb.save(excel_path)
    
    book = openpyxl.load_workbook(excel_path)
    writer = pd.ExcelWriter(excel_path, engine='openpyxl')
    writer.book = book
    startrow = 1
    
    node_labels = str(subsystem.indices2nodes(nodes))
    translator = str.maketrans('', '', string.punctuation)
    sheet_name_no_punct = node_labels.translate(translator)
    sheet_name = (f"{sheet_name_no_punct.replace(' ','')}_{orders}")
        
    mechanisms = [subset for subset in pyphi.utils.powerset(nodes) 
              if len(subset) in orders]
    
    for mechanism in tqdm_notebook(mechanisms):
        concept = subsystem.concept(mechanism)
        print(mechanism, concept.phi)
        if concept.phi > phi_lower_bound:
            C = concept2pickle(concept)
            concept_label = str(concept.subsystem.indices2nodes(concept.mechanism))
            translator = str.maketrans('', '', string.punctuation)
            concept_name_no_punct = concept_label.translate(translator)
            concept_name = concept_name_no_punct.replace(' ','')
            
            pickled_concept = pd.read_pickle(f"{new_dir}/{network_name}_{network_version}_{network_state}_{concept_name}.file")
            
            with open(f"{new_dir}/{network_name}_{network_version}_{network_state}_{concept_name}.txt", "w") as text_file:
                print(pickled_concept, file=text_file)
               
            writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
            row = DataFrame(concept2row(concept)).transpose()
            row.to_excel(writer, (f'{sheet_name}'), startrow=startrow, index=False, header=None)
            startrow += 1
            writer.save()


# In[58]:


def pickle2concept(mechanism):
    """
    Retrieve a pickled concept as a pandas series.
    The unpickled concept has the properties of a pandas dictionary.
    To retrieve info:
        C.phi
        C.cause_purview
        C.cause_phi
        C.cause_mip
        C.effect_purview
        C.effect_phi
        C.effect_mip
    """
    file = (f'{new_dir}/{network_name}_{network_version}_{network_state}_{mechanism}.file')
    unpickled_concept = pd.read_pickle(file)
    return unpickled_concept


# In[ ]:


'''
# Recover repertoire from pickled concept
C = pickle2concept(filename)
mechanism = pyphi.convert.nodes2indices(C.mechanism)
purview = pyphi.convert.nodes2indices(C.cause_purview)
partition = C.cause_mip
phi, partitioned_repertoire = subsystem.evaluate_partition(Direction.CAUSE, mechanism, purview, partition)
print(phi)
print(partitioned_repertoire)
'''

