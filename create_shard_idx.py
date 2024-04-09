'''
Currently randomly generate embeddings and create indexes. 

Generate shard index for the given dataset, if dataset not provided, generate random embeddings
'''

import os
import time
import faiss
import argparse
import numpy as np

from utils.read_write import save_np_to_file, load_npy
from utils.vdb_utils import random_normal_vectors, save_index, random_floats

# fix random seed
np.random.seed(0)

def create_ivf_index(npy_path):
    # load npy file
    data = load_npy(npy_path)
    nlist = 100
    # print(data.shape)
    d = data.shape[1]
    quantizer = faiss.IndexFlatL2(d)  # the other index
    index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_L2)
    assert not index.is_trained
    index.train(data)
    assert index.is_trained
    # save index and embeds
    index.add(data)
    return index

# KNN search
def create_flat_index(npy_path):
    data = load_npy(npy_path)
    dim = data.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(data)
    return index

def compute_embeds_avgs(embeds):
    return np.mean(embeds, axis=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate shard indics")
    parser.add_argument("-np", "--npy_root", required=False, default="shards/npys/", help="dir to npy files", type=str,)
    parser.add_argument("-idx", "--idx_root", required=False, default="shards/idxs/", help="dir to index files", type=str,)
    # args for random generation
    parser.add_argument("-d", "--dim", default=128, help="dimension of embeddings", type=int,)
    parser.add_argument("-ns", "--num_shards", default=100, help="number of shards", type=int,)
    args = parser.parse_args()

    # args for random generation
    dim = args.dim
    num_shards = args.num_shards

    npy_root = args.npy_root
    index_root = args.idx_root
    if not os.path.exists(npy_root):
        os.makedirs(npy_root)
    if not os.path.exists(index_root):
        os.makedirs(index_root)

    # init empty npy arrays
    embeds_centroids = np.zeros((num_shards, dim))
    
    # create npy files
    for i in range(num_shards):
        random_mean = random_floats(1, low=-1, high=1)
        # random_std = random_floats(1)
        # random_mean = [0]
        random_std = [0.5]
        embeds = random_normal_vectors(100000, dim, random_mean[0], random_std[0])
        embeds_centroids[i] = compute_embeds_avgs(embeds)
        save_np_to_file(os.path.join(npy_root, f"embeds_{i}.npy"), embeds)
        print(f"embeds_{i}.npy created")

    # save centroids
    save_np_to_file(os.path.join(npy_root, f"embeds_centroids.npy"), embeds_centroids)

    # create indexes
    for npy_path in os.listdir(npy_root):
        if "centroids" in npy_path: 
            # create flat index for centroids
            index = create_flat_index(os.path.join(npy_root, npy_path))
            save_index(index, os.path.join(index_root, "embeds_centroids.index"))
            print("Centroids index created")
            continue
        
        print(npy_path)
        index_prefix = npy_path.split(".")[0]
        index = create_ivf_index(os.path.join(npy_root, npy_path))
        save_index(index, os.path.join(index_root, f"{index_prefix}.index"))
        print(f"{index_prefix}.index created")
        