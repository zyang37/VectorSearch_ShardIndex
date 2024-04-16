#!/bin/bash

ST=index_async
NUM_QUERIES=10000
K=10
NPROBE=10
i=1000
# MIXTURES_RATIO=0.

for MIXTURES_RATIO in 0. 0.002 0.004 0.006 0.008 0.01 0.05 0.1
# for MIXTURES_RATIO in 0. 0.01 0.05 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.
do  
    echo $MIXTURES_RATIO
    python query_shard_idx.py -nq $NUM_QUERIES -k $K --nprobe $NPROBE \
                                --search_topology $ST \
                                --max_index_store $i \
                                --mixtures_ratio $MIXTURES_RATIO \
                                --log logs/st_${ST}_${MIXTURES_RATIO}_batch.log \
                                --seed 0
done
