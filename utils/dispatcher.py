'''
The dispatcher module 
    - Process a batch of queries
    - search knn centroids and return the search topology
'''

import logging

from utils.vdb_utils import query_index_file
from utils.search_by_topology import reverse_stopology

class Dispatcher:
    '''
    Dispatcher re-batch queries in a "intelligent" way, then search knn centroids and return a search topology
    '''
    def __init__(self, centriod_idx_paths, queries, nprobe, verbose=True):
        self.centriod_idx_paths = centriod_idx_paths
        self.queries = queries
        self.nprobe = nprobe
        self.verbose = verbose

        self.search_knn_centroids()

    def batch_by_distruibution(self):
        pass

    def search_knn_centroids(self):
        self.D, self.I = query_index_file(self.centriod_idx_paths, self.queries, self.nprobe)
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
        stopology = self.create_search_outterloop_query_topology()
        return reverse_stopology(stopology)
    