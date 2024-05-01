
# Efficient Serving of Large-scale Vector Search with Sharded Indexes

A prototype system built on top of Faiss for efficient vector search on large datasets with sharded indexes.

<!-- <p align="center">
  <img src="doc/pref.png" alt="..." width="500"/> -->
# ![](doc/pref.png)

## Setup
```
pip install -r requirements.txt
```

## Generate synthetic index shards
```
mkdir shards

python create_shard_idx.py
```

## Query sharded indexes
```
python query_shard_idx.py
```

## Visualize Logs
Once query index is done, by default logs will be generated called `logs/app.log`. To visualize the logs, run:
```
python vislogs/vislogs.py --log logs/app.log
```
Then, check out `vislogs_tmp.pdf`!
