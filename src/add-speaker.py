#!/usr/bin/env python3
"""
Script to add 'speaker' property to JSON files where slok starts with 'श्रीभगवानुवाच'
"""

import json
import os
import glob
from collections import OrderedDict

def add_speaker_to_file(file_path):
    """Add speaker property to a JSON file if slok starts with श्रीभगवानुवाच"""

    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f, object_pairs_hook=OrderedDict)

    # Check if slok starts with श्रीभगवानुवाच
    if 'slok' in data and data['slok'].startswith('श्रीभगवानुवाच'):
        # Check if speaker property already exists
        if 'speaker' not in data:
            # Create a new OrderedDict with speaker inserted before slok
            new_data = OrderedDict()
            for key, value in data.items():
                if key == 'slok':
                    # Add speaker before slok
                    new_data['speaker'] = 'श्रीभगवान्'
                new_data[key] = value

            # Write back to file with trailing newline
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=4)
                f.write('\n')  # Preserve the trailing newline

            print(f"✓ Updated: {os.path.basename(file_path)}")
            return True
        else:
            print(f"⊘ Skipped (speaker already exists): {os.path.basename(file_path)}")
            return False
    else:
        print(f"- Skipped (no matching slok): {os.path.basename(file_path)}")
        return False

def main():
    # Get all JSON files in the slok directory
    slok_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'slok')
    json_files = glob.glob(os.path.join(slok_dir, '*.json'))

    print(f"Processing {len(json_files)} JSON files in {slok_dir}...\n")

    updated_count = 0
    for file_path in sorted(json_files):
        if add_speaker_to_file(file_path):
            updated_count += 1

    print(f"\n✓ Done! Updated {updated_count} files.")

if __name__ == '__main__':
    main()

