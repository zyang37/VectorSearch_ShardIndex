#!/bin/bash

NUM_QUERIES=10000
MEM_BUDGET=300

rm logs/app.log

python squery_shard_idx.py -mr 0. 0. 0.001 0.002 0.003 0.01 0.1 0.001 0.002 0. 0. 0. -mi $MEM_BUDGET \
                        --nprobe 10 \
                        -nq $NUM_QUERIES \
                        --ranking_policy LRU \
                


python squery_shard_idx.py -mr 0. 0. 0.001 0.002 0.003 0.01 0.1 0.001 0.002 0. 0. 0. -mi $MEM_BUDGET \
                        --nprobe 10 \
                        -nq $NUM_QUERIES \
                        --ranking_policy LFU \

