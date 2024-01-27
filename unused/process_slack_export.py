import json
import sys

"""
This script processes a Slack export file and extracts the messages with "type": "message".
It takes two command-line arguments: the input file path and the output file path.
It reads the input file as JSON, extracts the messages, and writes them as JSON to the output file.
"""

# Check that the correct number of command-line arguments were provided
if len(sys.argv) != 3:
    print('Usage: python process_slack_export.py input_file output_file')
    sys.exit(1)

# Get the input and output file paths from the command-line arguments
input_file = sys.argv[1]
output_file = sys.argv[2]

# Open the input file and read the JSON data
with open(input_file, 'r') as input_f:
    data = json.load(input_f)

# Extract the messages with "type": "message"
messages = [
    {
        "client_msg_id": m["client_msg_id"],
        "ts": m["ts"],
        "text": m["text"]
    }
    for m in data
    if m["type"] == "message"
]

# Open the output file and write the messages as JSON
with open(output_file, 'w') as output_f:
    json.dump(messages, output_f)
