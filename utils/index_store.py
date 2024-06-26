'''
Index store class
    - Store index files in memory for faster access
    - Add, get and remove indexes
'''

import time
import asyncio
import threading
import multiprocessing

import faiss
from utils.logger import Logger


class ThreadDataLoader(threading.Thread):
    def __init__(self, Index_store, all_file_paths:list):
        super().__init__()
        self.daemon = True
        self.keep_running = True
        self.paused = threading.Event()
        self.paused.set()  # Set initially to not paused
        self.index_store = Index_store
        self.all_file_paths = all_file_paths
        
        self.lock = self.index_store.lock
        self.file_paths_to_load = []
        # self.pause_loading()

    def run(self):
        # print("loading task is starting")
        while self.keep_running:
            self.paused.wait()  # This will block if the loader is paused
            # if len(self.file_paths_to_load)==0 or self.index_store.at_capacity():
            #     self.pause_loading()
            #     continue

            if len(self.file_paths_to_load)==0:
                with self.lock:
                    hot_idxs = self.index_store.index_manager.get_head_index(k=self.index_store.max_indexes)
                    if len(hot_idxs) > 1:
                        # when it is 1, means it only contains centroid index, not need to keep loading it
                        self.file_paths_to_load = hot_idxs
                    continue

            if self.index_store.at_capacity():
                self.pause_loading()
                continue

            self.fetch_data(self.file_paths_to_load[0])

    def update_files_to_load(self, file_paths):
        self.file_paths_to_load = file_paths

    def parse_stopology(self, stopology):
        self.file_paths_to_load = [self.all_file_paths[idx] for idx in stopology.keys()]

    def fetch_data(self, file_path):
        # Add index to the store
        # if file_path not in self.index_store.indexes:
        self.index_store.add_index_from_path(file_path)
        # print(f"Index {file_path} has been loaded.")
        try:
            self.file_paths_to_load.remove(file_path)
        except:
            pass

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
        self.index_loader = None
        self.local_ranking_dict = {}
        self.local_ranking_list = []
        self.lock = threading.Lock()

        '''
        Obtain rank_policy from index_manager
            - LFU: Least Frequently Used
            - LRU: Least Recently Used
        '''
        if self.index_manager is not None:
            self.rank_policy = self.index_manager.policy

    def set_index_loader(self, index_loader):
        self.index_loader = index_loader

    def cleanup(self, stopology, idxpath2id_map):
        '''
        rm idx that is not in stopology, used in serving
        '''
        updated_stopology = stopology.copy()
        remove_idxs = []
        dram_required_idxs = [] # [(idx: [q1,q2], ...)]

        # BE CAREFUL: indexes: {full_idx_path: [q1]}, stopology: {idx: [q1]}
        with self.lock:
            for idx_path in self.indexes.keys():
                if "centroids" in idx_path:
                    # centroid will not present in stopology
                    continue
                idx = idxpath2id_map[idx_path]
                if idx not in updated_stopology.keys():
                    remove_idxs.append(idx)
                else:
                    dram_required_idxs.append( (idx, updated_stopology[idx]) )

                    # Update later
                    del updated_stopology[idx]
        
        # clear up unnecessary indexes
        # print("clean up: ", remove_idxs)
        self.remove_multiple_indexes(remove_idxs)

        '''
        Locality aware batching
            1. Search required DRAM-idxs for vsearch
            2. Sort by batch size (small batch goes 1st)
                - finish faster quickly allow to load more indexes
            3. Append old st to the end
        '''
        # dram_required_idxs = sorted(dram_required_idxs, key=lambda x: len(x[1]), reverse=False)
        # print(len(dram_required_idxs))
        dram_required_idxs.extend(list(updated_stopology.items()))
        updated_stopology = dict(dram_required_idxs)
        return updated_stopology

    @Logger.log_index_load_time
    def load_index(self, index_path):
        # update index status, 1 means it is currently loading
        with self.lock:
            self.indexes[index_path] = "loading"
        return faiss.read_index(index_path)

    def add_index_from_path(self, index_path):
        '''
        This design here is stupid. calling load_index will increase the num_indexes without respect to the capacity. 
        So I also handle the capacity here.
        '''
        if self.at_capacity():
            self.evict_index()
        self.add_index(index_path, self.load_index(index_path))

    def add_index(self, index_path, index):
        # handle evicting indexes if the store is at capacity
        if self.at_capacity():
            self.evict_index()
        
        with self.lock:
            # print("adding {}th idx".format(self.num_indexes))
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
            if self.rank_policy == 'LFU':
                self.index_manager.update_index_rank(index_path, query_shape[0]/1000.)
            else:
                self.index_manager.update_index_rank(index_path, time.perf_counter())

        # evict before adding new index
        # if self.at_capacity():
            # self.evict_index()

        if index_path not in self.indexes:
            # print("NOT loaded yet. Loading now...")
            self.add_index_from_path(index_path)
        elif self.indexes[index_path] == "loading":
            while self.indexes[index_path] == "loading":
                time.sleep(0.000001)
        
        return self.indexes[index_path]

    def remove_index(self, index_path):
        with self.lock:
            if index_path in self.indexes:
                del self.indexes[index_path]
                self.num_indexes -= 1
        
        if self.index_loader is not None:
            self.index_loader.resume_loading()

        return 
        try:
            '''
            Note: calling remove from index store is fine. 
            But when it is called outside of the store, sometime it is already removed.
            '''
            with self.lock:
                del self.indexes[index_path]
                self.num_indexes -= 1
        except Exception as e: 
            # print the error message
            print(e)
            print("delete index failed")

    def remove_multiple_indexes(self, index_paths):
        for index_path in index_paths:
            self.remove_index(index_path)

    def at_capacity(self):
        with self.lock:
            self.num_indexes = len(self.indexes)
            if self.num_indexes > self.max_indexes:
                raise Exception("Index store is exceeding the maximum capacity!!! there is a bug in the code. {} > {}".format(self.num_indexes, self.max_indexes))
            return self.num_indexes >= self.max_indexes
    
    def reset_local_ranking(self):
        self.local_ranking_dict = {}
        for index_path in self.indexes.keys():
            # obtain ranking for DRAM-index from the index manager
            try:
                self.local_ranking_dict[index_path] = self.index_manager.ranking_dict[index_path]
            except:
                # index could be swapped out but have a ranking
                self.local_ranking_dict[index_path] = 0

    def evict_index(self):
        if self.index_manager is not None:
            self.reset_local_ranking()
            self.local_ranking_list = sorted(self.local_ranking_dict, key=self.local_ranking_dict.get, reverse=True)
            remove_ids_key = self.local_ranking_list[-1]
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
