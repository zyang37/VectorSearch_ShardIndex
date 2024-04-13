'''
The dispatcher module 
    - Process a batch of queries
    - search knn centroids and return the search topology
'''

import logging

from utils.vdb_utils import query_index_file
from utils.search_by_topology import query_to_index_stopology

class Dispatcher:
    '''
    Dispatcher re-batch queries in a "intelligent" way, then search knn centroids and return a search topology
    '''
    def __init__(self, centriod_idx_paths, queries, nprobe, index_store, verbose=True):
        self.centriod_idx_paths = centriod_idx_paths
        self.queries = queries
        self.nprobe = nprobe
        self.index_store = index_store
        self.verbose = verbose

        self.search_knn_centroids()

    def batch_by_distruibution(self):
        pass

    def search_knn_centroids(self):
        self.D, self.I = query_index_file(self.centriod_idx_paths, self.queries, self.nprobe, self.index_store)
        if self.verbose:
            print("Top-k centroids")
            print(self.I)
            print()

    def create_search_outterloop_query_topology(self):
        stopology = {}
        for i in range(len(self.queries)):
            stopology[i] = list(self.I[i])
        return stopology
    
    def create_search_outterloop_index_topology(self):
        # stopology = self.create_search_outterloop_query_topology()
        # return query_to_index_stopology(stopology)
        # self.I is a 2D array of shape (num_queries, k)
        # {idx1: [q1, q2, ..], idx2: [q3, q4, ...]}
        stopology = {}
        for q_idx, idxs in enumerate(self.I):
            for idx in idxs:
                if idx in stopology:
                    stopology[idx].append(q_idx)
                else:
                    stopology[idx] = [q_idx]
        return stopology
    