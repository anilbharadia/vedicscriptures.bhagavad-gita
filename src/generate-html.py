#!/usr/bin/env python3
"""
Generate interactive HTML page from Bhagavad Gita slok JSON files.
Extracts 'rams.ht' field from each slok and creates a chat-like interface.
Messages from श्रीभगवान् are hidden by default and can be expanded by clicking.
"""

import json
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
    Read all slok JSON files and extract rams.ht field and speaker.

    Args:
        slok_dir: Path to the directory containing slok JSON files

    Returns:
        List of tuples: (chapter_num, slok_num, rams_ht_text, speaker)
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

            # Extract rams.ht field and speaker
            if 'rams' in data and 'ht' in data['rams']:
                rams_ht = data['rams']['ht']
                speaker = data.get('speaker', None)  # Extract speaker, default to None if not present
                slok_data.append((chapter_num, slok_num, rams_ht, speaker))
            else:
                print(f"Warning: 'rams.ht' not found in {json_file.name}")

        except json.JSONDecodeError as e:
            print(f"Error reading {json_file.name}: {e}")
        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")

    return slok_data


def generate_html(slok_data, output_file):
    """
    Generate interactive HTML page with chat-like interface for each slok.
    Messages from श्रीभगवान् are hidden by default and expandable.

    Args:
        slok_data: List of tuples (chapter_num, slok_num, rams_ht_text, speaker)
        output_file: Path to output HTML file
    """
    # Sort by chapter number, then slok number
    slok_data.sort(key=lambda x: (x[0], x[1]))

    with open(output_file, 'w', encoding='utf-8') as f:
        # Write HTML header
        f.write("""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>भगवद गीता - स्वामी रामसुखदास जी की व्याख्या</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .chat-container {
            padding: 30px;
            background: #f5f5f5;
            min-height: 500px;
        }

        .chapter-header {
            text-align: center;
            margin: 30px 0 20px 0;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            font-size: 1.3em;
            font-weight: bold;
        }

        .message {
            margin: 15px 0;
            animation: fadeIn 0.3s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message-content {
            display: inline-block;
            max-width: 75%;
            padding: 15px 20px;
            border-radius: 18px;
            line-height: 1.6;
            font-size: 1.05em;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .verse-number {
            font-weight: bold;
            font-size: 0.9em;
            opacity: 0.7;
            margin-bottom: 5px;
            display: block;
        }

        /* अर्जुन (Arjuna) - Left aligned, orange */
        .arjuna {
            text-align: left;
        }

        .arjuna .message-content {
            background: linear-gradient(135deg, #FF9966 0%, #FF5E62 100%);
            color: white;
            border-bottom-left-radius: 5px;
        }

        /* श्रीभगवान् (Bhagavan) - Right aligned, blue */
        .bhagavan {
            text-align: right;
        }

        .bhagavan .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .bhagavan .message-content:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        .bhagavan .message-content.hidden {
            background: linear-gradient(135deg, #a8b5ea 0%, #b89fd2 100%);
            opacity: 0.6;
        }

        .bhagavan .message-text {
            display: block;
        }

        .bhagavan .message-text.hidden {
            display: none;
        }

        .bhagavan .placeholder {
            display: none;
            font-style: italic;
            opacity: 0.9;
        }

        .bhagavan .placeholder.show {
            display: block;
        }

        .click-hint {
            font-size: 0.85em;
            opacity: 0.8;
            margin-top: 5px;
            font-style: italic;
        }

        /* सञ्जय and धृतराष्ट्र (Narrator) - Centered, grey */
        .narrator {
            text-align: center;
        }

        .narrator .message-content {
            background: linear-gradient(135deg, #bdc3c7 0%, #95a5a6 100%);
            color: white;
            border-radius: 18px;
            font-style: italic;
        }

        /* Other speakers - Left aligned, default */
        .other {
            text-align: left;
        }

        .other .message-content {
            background: #e8e8e8;
            color: #333;
            border-bottom-left-radius: 5px;
        }

        .footer {
            background: #333;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }

        .legend {
            background: white;
            padding: 20px;
            margin: 0 30px 20px 30px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .legend h3 {
            margin-bottom: 15px;
            color: #333;
        }

        .legend-item {
            display: inline-block;
            margin: 5px 15px 5px 0;
            font-size: 0.95em;
        }

        .legend-color {
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>श्रीमद् भगवद्गीता</h1>
            <p>स्वामी रामसुखदास जी की व्याख्या के साथ</p>
        </div>

        <div class="legend">
            <h3>संवाद सहभागी (Conversation Participants):</h3>
            <div class="legend-item">
                <span class="legend-color" style="background: linear-gradient(135deg, #FF9966 0%, #FF5E62 100%);"></span>
                अर्जुन (Arjuna)
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"></span>
                श्रीभगवान् (Lord Krishna) - <em>Click to reveal</em>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: linear-gradient(135deg, #bdc3c7 0%, #95a5a6 100%);"></span>
                सञ्जय / धृतराष्ट्र (Narrator)
            </div>
        </div>

        <div class="chat-container">
""")

        current_chapter = None

        for chapter_num, slok_num, rams_ht, speaker in slok_data:
            # Add chapter header when we encounter a new chapter
            if current_chapter != chapter_num:
                current_chapter = chapter_num
                f.write(f'            <div class="chapter-header">अध्याय {chapter_num}</div>\n')

            # Determine message class based on speaker
            if speaker == "अर्जुन":
                msg_class = "arjuna"
                f.write(f'            <div class="message {msg_class}">\n')
                f.write(f'                <div class="message-content">\n')
                f.write(f'                    <span class="verse-number">{chapter_num}.{slok_num}</span>\n')
                f.write(f'                    {rams_ht}\n')
                f.write(f'                </div>\n')
                f.write(f'            </div>\n')

            elif speaker == "श्रीभगवान्":
                msg_class = "bhagavan"
                f.write(f'            <div class="message {msg_class}">\n')
                f.write(f'                <div class="message-content hidden" onclick="this.classList.toggle(\'hidden\'); this.querySelector(\'.message-text\').classList.toggle(\'hidden\'); this.querySelector(\'.placeholder\').classList.toggle(\'show\');">\n')
                f.write(f'                    <span class="verse-number">{chapter_num}.{slok_num}</span>\n')
                f.write(f'                    <span class="placeholder show">श्रीभगवान् का उत्तर देखने के लिए क्लिक करें... 🙏</span>\n')
                f.write(f'                    <span class="message-text hidden">{rams_ht}</span>\n')
                f.write(f'                </div>\n')
                f.write(f'            </div>\n')

            elif speaker == "सञ्जय" or speaker == "धृतराष्ट्र":
                msg_class = "narrator"
                f.write(f'            <div class="message {msg_class}">\n')
                f.write(f'                <div class="message-content">\n')
                f.write(f'                    <span class="verse-number">{speaker} - {chapter_num}.{slok_num}</span>\n')
                f.write(f'                    {rams_ht}\n')
                f.write(f'                </div>\n')
                f.write(f'            </div>\n')

            else:
                msg_class = "other"
                speaker_name = speaker if speaker else "अन्य"
                f.write(f'            <div class="message {msg_class}">\n')
                f.write(f'                <div class="message-content">\n')
                f.write(f'                    <span class="verse-number">{speaker_name} - {chapter_num}.{slok_num}</span>\n')
                f.write(f'                    {rams_ht}\n')
                f.write(f'                </div>\n')
                f.write(f'            </div>\n')

        # Write HTML footer
        f.write("""        </div>

        <div class="footer">
            <p>श्रीमद् भगवद्गीता - स्वामी रामसुखदास जी की व्याख्या</p>
            <p style="margin-top: 10px; font-size: 0.85em;">Total Verses: """ + str(len(slok_data)) + """</p>
        </div>
    </div>

    <script>
        // Optional: Add keyboard shortcut to reveal all hidden messages
        document.addEventListener('keydown', function(e) {
            if (e.key === 'r' && e.ctrlKey) {
                e.preventDefault();
                document.querySelectorAll('.bhagavan .message-content.hidden').forEach(el => {
                    el.classList.remove('hidden');
                    el.querySelector('.message-text').classList.remove('hidden');
                    el.querySelector('.placeholder').classList.remove('show');
                });
            }
        });
    </script>
</body>
</html>
""")

    print(f"Successfully generated {output_file}")
    print(f"Total sloks processed: {len(slok_data)}")



def main():
    """Main function to orchestrate the script."""
    # Get the script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Define paths
    slok_dir = project_root / 'slok'
    output_file = project_root / 'bhagavad_gita_rams.html'

    print(f"Reading slok files from: {slok_dir}")
    print(f"Output will be written to: {output_file}")
    print("-" * 60)

    # Read all slok files
    slok_data = read_slok_files(slok_dir)

    if not slok_data:
        print("Error: No slok data found!")
        return

    # Generate HTML file
    generate_html(slok_data, output_file)

    print("-" * 60)
    print("Done!")
    print(f"\nOpen {output_file} in your web browser to view the interactive Bhagavad Gita!")



if __name__ == "__main__":
    main()

