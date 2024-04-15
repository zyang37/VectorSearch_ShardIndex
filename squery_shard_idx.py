'''
Serve index_async search topology only

Generate <multiple> random queries batch and query shard index files
'''

import os
import time
import faiss
# import asyncio
import logging
import argparse
import threading

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
    parser.add_argument("-k", default=10, help="top k results", type=int,)
    parser.add_argument("-nq", "--num_query", default=10000, help="number of queries", type=int,)
    parser.add_argument("-mr", "--mixtures_ratios", nargs="+", default=[0.], help="mixtures ratio for random queries (-mr 0.1 0.2 0.3)", type=float,)

    parser.add_argument("--log", required=False, default="logs/app.log", help="log file", type=str,)
    parser.add_argument("-mi", "--max_index_store", default=1000, help="max indexes to store", type=int,)
    parser.add_argument("-d", "--dim", default=128, help="dimension of embeddings", type=int,)
    parser.add_argument("--seed", default=None, help="random seed", type=int,)
    parser.add_argument("--verbose", action="store_true", help="increase output verbosity")
    args = parser.parse_args()
    
    index_root = args.idx_root
    nprobe = args.nprobe
    k = args.k
    dim = args.dim
    num_queries = args.num_query
    mixtures_ratios = args.mixtures_ratios
    max_index_store = args.max_index_store
    search_topology = "index_async"
    seed = args.seed

    if args.verbose:
        print(args)

    if seed is not None:
        np.random.seed(seed)

    os.makedirs("logs", exist_ok=True)
    time_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(filename=args.log, level=logging.INFO, format="%(asctime)s.%(msecs)03d,%(message)s", datefmt=time_format)

    # idx_k: k for each index search
    idx_k = k
    
    # parse shard index files
    idx_paths = []
    centriod_idx_paths = ""
    for f in os.listdir(index_root):
        if "centroid" in f:
            centriod_idx_paths = os.path.join(index_root, f)
        else:
            idx_paths.append(os.path.join(index_root, f))    

    # Generate multiple random queries batch
    query_batches = []
    for mr in mixtures_ratios:
        query_batches.append(random_queries_mix_distribs(num_queries, dim, mixtures_ratio=mr, low=-1, high=1, seed=seed))

    # init index manager and store
    index_manager = IndexManager()
    index_store = IndexStore(max_indexes=max_index_store, index_manager=index_manager)
    dispatcher = Dispatcher(centriod_idx_paths, index_store, verbose=args.verbose)
    index_loader = ThreadDataLoader(index_store, idx_paths)
    index_loader.start()

    index_store.set_index_loader(index_loader)
    
    for i, qb in enumerate(query_batches):
        # start loading hot idx here if ranking exists
        index_loader.resume_loading()

        # print(len(index_store.indexes))
        start_time = time.perf_counter()

        dispatcher.search_knn_centroids(qb, nprobe)
        rstopology = dispatcher.create_search_outterloop_index_topology()
        
        # sort rs topology by length of values
        rstopology = {k: v for k, v in sorted(rstopology.items(), key=lambda item: len(item[1]), reverse=True)}
        
        # need update, want to reorder stopology so that DRAM-idx start first, then sort by batch size
        index_store.clearup(stopology=rstopology)

        # print(len(rstopology))
        index_loader.pause_loading()
        index_loader.update_files_to_load([idx_paths[idx] for idx in rstopology.keys()])
        index_loader.resume_loading()
        
        D_matrix, I_matrix, file_idx_matrix = search_outterloop_index_async(rstopology, qb, idx_k, k, idx_paths, index_store)
        
        index_loader.pause_loading()
        hot_idxs = index_manager.get_head_index(k=max_index_store)
        index_loader.update_files_to_load(hot_idxs)

        end_time = time.perf_counter()
        qb_runtime = end_time - start_time
        print(f"Search time: {qb_runtime:.8f}s")

        time.sleep(0.01)
        
        # if reached the last query batch, stop the loader
        if i == len(query_batches) - 1:
            index_loader.stop_loading()
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
