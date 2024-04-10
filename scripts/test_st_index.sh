#!/bin/bash

python query_shard_idx.py -nq 1000 --search_topology index --max_index_store 100 --mixtures_ratio 0 --log logs/st_index.log --seed 0
python query_shard_idx.py -nq 1000 --search_topology index --max_index_store 10 --mixtures_ratio 0 --log logs/st_index.log --seed 0
python query_shard_idx.py -nq 1000 --search_topology index --max_index_store 100 --mixtures_ratio 0.5 --log logs/st_index.log --seed 0
python query_shard_idx.py -nq 1000 --search_topology index --max_index_store 10 --mixtures_ratio 0.5 --log logs/st_index.log --seed 0
python query_shard_idx.py -nq 1000 --search_topology index --max_index_store 100 --mixtures_ratio 1 --log logs/st_index.log --seed 0
python query_shard_idx.py -nq 1000 --search_topology index --max_index_store 10 --mixtures_ratio 1 --log logs/st_index.log --seed 0
