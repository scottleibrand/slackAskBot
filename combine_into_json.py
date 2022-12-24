#!/usr/bin/env python

"""
Combine data and embeddings into a single JSON file.

This script combines data from two different JSON files into one output file.
It takes three arguments: `data_dir`, `embeddings_dir`, and `output_file`.
It iterates over the subdirectories in the `data_dir` and looks for JSON files.
It then reads the data from the JSON files and checks for an embeddings file in the `embeddings_dir` with the same name.
If the embeddings file is found, it is added to the data JSON.
All the data is then written to the `output_file` in a pretty-printed format.
"""

import os
import json
import csv
import sys

# Check for all three arguments
if len(sys.argv) != 4:
    print('Usage: combine_into_json.py <data_dir> <embeddings_dir> <output_file>')
    sys.exit(1)

# Get arguments
data_dir = sys.argv[1]
embeddings_dir = sys.argv[2]
output_file = sys.argv[3]

all_data = []

# Open output file
with open(output_file, 'w') as outfile:
    # Iterate over subdirectories in data directory
    for subdir in sorted(os.listdir(data_dir)):
        subdir_path = os.path.join(data_dir, subdir)

        # Iterate over json files in subdirectory
        for filename in sorted(os.listdir(subdir_path)):
            if filename.endswith('.json'):
                file_path = os.path.join(subdir_path, filename)

                # Read data json
                with open(file_path) as data_file:
                    data_json = json.load(data_file)

                # Read embeddings json
                embeddings_path = os.path.join(embeddings_dir, subdir, filename)
                if os.path.exists(embeddings_path) and os.path.getsize(embeddings_path) > 0:
                    print(f'Found embeddings file for {subdir_path}/{filename} at {embeddings_path}')
                    with open(embeddings_path) as embeddings_file:
                        embeddings_json = json.load(embeddings_file)
                        # Add embeddings json to all_data    
                else:
                    #print('Warning: embeddings file not found for {}'.format(filename))
                    print(f'Warning: embeddings file not found for {subdir_path}/{filename} at {embeddings_path}')
                    continue

                # Add data json and embeddings json to all_data
                all_data.append({'messages': data_json, 'ada_search': embeddings_json})

    # Write all record to output file, pretty-printed
    #json.dump({'messages': data_json, 'ada_search': embeddings_json}, outfile, indent=4)
    json.dump(all_data, outfile, indent=4)