'''
Index store class
    - Store index files in memory for faster access
    - Add, get and remove indexes
'''

import asyncio
import threading
import multiprocessing

import faiss
from utils.logger import Logger


class ThreadDataLoader(threading.Thread):
    def __init__(self, Index_store, all_file_paths:list, stopology):
        super().__init__()
        self.daemon = True
        self.keep_running = True
        self.paused = threading.Event()
        self.paused.set()  # Set initially to not paused
        self.index_store = Index_store
        self.all_file_paths = all_file_paths
        self.file_paths = []
        self.parse_stopology(stopology)

    def run(self):
        # print("loading task is starting")
        while self.keep_running:
            self.paused.wait()  # This will block if the loader is paused
            if len(self.file_paths)==0 or self.index_store.at_capacity():
                self.pause_loading()
                continue
            # print("loading", self.file_paths[0])
            self.fetch_data(self.file_paths[0])

    def parse_stopology(self, stopology):
        self.file_paths = [self.all_file_paths[idx] for idx in stopology.keys()]

    def fetch_data(self, file_path):
        # Add index to the store
        # index = self.index_store.load_index(file_path)
        # self.index_store.add_index(file_path, index)
        self.index_store.add_index_from_path(file_path)
        self.file_paths.remove(file_path)

    def pause_loading(self):
        self.paused.clear()  # Clearing the event to pause
        # print("Pausing the loader...")

    def resume_loading(self):
        self.paused.set()  # Setting the event to resume
        # print("Resuming the loader...")

    def stop_loading(self):
        self.keep_running = False
        self.resume_loading()  # If it's paused, we need to resume it to allow it to exit
        # print("Stopping the loader...")

class IndexStore:
    '''
    A class to store indexes in memory for faster access
    '''
    def __init__(self, max_indexes=1000, index_manager=None):
        self.indexes = {}
        self.num_indexes = 0
        self.max_indexes = max_indexes
        self.index_manager = index_manager
        self.local_ranking_dict = {}
        self.local_ranking_list = []

    @Logger.log_index_load_time
    def load_index(self, index_path):
        # update index status, 1 means it is currently loading
        self.indexes[index_path] = "loading"
        return faiss.read_index(index_path)

    def add_index_from_path(self, index_path):
        self.add_index(index_path, self.load_index(index_path))

    def add_index(self, index_path, index):
        # handle evicting indexes if the store is at capacity
        if self.at_capacity():
            self.evict_index()
        self.indexes[index_path] = index
        self.num_indexes = len(self.indexes)

    def get_index(self, index_path, query_shape=None):
        '''
        User trying to get index
            - User need it now
            - Do not evict this index

        args:
            - index_path: str, path to the index file
            - query_size: int, use to update the ranking
        '''
        if self.index_manager is not None:
            self.index_manager.update_index_rank(index_path, query_shape[0])

        # evict before adding new index
        if self.at_capacity():
            self.evict_index()

        if index_path not in self.indexes:
            self.add_index_from_path(index_path)
        
        return self.indexes[index_path]

    def remove_index(self, index_path):
        try:
            '''
            Note: calling remove from index store is fine. 
            But when it is called outside of the store, sometime it is already removed.
            '''
            del self.indexes[index_path]
            self.num_indexes = len(self.indexes)
        except:
            print("delete index failed")

    def remove_multiple_indexes(self, index_paths):
        for index_path in index_paths:
            self.remove_index(index_path)

    def at_capacity(self):
        if self.num_indexes > self.max_indexes:
            raise Exception("Index store is exceeding the maximum capacity!!! there is a bug in the code.")
        return self.num_indexes >= self.max_indexes
    
    def reset_local_ranking(self):
        self.local_ranking_dict = {}
        for index_path in self.indexes.keys():
            # obtain ranking for DRAM-index from the index manager
            self.local_ranking_dict[index_path] = self.index_manager.ranking_dict[index_path]

    # BUG: this function is not working properly
    def evict_index(self):
        # get a key to remove, and call remove_index
        if self.index_manager is not None:
            self.reset_local_ranking()
            self.local_ranking_list = sorted(self.local_ranking_dict, key=self.local_ranking_dict.get, reverse=True)
            remove_ids_key = self.local_ranking_list[-1]
            # print(self.local_ranking_dict)
            # print(remove_ids_key)
        else:
            remove_ids_key = list(self.indexes.keys())[0]
        self.remove_index(remove_ids_key)



# ===================================================================================================
# NOT USED
class ProcessDataLoader(multiprocessing.Process):
    def __init__(self, Index_store, all_file_paths:list, stopology):
        super().__init__()
        self.daemon = True
        self.keep_running = multiprocessing.Value('i', 1)  # Using shared memory for process-safe flag
        self.paused = multiprocessing.Event()
        self.paused.set()  # Set initially to not paused
        self.index_store = Index_store
        self.all_file_paths = all_file_paths
        self.file_paths = []
        self.parse_stopology(stopology)

    def run(self):
        # print("loading task is starting")
        while self.keep_running.value:
            self.paused.wait()  # This will block if the loader is paused
            if len(self.file_paths) == 0 or self.index_store.at_capacity():
                self.pause_loading()
                continue
            # print(f"loading {self.file_paths[0]}")
            self.fetch_data(self.file_paths[0])

    def parse_stopology(self, stopology):
        self.file_paths = [self.all_file_paths[idx] for idx in stopology.keys()]

    def fetch_data(self, file_path):
        # Simulate adding index to the store
        index = self.index_store.load_index(file_path)  # This method should be process-safe
        self.index_store.add_index(file_path, index)
        self.file_paths.remove(file_path)  # Manage list operations carefully, as they're shared across processes

    def pause_loading(self):
        self.paused.clear()  # Clearing the event to pause
        # print("Pausing the loader...")

    def resume_loading(self):
        self.paused.set()  # Setting the event to resume
        # print("Resuming the loader...")

    def stop_loading(self):
        self.keep_running.value = 0
        self.resume_loading()  # If it's paused, we need to resume it to allow it to exit
        # print("Stopping the loader...")


# NOT USED
class AsyncDataLoader:
    '''
    A class to asynchronously load data. Signal to pause and resume data loading.
    '''
    def __init__(self, Index_store, file_paths:list):
        '''
        args:
            - Index_store: IndexStore object
            - file_paths: list of file paths to load (not in the store yet)
        '''
        self.index_store = Index_store
        self.file_paths = file_paths
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        self.running = False

    def update_file_paths(self, file_paths):
        self.file_paths = file_paths

    async def load_data(self):
        # print("loading task is starting")
        self.running = True
        try:
            while self.running:
                await self.pause_event.wait()
                if len(self.file_paths)==0 or self.index_store.at_capacity():
                    self.pause()
                else:
                    # print("loading", self.file_paths[0])
                    self.fetch_data(self.file_paths[0])
        finally:
            print("Loader has been stopped.")

    async def pause_loading(self):
        self.pause_event.clear()

    def fetch_data(self, file_path):
        # Add index to the store
        index = self.index_store.load_index(file_path)
        self.index_store.add_index(file_path, index)
        self.file_paths.remove(file_path)

    def start(self):
        """Start the background task."""
        asyncio.create_task(self.load_data())

    def stop(self):
        """Stop the background task."""
        self.running = False
        self.pause_event.set()  # Ensure the loop can exit if it is paused

    def pause(self):
        """Pause the background task."""
        self.pause_event.clear()

    def resume(self):
        """Resume the background task."""
        self.pause_event.set()
