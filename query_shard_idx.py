'''
Generate random queries and query shard index files
'''

import os
import time
import faiss
# import asyncio
import logging
import argparse
import multiprocessing

import numpy as np
from pprint import pprint

from utils.index_store import IndexStore, ThreadDataLoader, ProcessDataLoader
from utils.dispatcher import Dispatcher
from utils.index_manager import IndexManager
from utils.vdb_utils import random_floats, random_normal_vectors, query_index_file, random_queries_mix_distribs
from utils.search_by_topology import search_outterloop_index, search_outterloop_query, search_outterloop_index_async, query_to_index_stopology


faiss.omp_set_num_threads(3)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query shard index for vector database")
    parser.add_argument("-idx", "--idx_root", required=False, default="shards/idxs/", help="dir to index files", type=str,)
    parser.add_argument("-np", "--nprobe", default=10, help="a small number (nprobe) of subsets to visit", type=int,)
    parser.add_argument("-k", default=3, help="top k results", type=int,)
    parser.add_argument("-nq", "--num_query", default=5, help="number of queries", type=int,)
    parser.add_argument("-mr", "--mixtures_ratio", default=0., help="mixtures ratio for random queries", type=float,)
    parser.add_argument("--log", required=False, default="logs/app.log", help="log file", type=str,)
    parser.add_argument("-mi", "--max_index_store", default=1000, help="max indexes to store", type=int,)
    parser.add_argument("-st", "--search_topology", default="index", 
                        help="search topology: <index>, <query> or <index_async>", type=str,)
    # hardcode args for now
    parser.add_argument("-d", "--dim", default=128, help="dimension of embeddings", type=int,)
    parser.add_argument("--seed", default=None, help="random seed", type=int,)
    parser.add_argument("--verbose", action="store_true", help="increase output verbosity")
    args = parser.parse_args()

    os.makedirs("logs", exist_ok=True)
    # Note it will keep appending to the log file if file exists!
    # logging.basicConfig(filename='logs/app.log', level=logging.INFO, format='%(asctime)s.%(msecs)03d,%(levelname)s,%(message)s')
    time_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(filename=args.log, level=logging.INFO, format="%(asctime)s.%(msecs)03d,%(message)s", datefmt=time_format)

    # headers: timestamp,action,latency,args
    if args.verbose:
        print(args)
    index_root = args.idx_root
    nprobe = args.nprobe
    k = args.k
    dim = args.dim
    num_queries = args.num_query
    mixtures_ratio = args.mixtures_ratio
    max_index_store = args.max_index_store
    search_topology = args.search_topology
    seed = args.seed

    if seed is not None:
        np.random.seed(seed)

    # logging.info(f"Index root: {index_root}")
    # logging.info(f"nprobe: {nprobe}")
    # logging.info(f"k: {k}")
    # logging.info(f"dim: {dim}")
    # logging.info(f"num_queries: {num_queries}")
    # logging.info(f"mixtures_ratio: {mixtures_ratio}")

    # idx_k: k for each index search
    # idx_k = (k // nprobe) + k
    idx_k = k
    
    # idx_paths = [os.path.join(index_root, f) for f in os.listdir(index_root)]
    idx_paths = []
    centriod_idx_paths = ""
    for f in os.listdir(index_root):
        if "centroid" in f:
            centriod_idx_paths = os.path.join(index_root, f)
        else:
            idx_paths.append(os.path.join(index_root, f))    

    # Generate random queries from normal distribution with mean 0 and std 1
    # random_mean = random_floats(1, low=-1, high=1)
    # random_std = [0.5]
    # queries = random_normal_vectors(num_queries, dim, random_mean[0], random_std[0], seed=seed)
    queries = random_queries_mix_distribs(num_queries, dim, mixtures_ratio=mixtures_ratio, low=-1, high=1, seed=seed)

    index_manager = IndexManager()
    index_store = IndexStore(max_indexes=max_index_store, index_manager=index_manager)
    dispatcher = Dispatcher(centriod_idx_paths, queries, nprobe, index_store, verbose=args.verbose)

    # inference
    start_time = time.perf_counter()
    
    if "query" == search_topology.lower():
        stopology = dispatcher.create_search_outterloop_query_topology()
        D_matrix, I_matrix, file_idx_matrix = search_outterloop_query(stopology, queries, idx_k, k, idx_paths, index_store)
    elif "index" == search_topology.lower():
        # rstopology = query_to_index_stopology(stopology)
        rstopology = dispatcher.create_search_outterloop_index_topology()
        D_matrix, I_matrix, file_idx_matrix = search_outterloop_index(rstopology, queries, idx_k, k, idx_paths, index_store)
    elif "index_async" == search_topology.lower():
        rstopology = dispatcher.create_search_outterloop_index_topology()
        # sort rs topology by length of values
        rstopology = {k: v for k, v in sorted(rstopology.items(), key=lambda item: len(item[1]), reverse=True)}
        index_loader = ThreadDataLoader(index_store, idx_paths, rstopology)
        index_loader.start()
        D_matrix, I_matrix, file_idx_matrix = search_outterloop_index_async(rstopology, queries, idx_k, k, idx_paths, index_store)
        index_loader.stop_loading()
    else:
        raise ValueError("Invalid search topology")

    end_time = time.perf_counter()
    qb_runtime = end_time - start_time

    if "index_async" == search_topology.lower():
        index_loader.join()

    if args.verbose:
        print()
        print("Distances")
        print(D_matrix)
        print()
        print("Index")
        print(I_matrix)
        print()
        print("Index file")
        print(file_idx_matrix)

    print(f"Search time: {qb_runtime:.8f}s")
    
    # Sort index ranking dict: "index_manager.ranking_dict"
    # pprint(sorted(index_manager.ranking_dict.items(), key=lambda x: x[1], reverse=True))
