#!/usr/bin/env python3

"""
This script extracts messages with "type": "message" from a JSON file and writes them to a new JSON file.
It takes two command-line arguments: the input file path and the output file path.
The script opens the input file and reads the JSON data. It then extracts the messages with "type": "message" and stores them in a list.
It then writes them out in a compact pretty-printed format that is valid json with newlines for readability.
"""

import json
import sys

# Check that the correct number of command-line arguments were provided
if len(sys.argv) != 3:
    print("Usage: extract_messages.py <input_file> <output_file>")
    sys.exit(1)

# Get the input and output file paths from the command-line arguments
input_file = sys.argv[1]
output_file = sys.argv[2]

# Open the input file and read the JSON data
with open(input_file, 'r') as f:
    data = json.load(f)

# Extract the messages with "type": "message"
messages = []
for item in data:
    if item['type'] == 'message':
        if 'client_msg_id' in item:
            #print(item['client_msg_id'])
            message = {
                'client_msg_id': item['client_msg_id'],
                'ts': item['ts'],
                'text': item['text']
            }
            #print(message)
            messages.append(message)

# Open the output file and write the messages as JSON
if messages:
    with open(output_file, 'w') as f:
        json_string = json.dumps(messages, indent=4)
        json_string_with_fewer_newlines = json_string.replace(',\n        ', ', ').replace('{\n        ','{ ').replace('\n    }', ' }')
        f.write(json_string_with_fewer_newlines.replace('    {','{'))
        print(f"Finished writing {len(messages)} messages to {output_file}")
