'''
This file contains utility functions for VectorDB.
'''

import faiss
import numpy as np
from utils.logger import Logger

# fix random seed
np.random.seed(0)

def random_floats(size, low=0, high=1):
    return [np.random.uniform(low, high) for _ in range(size)]

def random_normal_vectors(num_embeds, dim, mean=0, std=1):
    data = np.random.normal(mean, std, (num_embeds, dim)).astype('float32')
    return data

def random_queries_mix_distribs(num_queries, dim, mixtures_ratio=1, low=-1, high=1):
    '''
    This function generates random query batch where queries are drawn from a mix of distributions.

    Args:
        - num_queries: number of queries to generate
        - dim: dimensionality of the queries
        - low: lower bound of the uniform distribution (both mean and std)
        - high: upper bound of the uniform distribution (both mean and std)
        - mixtures_ratio [0,1]: 
            - 0 means only one distribution. 
            - 1 means every queries are drawn from different distributions.
            - 0.1 means per 10% of the query_batch are drawn from one distribution. 
    '''
    queries = np.zeros((num_queries, dim))

    # compute the number of queries for each distribution
    if mixtures_ratio == 0: 
        random_mean = random_floats(1, low, high)[0]
        # random_std = random_floats(1, low, high)[0]
        random_std = [0.5]
        return random_normal_vectors(num_queries, dim, random_mean, random_std)
    elif mixtures_ratio == 1:
        for i in range(num_queries):
            random_mean = random_floats(1, low, high)[0]
            # random_std = random_floats(1, low, high)[0]
            random_std = [0.5]
            queries[i] = random_normal_vectors(1, dim, random_mean, random_std)
        return queries
    else:
        # generate random queries per sample_size
        sample_size = int(num_queries * mixtures_ratio)
        for i in range(num_queries):
            if i % sample_size == 0:
                random_mean = random_floats(1, low, high)[0]
                # random_std = random_floats(1, low, high)[0]
                random_std = [0.5]
                # print(random_mean)
            queries[i] = random_normal_vectors(1, dim, random_mean, random_std)
    return queries

def random_embeddings(num_embeds, dim):
    '''
    Note: use random_normal_vectors for more controled random embeddings!

    Create random embeddings
    '''
    data = np.random.random((num_embeds, dim)).astype('float32')
    # data[:, 0] += np.arange(num_embeds) / 1000.
    return data

def random_queries(num_queries, dim):
    '''
    Note: use random_normal_vectors for more controled random embeddings!

    Create random queries
    '''
    queries = np.random.random((num_queries, dim)).astype('float32')
    # queries[:, 0] += np.arange(num_queries) / 1000.
    return queries

def save_index(index, index_path):
    faiss.write_index(index, index_path)

@Logger.log_index_load_time
def load_index(index_path):
    return faiss.read_index(index_path)

@Logger.log_index_search_time
def query_index(index, queries, k):
    D, I = index.search(queries, k)
    return D, I

def query_index_file(index_path, queries, k):
    index = load_index(index_path)
    D, I = query_index(index, queries, k)
    return D, I
