#!/bin/bash

NUM_QUERIES=15000
MEM_BUDGET=100

RANDOM_MRS=100

rm logs/app.log

python squery_shard_idx.py --random_mixtures_ratios $RANDOM_MRS \
                        -mi $MEM_BUDGET \
                        --nprobe 10 \
                        -nq $NUM_QUERIES \
                        --ranking_policy LRU \
                        --seed 42

rm logs/app.log

python squery_shard_idx.py --random_mixtures_ratios $RANDOM_MRS \
                        -mi $MEM_BUDGET \
                        --nprobe 10 \
                        -nq $NUM_QUERIES \
                        --ranking_policy LFU \
                        --seed 42

