#!/bin/bash

ST=index
NUM_QUERIES=10000
K=10
NPROBE=10
MIXTURES_RATIO=0.01

for i in 1 100 200 300 400 500 600 700 800 900 1000
do
    echo $i
    python query_shard_idx.py -nq $NUM_QUERIES -k $K --nprobe $NPROBE \
                                --search_topology $ST \
                                --max_index_store $i \
                                --mixtures_ratio $MIXTURES_RATIO \
                                --log logs/st_${ST}_${i}_batch.log \
                                --seed 0
    # rm logs/app.log
done
