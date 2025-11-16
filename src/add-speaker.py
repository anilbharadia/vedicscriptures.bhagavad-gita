#!/usr/bin/env python3
"""
Simplified script to add missing 'speaker' properties based solely on explicit prefixes.
Adds speaker if slok's first line starts with one of:
- 'श्रीभगवानुवाच' -> 'श्रीभगवान्'
- 'अर्जुन उवाच'   -> 'अर्जुन'
- 'सञ्जय उवाच'    -> 'सञ्जय'
- 'धृतराष्ट्र उवाच' -> 'धृतराष्ट्र'

Behavior:
- If speaker already present and matches detected prefix, leave unchanged.
- If speaker present but differs from detected prefix AND --fix is passed, correct it.
- If speaker absent and prefix detected, insert speaker immediately before 'slok'.
- Does NOT propagate speakers across verses; use recompute_speakers.py for normalization.

Output: per-file action + final summary counts.
"""

import json
import os
import glob
import argparse
from collections import OrderedDict

PREFIX_MAP = {
    'श्रीभगवानुवाच': 'श्रीभगवान्',
    'अर्जुन उवाच': 'अर्जुन',
    'सञ्जय उवाच': 'सञ्जय',
    'धृतराष्ट्र उवाच': 'धृतराष्ट्र',
}

def first_line(slok: str | None) -> str:
    if not slok:
        return ''
    return slok.split('\n', 1)[0].strip()

def detect(slok: str) -> str | None:
    fl = first_line(slok)
    for prefix, speaker in PREFIX_MAP.items():
        if fl.startswith(prefix):
            return speaker
    return None

def insert_speaker(data: OrderedDict, speaker: str) -> OrderedDict:
    new_data = OrderedDict()
    for k, v in data.items():
        if k == 'speaker':
            continue  # drop old, will reinsert
        if k == 'slok':
            new_data['speaker'] = speaker
        new_data[k] = v
    return new_data

def process_file(path: str, fix: bool, counters: dict):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f, object_pairs_hook=OrderedDict)

    slok_text = data.get('slok', '')
    detected = detect(slok_text)
    existing = data.get('speaker')
    action = 'skip'

    if detected:
        if existing is None:
            # Add speaker
            data = insert_speaker(data, detected)
            action = 'add'
        elif existing != detected:
            if fix:
                data = insert_speaker(data, detected)
                action = 'fix'
            else:
                action = 'mismatch'
        else:
            action = 'match'
    else:
        action = 'none'

    if action in {'add', 'fix'}:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.write('\n')
    counters[action] = counters.get(action, 0) + 1

    print(f"{action:8} {os.path.basename(path)} -> {existing or '∅'} / {detected or '∅'}")

def summarize(counters: dict):
    print("\nSummary:")
    for k in sorted(counters.keys()):
        print(f"  {k:8}: {counters[k]}")


def main():
    parser = argparse.ArgumentParser(description='Add speaker fields based on explicit prefixes.')
    parser.add_argument('--dir', default=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'slok'), help='Directory containing slok JSON files')
    parser.add_argument('--fix', action='store_true', help='Correct mismatched existing speaker values')
    args = parser.parse_args()

    json_files = sorted(glob.glob(os.path.join(args.dir, '*.json')))
    print(f"Scanning {len(json_files)} files in {args.dir}\n")

    counters: dict = {}
    for path in json_files:
        process_file(path, args.fix, counters)

    summarize(counters)

if __name__ == '__main__':
    main()
