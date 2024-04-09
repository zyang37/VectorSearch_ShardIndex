import numpy as np
import json
import pickle

# numpy
def save_np_to_file(file_path, np_array):
    np.save(file_path, np_array)
    # print(f"Saved to {file_path}")

def load_npy(npy_path):
    return np.load(npy_path)

# json
def save_json_to_file(file_path, json_data):
    with open(file_path, "w") as f:
        json.dump(json_data, f, indent=4)

def load_json(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    return data

# pickle
def save_pickle_to_file(file_path, data):
    with open(file_path, "wb") as f:
        pickle.dump(data, f)

def load_pickle(pickle_path):
    with open(pickle_path, "rb") as f:
        data = pickle.load(f)
    return data
