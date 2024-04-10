#!/bin/bash

python query_shard_idx.py -nq 1000 --search_topology query --max_index_store 100 --mixtures_ratio 0 --log logs/st_query.log
python query_shard_idx.py -nq 1000 --search_topology query --max_index_store 10 --mixtures_ratio 0 --log logs/st_query.log
python query_shard_idx.py -nq 1000 --search_topology query --max_index_store 100 --mixtures_ratio 0.5 --log logs/st_query.log
python query_shard_idx.py -nq 1000 --search_topology query --max_index_store 10 --mixtures_ratio 0.5 --log logs/st_query.log
python query_shard_idx.py -nq 1000 --search_topology query --max_index_store 100 --mixtures_ratio 1 --log logs/st_query.log
python query_shard_idx.py -nq 1000 --search_topology query --max_index_store 10 --mixtures_ratio 1 --log logs/st_query.log
