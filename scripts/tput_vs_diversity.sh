#!/bin/bash

ST=index
NUM_QUERIES=100000
K=10
NPROBE=10
i=1000
# MIXTURES_RATIO=0.

for MIXTURES_RATIO in 0. 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0
do  
    echo $MIXTURES_RATIO
    python query_shard_idx.py -nq $NUM_QUERIES -k $K --nprobe $NPROBE \
                                --search_topology $ST \
                                --max_index_store $i \
                                --mixtures_ratio $MIXTURES_RATIO \
                                --log logs/st_${ST}_${MIXTURES_RATIO}_batch.log \
                                --seed 0

done
