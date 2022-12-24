"""
Process files in an input directory and get embeddings using OpenAI Text Embedding API, writing the embeddings to an output directory.

This script takes an input directory and an output directory as command-line arguments
and processes all the files in the input directory.
For each file, it gets the embedding using the OpenAI Text Embedding API
and writes the embedding to an identically named file in the output directory.
If the line is longer than 8000 tokens, it will split the line into chunks
of <8000 tokens and write each chunk to its own file.
"""

import openai
from openai.embeddings_utils import get_embedding
import sys
import os
import tiktoken

def get_embeddings_old(input_file, output_file):
    # Open the input file for reading and the output file for writing
    with open(input_file, 'r') as input_f, open(output_file, 'w') as output_f:
        # Iterate over the lines in the input file
        for line in input_f:
            # Get the embedding for the line
            embedding = get_embedding(line, engine='text-embedding-ada-002')
            
            # Write the embedding to the output file as a string
            output_f.write(str(embedding) + '\n')

def get_embeddings(input_file, output_file):
    # Open the input file for reading and the output file for writing
    with open(input_file, 'r') as input_f:
        # Iterate over the lines in the input file
        for line in input_f:
            # Get the token count of the line
            enc = tiktoken.get_encoding("gpt2")
            tokens = enc.encode(line)
            line_token_count = len(tokens)
            
            # If the token count is >8000, split the line into as many equal-sized chunks as needed so each chunk is <8000 tokens
            if line_token_count > 8000:
                num_chunks = line_token_count // 8000
                print(f'{input_file} is too long ({line_token_count} tokens), splitting into {num_chunks+1} chunks')
                for i in range(num_chunks+1):
                    chunk = line[i*8000:(i+1)*8000]
                    # Get the embedding for the chunk
                    embedding = get_embedding(chunk, engine='text-embedding-ada-002')
                    # Write out the chunk embedding to its own file
                    print(f'Writing chunk {i+1} of {num_chunks+1} to {output_file}-chunk-{i+1}')
                    with open(output_file + "-chunk-" + str(i+1), 'w') as chunk_f:
                        chunk_f.write(str(embedding) + '\n')
            else:
                # Get the embedding for the line
                embedding = get_embedding(line, engine='text-embedding-ada-002')
                # Write the embedding to the output file as a string
                with open(output_file, 'w') as output_f:
                    output_f.write(str(embedding) + '\n')

# Check that the correct number of command-line arguments were provided
if len(sys.argv) < 3:
    print('Usage: python get_embeddings.py input_dir output_dir [subdirs]')
    sys.exit(1)

# Get the input and output directory paths from the command-line arguments
input_dir = sys.argv[1]
output_dir = sys.argv[2]

# Create the output directory if it does not exist
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

# Get the subdirectory names from the command-line arguments, or use all subdirectories if none provided
subdirs = sys.argv[3:]
if not subdirs:
    subdirs = os.listdir(input_dir)

# Iterate over all the subdirectories in the input directory
for root, dirs, files in sorted(os.walk(input_dir)):
    # Only process subdirectories with the provided names, or all subdirectories if none provided
    dirname = os.path.basename(root)
    if subdirs and dirname not in subdirs:
        continue
    # Create the same subdirectories in the output directory
    subdir = root.replace(input_dir, output_dir)
    if not os.path.exists(subdir):
        os.mkdir(subdir)
    # Iterate over all the files in the subdirectory
    for file in sorted(files):
        input_file = os.path.join(root, file)
        output_file = os.path.join(subdir, file)
        # Skip the file if the output file already exists and is more than 0 bytes
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f'Skipping {subdir}/{file} because output file already exists')
            continue
        # Skip the file if a chunk of the output file already exists
        if os.path.exists(output_file + "-chunk-1"):
            print(f'Skipping {subdir}/{file} because output file chunks already exist')
            continue
        # Print the file name
        print(f'Processing {subdir}/{file}')
        # Process the file and write the output to an identically named file in the output subdirectory
        get_embeddings(input_file, output_file)