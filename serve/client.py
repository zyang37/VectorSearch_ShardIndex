'''
Client-side code for sending a NumPy query batch to a server via a POST request.
'''

import sys
import argparse
import requests

import numpy as np

sys.path.append('..')
from utils.vdb_utils import query_index_file, random_queries_mix_distribs

def send_array_to_server(url, array):
    """
    Sends a NumPy array to a server via POST request and returns the processed array.

    Parameters:
    - url: The URL of the server endpoint expecting the array.
    - array: The NumPy array to send.

    Returns:
    - A NumPy array returned by the server, or None if an error occurred.
    """
    try:
        # Convert the NumPy array to a list for JSON serialization
        array_list = array.tolist()
        
        # Send the array to the server as JSON and receive the response
        response = requests.post(url, json={'array': array_list})
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Convert the response data back into a NumPy array
        processed_array = np.array(response.json()['processed_array'])
        return processed_array

    except requests.RequestException as e:
        print(f"Request error: {e}")
    except ValueError as e:
        print(f"Error processing response data: {e}")
    return None

def batch_query_generator(num_queries, dim, mixtures_ratio, seed):
    '''
    This function generates random query batch where queries are drawn from a mix of distributions.

    Args:
        - num_queries: number of queries to generate
        - dim: dimensionality of the queries
        - mixtures_ratio [0,1]: 
            - 0 means draw from one distribution. 
            - 1 means every queries are drawn from different distributions.
            - 0.1 means per 10% of the query_batch are drawn from one distribution. 
    '''
    queries = random_queries_mix_distribs(num_queries, dim, mixtures_ratio=mixtures_ratio, low=-1, high=.1, seed=seed)
    return queries

def main(args):
    # The server URL
    url = 'http://127.0.0.1:5000/vector_search'
    
    # Create a NumPy array to send
    query_batch = batch_query_generator(args.num_query, args.dim, args.mixtures_ratio, args.seed)
    
    print("Sending query_batch ({}) to server:".format(query_batch.shape))
    topk_results = send_array_to_server(url, query_batch)
    
    if topk_results is not None:
        print("Responses from server: {}".format(topk_results.shape))
    else:
        print("Failed to receive a valid response from the server.")
    return topk_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a NumPy array to a server via a POST request")
    parser.add_argument("-np", "--nprobe", default=10, help="a small number (nprobe) of subsets to visit", type=int,)
    parser.add_argument("-k", default=3, help="top k results", type=int,)
    parser.add_argument("-nq", "--num_query", default=5, help="number of queries", type=int,)
    parser.add_argument("-mr", "--mixtures_ratio", default=0., help="mixtures ratio for random queries", type=float,)
    parser.add_argument("-st", "--search_topology", default="index", 
                        help="search topology: <index>, <query> or <index_async>", type=str,)
    parser.add_argument("-d", "--dim", default=128, help="dimension of embeddings", type=int,)
    parser.add_argument("--seed", default=None, help="random seed", type=int,)
    args = parser.parse_args()
    
    topk_results = main(args)
    