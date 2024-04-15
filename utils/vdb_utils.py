'''
This file contains utility functions for VectorDB.
'''

import faiss
import numpy as np

from utils.logger import Logger


def random_mv_normal_vectors(cluster_size, dim, scale=1):
    # scale=10: range from 0 to 10
    mean = np.random.rand(dim) * scale
    cov = np.eye(dim) * np.random.rand(dim)  # varied diagonal covariance
    cluster_data = np.random.multivariate_normal(mean, cov, cluster_size)
    return cluster_data

def random_floats(size, low=0, high=1, seed=None):
    if seed is not None: np.random.seed(seed)
    return [np.random.uniform(low, high) for _ in range(size)]

def random_normal_vectors(num_embeds, dim, mean=0, std=1, seed=None):
    if seed is not None: np.random.seed(seed)
    data = np.random.normal(mean, std, (num_embeds, dim)).astype('float32')
    return data

def random_queries_mix_distribs(num_queries, dim, mixtures_ratio=1, low=-1, high=1, seed=None):
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
    if seed is not None: np.random.seed(seed)

    queries = np.zeros((num_queries, dim))

    # compute the number of queries for each distribution
    random_std = [0.3]

    if mixtures_ratio == 0: 
        random_mean = random_floats(1, low, high)[0]
        return random_normal_vectors(num_queries, dim, random_mean, random_std).astype('float32')
    elif mixtures_ratio == 1:
        for i in range(num_queries):
            random_mean = random_floats(1, low, high)[0]
            queries[i] = random_normal_vectors(1, dim, random_mean, random_std)
        # queries = np.random.uniform(low=low, high=high, size=(num_queries, dim)).astype('float32')
        return queries
    else:
        # draw some queries from different distributions
        num_query_from_diff_distr = int(num_queries * mixtures_ratio)
        for i in range(num_query_from_diff_distr):
            random_mean = random_floats(1, low, high)[0]
            queries[i] = random_normal_vectors(1, dim, random_mean, random_std)

        # draw the rest of the queries from the same distribution
        random_mean = random_floats(1, low, high)[0]
        for i in range(num_query_from_diff_distr, num_queries):
            queries[i] = random_normal_vectors(1, dim, random_mean, random_std)
        # uniform_queries = np.random.uniform(low=low, high=high, size=(num_query_from_diff_distr, dim)).astype('float32')
        # random_mean = random_floats(1, low, high)[0]
        # normal_queries = random_normal_vectors(num_queries - num_query_from_diff_distr, dim, random_mean, random_std).astype('float32')
        # queries = np.concatenate((uniform_queries, normal_queries), axis=0)
    return queries

def random_embeddings(num_embeds, dim, seed=None):
    '''
    Note: use random_normal_vectors for more controled random embeddings!

    Create random embeddings
    '''
    if seed is not None: np.random.seed(seed)

    data = np.random.random((num_embeds, dim)).astype('float32')
    # data[:, 0] += np.arange(num_embeds) / 1000.
    return data

def random_queries(num_queries, dim, seed=None):
    '''
    Note: use random_normal_vectors for more controled random embeddings!

    Create random queries
    '''
    if seed is not None: np.random.seed(seed)

    queries = np.random.random((num_queries, dim)).astype('float32')
    # queries[:, 0] += np.arange(num_queries) / 1000.
    return queries

def save_index(index, index_path):
    faiss.write_index(index, index_path)

# @Logger.log_index_load_time
# def load_index(index_path):
#     # NOT used now, function integrated in the IndexStore class
#     return faiss.read_index(index_path)

@Logger.log_index_search_time
def query_index(index, queries, k, index_path=None):
    D, I = index.search(queries, k)
    return D, I

def query_index_file(index_path, queries, k, index_store):
    # pass in more arguments to update the ranking
    index = index_store.get_index(index_path, queries.shape)
    D, I = query_index(index, queries, k, index_path)
    return D, I
