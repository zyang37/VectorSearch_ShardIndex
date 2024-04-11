#!/bin/bash

python query_shard_idx.py -nq 10000 -k 10 --nprobe 10 --search_topology index \
    --max_index_store 100 \
    --mixtures_ratio 0 \
    --log logs/st_index_1_batch.log \
    --seed 0


python query_shard_idx.py -nq 10000 -k 10 --nprobe 10 --search_topology query \
    --max_index_store 100 \
    --mixtures_ratio 0 \
    --log logs/st_query_1_batch.log \
    --seed 0
