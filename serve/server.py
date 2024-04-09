from flask import Flask, request, jsonify
import numpy as np

app = Flask(__name__)

def process_array(arr):
    """
    Example processing function that multiplies each element by 2.
    
    Parameters:
    - arr: NumPy array to process.
    
    Returns:
    - Processed NumPy array.
    """
    return arr * 10

@app.route('/process_array', methods=['POST'])
def handle_array():
    if not request.json or 'array' not in request.json:
        return jsonify({'error': 'Bad request, JSON with "array" key required'}), 400
    
    try:
        # Convert the JSON array to a NumPy array
        input_array = np.array(request.json['array'])
        print("Received array from client:", input_array)
        
        # Process the array
        processed_array = process_array(input_array)
        
        # Convert the NumPy array back to a list for JSON serialization
        processed_list = processed_array.tolist()
        
        return jsonify({'processed_array': processed_list})
    except Exception as e:
        return jsonify({'error': f'An error occurred processing the array: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
