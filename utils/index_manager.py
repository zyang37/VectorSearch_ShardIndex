'''
Ranking policies: 
    - LRU: Least Recently Used
    - LFU: Least Frequently Used
    - Multi-Queue: Multiple queues for different priorities
    - statistics-based: based on statistics of the index
'''

class IndexManager:
    """
    A class to manage index file rankings
    """
    def __init__(self, policy='LFU'):
        '''
        The manager keep track of all the indexes and their rankings. Always assume reverse=True, the ranking is in descending order
        
        args:
            - policy: str, the ranking policy to use, either LFU or LRU
                - LFU: Least Frequently Used
                - LRU: Least Recently Used
        '''
        self.policy = policy

        self.rankings = []
        self.ranking_dict = {}
        self.ranking_updated = True

    def update_index_rank(self, index_path, rank):
        if self.policy == 'LFU' and index_path in self.ranking_dict:
            self.ranking_dict[index_path] += rank
        else:
            self.ranking_dict[index_path] = rank
        self.ranking_updated = False

    def get_tail_index(self, k=1):
        print("get_tail_index")
        if not self.ranking_updated:
            print('sort_rankings')
            self.sort_rankings()
        return self.rankings[-k:]

    def get_head_index(self, k=1):
        if not self.ranking_updated:
            self.sort_rankings()
        return self.rankings[:k]
    
    def reset_rankings(self):
        self.rankings = []
        self.ranking_dict = {}
        self.ranking_updated = True

    def sort_rankings(self):
        # sort the ranking dict by value, 
        # Set rankings list with sort keys: [idx10, idx22, ...] sort by values. 
        self.rankings = sorted(self.ranking_dict, key=self.ranking_dict.get, reverse=True)
        self.ranking_updated = True
