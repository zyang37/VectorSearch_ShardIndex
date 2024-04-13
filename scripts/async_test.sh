#!/bin/bash

# define variables for the script
NUM_QUERIES=10000
K=10
NPROBE=10
MAX_INDEX_STORE=1000
MIXTURES_RATIO=0.

python query_shard_idx.py -nq $NUM_QUERIES -k $K --nprobe $NPROBE \
    --search_topology index_async \
    --max_index_store $MAX_INDEX_STORE \
    --mixtures_ratio $MIXTURES_RATIO \
    --log logs/st_index_async_1_batch.log \
    --seed 0

sleep 2

python query_shard_idx.py -nq $NUM_QUERIES -k $K --nprobe $NPROBE \
    --search_topology index \
    --max_index_store $MAX_INDEX_STORE \
    --mixtures_ratio $MIXTURES_RATIO \
    --log logs/st_index_1_batch.log \
    --seed 0

sleep 2

python query_shard_idx.py -nq $NUM_QUERIES -k $K --nprobe $NPROBE \
    --search_topology query \
    --max_index_store $MAX_INDEX_STORE \
    --mixtures_ratio $MIXTURES_RATIO \
    --log logs/st_query_1_batch.log \
    --seed 0
