'''
Index store class
    - Store index files in memory for faster access
    - Add, get and remove indexes
'''

import faiss

from utils.logger import Logger


class IndexStore:
    '''
    A class to store indexes in memory for faster access
    '''
    def __init__(self, max_indexes=100):
        self.indexes = {}
        self.num_indexes = 0
        self.max_indexes = max_indexes

    @Logger.log_index_load_time
    def load_index(self, index_path):
        return faiss.read_index(index_path)

    def add_index(self, index_path, index):
        # Remove the first index if the number of indexes exceeds the max indexes
        if self.num_indexes >= self.max_indexes:
            self.remove_index(list(self.indexes.keys())[0])
        self.indexes[index_path] = index
        self.num_indexes += 1

    def get_index(self, index_path):
        # Load the index if it is not in the store
        if index_path not in self.indexes:
            index = self.load_index(index_path)
            # Add the index to the store
            self.add_index(index_path, index)
        return self.indexes[index_path]

    def remove_index(self, index_path):
        del self.indexes[index_path]
        self.num_indexes -= 1
