#!/usr/bin/env python3
"""
Generate markdown file from Bhagavad Gita slok JSON files.
Extracts 'rams.ht' field from each slok and creates a bullet-point list.
"""

import json
import os
import re
from pathlib import Path


def extract_chapter_slok_numbers(filename):
    """
    Extract chapter and slok numbers from filename.

    Args:
        filename: String like 'bhagavadgita_chapter_1_slok_1.json'

    Returns:
        Tuple of (chapter_num, slok_num) as integers, or None if pattern doesn't match
    """
    match = re.match(r'bhagavadgita_chapter_(\d+)_slok_(\d+)\.json', filename)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return None


def read_slok_files(slok_dir):
    """
    Read all slok JSON files and extract rams.ht field.

    Args:
        slok_dir: Path to the directory containing slok JSON files

    Returns:
        List of tuples: (chapter_num, slok_num, rams_ht_text)
    """
    slok_data = []

    # Get all JSON files in the directory
    slok_path = Path(slok_dir)
    if not slok_path.exists():
        print(f"Error: Directory {slok_dir} does not exist!")
        return []

    for json_file in slok_path.glob('bhagavadgita_chapter_*_slok_*.json'):
        # Extract chapter and slok numbers from filename
        numbers = extract_chapter_slok_numbers(json_file.name)
        if not numbers:
            continue

        chapter_num, slok_num = numbers

        # Read JSON file
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract rams.ht field
            if 'rams' in data and 'ht' in data['rams']:
                rams_ht = data['rams']['ht']
                slok_data.append((chapter_num, slok_num, rams_ht))
            else:
                print(f"Warning: 'rams.ht' not found in {json_file.name}")

        except json.JSONDecodeError as e:
            print(f"Error reading {json_file.name}: {e}")
        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")

    return slok_data


def generate_markdown(slok_data, output_file):
    """
    Generate markdown file with bullet points for each slok.

    Args:
        slok_data: List of tuples (chapter_num, slok_num, rams_ht_text)
        output_file: Path to output markdown file
    """
    # Sort by chapter number, then slok number
    slok_data.sort(key=lambda x: (x[0], x[1]))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Bhagavad Gita - Swami Ramsukhdas Commentary\n\n")
        f.write("This document contains the Hindi translation and commentary by Swami Ramsukhdas.\n\n")
        f.write("---\n\n")

        current_chapter = None

        for chapter_num, slok_num, rams_ht in slok_data:
            # Add chapter header when we encounter a new chapter
            if current_chapter != chapter_num:
                current_chapter = chapter_num
                f.write(f"\n## Chapter {chapter_num}\n\n")

            # Write the slok as a bullet point
            f.write(f"- **{chapter_num}.{slok_num}** {rams_ht}\n")

    print(f"Successfully generated {output_file}")
    print(f"Total sloks processed: {len(slok_data)}")


def main():
    """Main function to orchestrate the script."""
    # Get the script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Define paths
    slok_dir = project_root / 'slok'
    output_file = project_root / 'bhagavad_gita_rams.md'

    print(f"Reading slok files from: {slok_dir}")
    print(f"Output will be written to: {output_file}")
    print("-" * 60)

    # Read all slok files
    slok_data = read_slok_files(slok_dir)

    if not slok_data:
        print("Error: No slok data found!")
        return

    # Generate markdown file
    generate_markdown(slok_data, output_file)

    print("-" * 60)
    print("Done!")


if __name__ == "__main__":
    main()

