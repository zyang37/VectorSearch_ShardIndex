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


# NOT USED SLOW
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


class IndexStore:
    '''
    A class to store indexes in memory for faster access
    '''
    def __init__(self, max_indexes=1000):
        self.indexes = {}
        self.num_indexes = 0
        self.max_indexes = max_indexes

    @Logger.log_index_load_time
    def load_index(self, index_path):
        # update index status, 1 means it is currently loading
        self.indexes[index_path] = "loading"
        return faiss.read_index(index_path)

    def add_index_from_path(self, index_path):
        # Remove the first index if the number of indexes exceeds the max indexes
        if self.at_capacity():
            self.swap_index()
        self.indexes[index_path] = self.load_index(index_path)
        self.num_indexes += 1

    def add_index(self, index_path, index):
        # Remove the first index if the number of indexes exceeds the max indexes
        if self.at_capacity():
            # self.remove_index(list(self.indexes.keys())[0])
            self.swap_index()
        self.indexes[index_path] = index
        self.num_indexes += 1

    def get_index(self, index_path):
        # Load the index if it is not in the store
        if index_path not in self.indexes:
            # print("NOT in store!")
            index = self.load_index(index_path)
            # Add the index to the store
            self.add_index(index_path, index)
        return self.indexes[index_path]

    def remove_index(self, index_path):
        del self.indexes[index_path]
        self.num_indexes -= 1

    def at_capacity(self):
        return self.num_indexes >= self.max_indexes
    
    # NEED TO UPDATE!!!
    def swap_index(self):
        # get a key to remove, and call remove_index
        # Currently, remove the first index
        remove_ids_key = list(self.indexes.keys())[0]
        self.remove_index(remove_ids_key)
