
"""
This script combines multiple small files of messages into one file.
It splits large files of data into smaller parts based on the number of tokens in each part.
It takes in data from the 'trimmed' directory and splits it into parts with a maximum of 1000 tokens each.
The parts are then written to the 'combined' directory.
The script also combines multiple files into one if the total number of tokens is less than 1000.
The output files are named with the start and end dates of the data they contain.
"""

import os
import json
import tiktoken

def get_token_count(data):
    enc = tiktoken.get_encoding("gpt2")
    text = json.dumps(data)
    tokens = enc.encode(text)
    return len(tokens)

def split_old(data, tokens_threshold):
    token_count = 0
    messages = []
    message = []
    for item in data:
        print(item)
        
        if 'client_msg_id' in item:
            #print(item['client_msg_id'])
            message = {
                'client_msg_id': item['client_msg_id'],
                'ts': item['ts'],
                'text': item['text']
            }
            
def splitdata(data, tokens_threshold):
    parts = []
    current_part = []
    current_length = 0
    for item in data:
        item_length = get_token_count(item)
        if current_length + item_length > tokens_threshold:
            parts.append(current_part)
            current_part = []
            current_length = 0
        current_part.append(item)
        current_length += item_length
    parts.append(current_part)
    return parts

def main():
    tokens_threshold=1000
    maxtokens = 3000

    # Create the combined directory if it doesn't exist
    combined_dir = 'combined/'
    if not os.path.exists(combined_dir):
        os.makedirs(combined_dir)

    # Iterate through the trimmed directory
    for subdir in os.listdir('trimmed/'):
        # Create the same subdirectory in combined
        combined_subdir = os.path.join(combined_dir, subdir)
        
        # Initialize the token count and start/end dates and the combined data
        token_count = 0
        start_date = None
        end_date = None
        combined_data = []
        split_data = []
      

        for filename in sorted(os.listdir(os.path.join('trimmed/', subdir))):
            # Read in the file
            with open(os.path.join('trimmed/', subdir, filename)) as f:
                data = json.load(f)
            
            # Get the token count of the file's messages
            file_token_count = get_token_count(data)
            print(f'{subdir}/{filename}: {file_token_count} tokens')
            if start_date is None:
                start_date = filename.split('.')[0]
            if end_date is None:
                end_date = filename.split('.')[0]
            
            # If the current file tokens are greater than maxtokens, write out any previous files,
            #   then split the current file into multiple parts and write out each part
            if file_token_count > maxtokens:
                # Write out the previous messages
                if token_count > 0:
                    if not os.path.exists(combined_subdir):
                        os.makedirs(combined_subdir)
                        if start_date is not None and end_date is not None:
                            output_filename = start_date + '-' + end_date + '.json'
                            print(f'{filename} combined token count: {token_count+file_token_count} tokens: writing out previous {token_count} tokens')
                            # Write out the combined messages
                            if combined_data is not None:
                                with open(os.path.join(combined_subdir, output_filename), 'w') as f:
                                    json.dump(combined_data, f)
                # Split the current file
                split_data = splitdata(data, tokens_threshold)
                if split_data is not None:
                    for i, message in enumerate(split_data):
                        if not os.path.exists(combined_subdir):
                            os.makedirs(combined_subdir)
                        # format the part number to 2 digits
                        output_filename = start_date + '-' + end_date + '-part' + str(i).zfill(2) + '.json'
                        print(f'Writing out {output_filename} with {get_token_count(message)} tokens')
                        with open(os.path.join(combined_subdir, output_filename), 'w') as f:
                            json.dump(message, f)
                # Reset the start/end dates
                start_date = None
                end_date = None
                # Reset the combined data
                combined_data = []
                # Reset the token count to the current file's token count
                token_count = 0
            # Else if the combined token count plus the current file tokens are greater than tokens_threshold,
            #   then write out the combined messages and reset the combined data w/ the current file's messages
            elif token_count + file_token_count > tokens_threshold:
                # Write out the previous messages
                if not os.path.exists(combined_subdir):
                    os.makedirs(combined_subdir)
        
                print(f'{filename} combined token count: {token_count+file_token_count} tokens: writing out previous {token_count} tokens')
                # Create the output filename
                if start_date is not None and end_date is not None:
                    output_filename = start_date + '-' + end_date + '.json'
                    # If there is no combined data, write out the current file
                    if len(combined_data) == 0:
                        for message in data:
                            combined_data.append(message)
                    if not os.path.exists(combined_subdir):
                        os.makedirs(combined_subdir)
                    # Write out the combined messages
                    if combined_data is not None:
                        with open(os.path.join(combined_subdir, output_filename), 'w') as f:
                            json.dump(combined_data, f)
                # Reset the start/end dates
                start_date = None
                end_date = None
                # Reset the combined data
                combined_data = data
                # Reset the token count to the current file's token count
                token_count = file_token_count
            # Else the cumulative token count plus the current file tokens is less than tokens_threshold, so continue to read in the next file
            else:
                token_count += file_token_count
                # Update the start and end dates
                end_date = filename.split('.')[0]
                # Combine the messages
                for message in data:
                    combined_data.append(message)
                print(f'{filename} combined token count: {token_count+file_token_count} tokens: continuing')
                continue

        # If any data remains, write it out
        if len(combined_data) > 0:
            # Create the output filename
            if start_date is None:
                start_date = filename.split('.')[0]
            if end_date is None:
                end_date = filename.split('.')[0]
            #if start_date is None:
                #start_date = end_date
            if not os.path.exists(combined_subdir):
                os.makedirs(combined_subdir)
            output_filename = start_date + '-' + end_date + '.json'
            # Write out the combined messages
            if combined_data is not None:
                with open(os.path.join(combined_subdir, output_filename), 'w') as f:
                    json.dump(combined_data, f)

if __name__ == '__main__':
    main()
