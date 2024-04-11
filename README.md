
# Serving Vecter Search for Large Datasets with Index Shards

## Generate the shards
```
mkdir shards

python create_shard_idx.py
```

## Then run the query
```
python query_shard_idx.py
```
