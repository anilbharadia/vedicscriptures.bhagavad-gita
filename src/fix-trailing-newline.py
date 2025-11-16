#!/usr/bin/env python3
"""
Script to fix trailing newline in all JSON files
"""

import json
import os
import glob
from collections import OrderedDict

def fix_trailing_newline(file_path):
    """Add trailing newline to a JSON file if missing"""

    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if file already ends with newline
    if content.endswith('\n'):
        return False

    # Read and write with trailing newline
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f, object_pairs_hook=OrderedDict)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write('\n')

    print(f"✓ Fixed: {os.path.basename(file_path)}")
    return True

def main():
    # Get all JSON files in the slok directory
    slok_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'slok')
    json_files = glob.glob(os.path.join(slok_dir, '*.json'))

    print(f"Processing {len(json_files)} JSON files in {slok_dir}...\n")

    fixed_count = 0
    for file_path in sorted(json_files):
        if fix_trailing_newline(file_path):
            fixed_count += 1

    print(f"\n✓ Done! Fixed {fixed_count} files.")

if __name__ == '__main__':
    main()

