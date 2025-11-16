#!/usr/bin/env python3
"""
Recompute and normalize 'speaker' properties for all slok JSON files.
Rules:
1. Sort files by numeric (chapter, verse) extracted from filename.
2. If a slok starts with a known prefix (… उवाच) set current speaker to that value.
3. If a slok does not start with a known prefix, inherit the last current speaker for that chapter sequence.
4. Overwrite any existing speaker to the recomputed value (except if no current speaker yet).
5. Always place 'speaker' immediately before 'slok' in object order; preserve other fields and trailing newline.

Known prefixes mapping:
- 'श्रीभगवानुवाच' -> 'श्रीभगवान्'
- 'अर्जुन उवाच' -> 'अर्जुन'
- 'सञ्जय उवाच' -> 'सञ्जय'
- 'धृतराष्ट्र उवाच' -> 'धृतराष्ट्र'

This fixes earlier propagation bug caused by lexicographic filename sorting (e.g., verse 2.40 got speaker 'अर्जुन' due to verse 2.4 processed after 2.39).
"""

import json
import os
import re
import glob
from collections import OrderedDict

PREFIX_MAP = {
    'श्रीभगवानुवाच': 'श्रीभगवान्',
    'अर्जुन उवाच': 'अर्जुन',
    'सञ्जय उवाच': 'सञ्जय',
    'धृतराष्ट्र उवाच': 'धृतराष्ट्र',
}

FILENAME_RE = re.compile(r"bhagavadgita_chapter_(\d+)_slok_(\d+)\.json$")

def parse_numbers(path: str):
    m = FILENAME_RE.search(os.path.basename(path))
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))

def detect_prefix(slok: str):
    if not slok:
        return None
    first_line = slok.split('\n', 1)[0].strip()
    for prefix, speaker in PREFIX_MAP.items():
        if first_line.startswith(prefix):
            return speaker
    return None

def rebuild_with_speaker(data: OrderedDict, speaker: str) -> OrderedDict:
    # Ensure speaker inserted just before slok.
    new_data = OrderedDict()
    for k, v in data.items():
        if k == 'slok':
            new_data['speaker'] = speaker
        if k == 'speaker':
            # Skip old speaker entry (we will reinsert)
            continue
        new_data[k] = v
    return new_data

def main():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'slok')
    paths = glob.glob(os.path.join(base_dir, '*.json'))

    entries = []
    for p in paths:
        nums = parse_numbers(p)
        if nums:
            entries.append((nums[0], nums[1], p))
    # Sort by chapter then verse numerically
    entries.sort(key=lambda t: (t[0], t[1]))

    current_speaker = None
    changed = 0
    examined = 0
    chapter_last_speaker = None
    last_chapter = None

    for chap, verse, path in entries:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f, object_pairs_hook=OrderedDict)
        slok = data.get('slok', '')
        detected = detect_prefix(slok)

        if chap != last_chapter:
            # Reset speaker context at new chapter start unless first slok sets it.
            current_speaker = None
            chapter_last_speaker = None
            last_chapter = chap

        if detected:
            current_speaker = detected
            chapter_last_speaker = detected
        elif current_speaker is None:
            # If no current speaker yet (e.g., malformed opening), leave as is.
            pass

        computed = current_speaker
        existing = data.get('speaker')

        if computed and existing != computed:
            new_data = rebuild_with_speaker(data, computed)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=4)
                f.write('\n')
            changed += 1
            print(f"✓ Updated {os.path.basename(path)} -> {computed} (was {existing})")
        else:
            print(f"= Kept   {os.path.basename(path)} -> {existing or 'None'}")
        examined += 1

    print(f"\nSummary: examined={examined}, changed={changed}")

if __name__ == '__main__':
    main()

