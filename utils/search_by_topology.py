'''
This module contains functions to search a batch of queries or index shards by a given search topology.

Search topology 1: {query_idx1: [idx1, idx2...]} # naive search, can serve as a ground truth and baseline
Search topology 2: {idx1: [query_idx1, query_idx2...]} # intellegent batching
'''

import numpy as np
from utils.vdb_utils import query_index_file

# fix random seed
np.random.seed(0)

def reverse_stopology(stopology):
    '''
    This function reverse the stopology dict.
    '''
    reverse_dict = {}
    for key, val_list in stopology.items():
        for val in val_list:
            if val not in reverse_dict:
                reverse_dict[val] = [key]
            else:
                reverse_dict[val].append(key)
    return reverse_dict

def search_outterloop_query(stopology, queries, idx_k, k, idx_paths):
    '''
    Search a batch of queries: looping over queries 

    args:
        - search topology: {qidx1: [idx1,...]}
        - query: (num, dim)
        - idx_k: k for each index search
        - k: top k results (global)
        - idx_paths: list of index paths
    '''
    # result_matrix: init ndarray with shape (num_queries, k)
    final_D_matrix = np.zeros((queries.shape[0], k))
    final_I_matrix = np.zeros((queries.shape[0], k))
    final_file_idx_matrix = np.zeros((queries.shape[0], k))

    # loop over queries
    for q_idx, idxs in stopology.items():
        # select query make shape (1, dim)
        query = queries[q_idx].reshape(1, -1)
        D_concat = np.array([])
        I_concat = np.array([])
        file_idx_concat = np.array([])

        # loop over idxs for each query
        for j, file_idx in enumerate(idxs):
            D, I = query_index_file(idx_paths[file_idx], query, idx_k)
            # make file_idx_matrix
            file_idx_m = np.ones_like(D) * file_idx
            D_concat = np.concatenate((D_concat, D), axis=1) if D_concat.size else D
            I_concat = np.concatenate((I_concat, I), axis=1) if I_concat.size else I
            file_idx_concat = np.concatenate((file_idx_concat, file_idx_m), axis=1) if file_idx_concat.size else file_idx_m

        # Sort Overwrite D_concat, I_concat, and file_idx_concat. 
        sort_idx = np.argsort(D_concat, axis=1)
        D_concat = np.take_along_axis(D_concat, sort_idx, axis=1)
        I_concat = np.take_along_axis(I_concat, sort_idx, axis=1)
        file_idx_concat = np.take_along_axis(file_idx_concat, sort_idx, axis=1)
        
        # update final matrix with top k
        final_D_matrix[q_idx] = D_concat[:, :k]
        final_I_matrix[q_idx] = I_concat[:, :k]
        final_file_idx_matrix[q_idx] = file_idx_concat[:, :k]
    return final_D_matrix, final_I_matrix.astype(int), final_file_idx_matrix.astype(int)
    

def batch_queries_by_stopology(stopology, queries):
    '''
    This function take in a outterloop index topology and a global query batch. 
    Return a list of batched queries for each index search.

    args:
        - search topology: {index1: [q1,q2...]}
        - query: (num, dim)

    return:
        - [query_batch1, query_batch2...]
            - query_batch: (num_queries, dim)
    '''
    query_batch_dict = {}
    for idx, q_idxs in stopology.items():
        query_batch = queries[q_idxs]
        query_batch_dict[idx] = query_batch
    return query_batch_dict

def search_outterloop_index(stopology, queries, idx_k, k, idx_paths):
    '''
    Search a batch of index: looping over index shards

    args:
        - search topology: {index1: [q1,q2...]}
        - queries: (num, dim)
        - idx_k: k for each index search
        - k: top k results (global)
        - idx_paths: list of index paths
    '''
    # result_matrix: init ndarray with shape (num_queries, k)
    final_D_matrix = np.ones((queries.shape[0], k)) * np.inf
    final_I_matrix = np.zeros((queries.shape[0], k))
    final_file_idx_matrix = np.zeros((queries.shape[0], k))

    # batch queries by stopology: {idx1, [q1_data, q2_data...]}
    stopology_queries_dict = batch_queries_by_stopology(stopology, queries)

    # loop over index shards
    for file_idx, q_idxs in stopology.items():
        # loop over q_idxs for each index
        query_batch = stopology_queries_dict[file_idx]
        # query_batch_order = q_idxs
        D, I = query_index_file(idx_paths[file_idx], query_batch, idx_k)
        file_idx_m = np.ones_like(D) * file_idx
        
        # merge and compare results in final matrix (D), then save top k
        prev_D = final_D_matrix[q_idxs]
        prev_I = final_I_matrix[q_idxs]
        prev_file_idx = final_file_idx_matrix[q_idxs]
        # merge and sort
        D_concat = np.concatenate((prev_D, D), axis=1)
        I_concat = np.concatenate((prev_I, I), axis=1)
        file_idx_concat = np.concatenate((prev_file_idx, file_idx_m), axis=1)
        # sort
        sort_idx = np.argsort(D_concat, axis=1)
        D_concat = np.take_along_axis(D_concat, sort_idx, axis=1)
        I_concat = np.take_along_axis(I_concat, sort_idx, axis=1)
        file_idx_concat = np.take_along_axis(file_idx_concat, sort_idx, axis=1)
        # update final matrix with top k
        final_D_matrix[q_idxs] = D_concat[:, :k]
        final_I_matrix[q_idxs] = I_concat[:, :k]
        final_file_idx_matrix[q_idxs] = file_idx_concat[:, :k]
    return final_D_matrix, final_I_matrix.astype(int), final_file_idx_matrix.astype(int)