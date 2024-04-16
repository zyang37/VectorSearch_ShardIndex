#!/bin/bash

ST=query
NUM_QUERIES=15000
K=10
NPROBE=10
MIXTURES_RATIO=0.000

for i in 2 10 20 30 40 50 60 70 80 90 100 110 120 130 140 150
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
