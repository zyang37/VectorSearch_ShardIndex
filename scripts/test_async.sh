#!/bin/bash

python query_shard_idx.py -nq 1000 -k 100 --nprobe 10 --search_topology index \
    --max_index_store 1 \
    --mixtures_ratio 1. \
    --seed 0

sleep 3

python query_shard_idx.py -nq 1000 -k 100 --nprobe 10 --search_topology index_async \
    --max_index_store 1 \
    --mixtures_ratio 1. \
    --seed 0
