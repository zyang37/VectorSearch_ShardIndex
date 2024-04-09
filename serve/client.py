import requests
import numpy as np

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

def main():
    # The server URL
    url = 'http://127.0.0.1:5000/process_array'
    
    # Create a NumPy array to send
    array_to_send = np.array([1, 2, 3, 4, 5])
    
    print("Sending array to server:", array_to_send)
    processed_array = send_array_to_server(url, array_to_send)
    
    if processed_array is not None:
        print("Processed array received from server:", processed_array)
    else:
        print("Failed to receive a valid response from the server.")

if __name__ == "__main__":
    main()
