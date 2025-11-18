#!/usr/bin/env python3
"""
Generate interactive HTML page from Bhagavad Gita slok JSON files.
Extracts 'rams.ht' field from each slok and creates a chat-like interface.
Groups consecutive verses with identical (normalized) or highly similar text.
Strips leading verse prefix markers like '।।2.69।।' or '।।3.1 -- 3.2।।' from displayed commentary text.
"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher


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


def strip_verse_prefix(text: str) -> str:
    """Remove leading verse number prefix patterns of form:
    ।।<chapter>.<verse>।। or ।।<chapter>.<verse> -- <chapter>.<verse>।।
    Allow optional spaces. Return cleaned text.
    """
    if not text:
        return ''
    pattern = r'^।।\s*\d+\.\d+(?:\s*(?:--|[-–—])\s*\d+\.\d+)?।।\s*'
    return re.sub(pattern, '', text.strip())


def normalize_text(text: str) -> str:
    """Return a normalized version of commentary text for comparison.
    - Trim
    - Collapse all whitespace to single spaces
    - Remove spaces before common punctuation (Hindi danda '।', ! ? , ; :)
    """
    if text is None:
        return ''
    # Strip verse prefix before normalization so comparisons ignore it
    text = strip_verse_prefix(text)
    s = text.strip()
    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s)
    # Remove space before punctuation marks
    s = re.sub(r'\s+([!?,।;:])', r'\1', s)
    return s


def strip_for_tokens(text: str) -> str:
    """Lowercase and remove punctuation for token comparison."""
    if text is None:
        return ''
    t = normalize_text(text)
    t = re.sub(r'[!?,।;:\-–—]|\[|\]|"|\(|\)|\/', ' ', t)
    t = re.sub(r'\s+', ' ', t).lower()
    return t


def are_texts_equivalent(a: str, b: str) -> bool:
    """Return True if two texts are considered equivalent for grouping.
    Criteria:
      1. Exact normalized match
      2. High similarity ratio (>0.965) via SequenceMatcher
      3. Token symmetric difference very small (<=2 tokens diff) and length diff <=3
    """
    na = normalize_text(a)
    nb = normalize_text(b)
    if na == nb:
        return True
    ratio = SequenceMatcher(None, na, nb).ratio()
    if ratio > 0.965:
        return True
    ta = strip_for_tokens(a).split()
    tb = strip_for_tokens(b).split()
    set_a = set(ta)
    set_b = set(tb)
    sym_diff = (set_a - set_b) | (set_b - set_a)
    if len(sym_diff) <= 2 and abs(len(ta) - len(tb)) <= 3:
        return True
    return False


def group_sloks(slok_data):
    """Group consecutive sloks within a chapter where normalized rams_ht and speaker are identical.

    Args:
        slok_data: list of tuples (chapter, verse, text, speaker) sorted by (chapter, verse)

    Returns:
        list of tuples (chapter, start_verse, end_verse, text, speaker)
    """
    if not slok_data:
        return []
    grouped = []
    i = 0
    n = len(slok_data)
    while i < n:
        chap, verse, text, speaker = slok_data[i]
        start_verse = verse
        end_verse = verse
        j = i + 1
        while j < n:
            chap_j, verse_j, text_j, speaker_j = slok_data[j]
            if chap_j == chap and verse_j == end_verse + 1 and speaker_j == speaker and are_texts_equivalent(text, text_j):
                end_verse = verse_j
                j += 1
            else:
                break
        grouped.append((chap, start_verse, end_verse, text, speaker))
        i = j
    # Debug: report first few multi-verse groups
    multi = [g for g in grouped if g[1] != g[2]]
    if multi:
        print(f"Found {len(multi)} multi-verse grouped messages. Examples:")
        for example in multi[:8]:
            print(f"  Chapter {example[0]} verses {example[1]}-{example[2]} speaker={example[4]}")
    return grouped


def generate_html(slok_data, output_file):
    """
    Generate interactive HTML page with chat-like interface for each slok.
    Groups consecutive identical-text verses into a single message with a range label.

    Args:
        slok_data: List of tuples (chapter_num, slok_num, rams_ht_text, speaker)
        output_file: Path to output HTML file
    """
    # Sort by chapter number, then slok number
    slok_data.sort(key=lambda x: (x[0], x[1]))
    grouped_sloks = group_sloks(slok_data)
    print(f"Original verses: {len(slok_data)} | Grouped messages: {len(grouped_sloks)}")

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

        .chapter-header { cursor: pointer; position: relative; user-select: none; }
        .chapter-header .triangle { font-weight: bold; margin-right: 8px; display: inline-block; width: 1em; }
        .chapter-block.collapsed .chapter-content { display: none; }
        .chapter-block.expanded .chapter-content { display: block; }
        .chapter-block { margin-bottom: 10px; border: 1px solid #ddd; border-radius: 10px; overflow: hidden; background: #ffffff; }
        .chapter-block .chapter-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; padding: 12px 16px; font-size: 1.1em; }
        .chapter-content { padding: 10px 25px 25px 25px; background: #f5f5f5; }
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
                श्रीभगवान् (Lord Krishna)
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: linear-gradient(135deg, #bdc3c7 0%, #95a5a6 100%);"></span>
                सञ्जय / धृतराष्ट्र (Narrator)
            </div>
        </div>

        <div class="chat-container">
""")

        current_chapter = None
        # Track if a chapter block is open
        open_block = False

        for chap, start_v, end_v, text, speaker in grouped_sloks:
            if current_chapter != chap:
                # Close previous chapter block if open
                if open_block:
                    f.write("                </div>\n            </div>\n")  # close chapter-content and chapter-block
                    open_block = False
                current_chapter = chap
                # Start new chapter block (collapsed by default)
                f.write(f"            <div class=\"chapter-block collapsed\" data-chapter=\"{chap}\">\n")
                f.write(f"                <div class=\"chapter-header\" onclick=\"toggleChapter(this)\"><span class=\"triangle\">►</span> अध्याय {chap}</div>\n")
                f.write("                <div class=\"chapter-content\">\n")
                open_block = True

            # Compose verse label
            verse_label = f"{chap}.{start_v}" if start_v == end_v else f"{chap}.{start_v} - {chap}.{end_v}"
            cleaned = strip_verse_prefix(text)

            if speaker == "अर्जुन":
                f.write('                    <div class="message arjuna">\n')
                f.write('                        <div class="message-content">\n')
                f.write(f'                            <span class="verse-number">{verse_label}</span>\n')
                f.write(f'                            {cleaned}\n')
                f.write('                        </div>\n')
                f.write('                    </div>\n')

            elif speaker == "श्रीभगवान्":
                f.write('                    <div class="message bhagavan">\n')
                f.write('                        <div class="message-content">\n')
                f.write(f'                            <span class="verse-number">{verse_label}</span>\n')
                f.write(f'                            {cleaned}\n')
                f.write('                        </div>\n')
                f.write('                    </div>\n')

            elif speaker == "सञ्जय" or speaker == "धृतराष्ट्र":
                f.write('                    <div class="message narrator">\n')
                f.write('                        <div class="message-content">\n')
                f.write(f'                            <span class="verse-number">{speaker} - {verse_label}</span>\n')
                f.write(f'                            {cleaned}\n')
                f.write('                        </div>\n')
                f.write('                    </div>\n')

            else:
                speaker_name = speaker if speaker else "अन्य"
                f.write('                    <div class="message other">\n')
                f.write('                        <div class="message-content">\n')
                f.write(f'                            <span class="verse-number">{speaker_name} - {verse_label}</span>\n')
                f.write(f'                            {cleaned}\n')
                f.write('                        </div>\n')
                f.write('                    </div>\n')

        # Close any open chapter block
        if open_block:
            f.write("                </div>\n            </div>\n")

        f.write("""        </div>
        <div class="footer">
            <p>श्रीमद् भगवद्गीता - स्वामी रामसुखदास जी की व्याख्या</p>
            <p style="margin-top: 10px; font-size: 0.85em;">Total Verses: """ + str(len(slok_data)) + """ | Messages Displayed: """ + str(len(grouped_sloks)) + """</p>
        </div>
    </div>
    <script>
        function toggleChapter(header){
            const block = header.parentElement;
            const content = block.querySelector('.chapter-content');
            const tri = header.querySelector('.triangle');
            const collapsed = block.classList.contains('collapsed');
            if(collapsed){
                block.classList.remove('collapsed');
                block.classList.add('expanded');
                content.style.display='block';
                tri.textContent='▼';
            } else {
                block.classList.add('collapsed');
                block.classList.remove('expanded');
                content.style.display='none';
                tri.textContent='►';
            }
        }
        // Keyboard shortcut: Ctrl+Shift+E expand all, Ctrl+Shift+C collapse all
        document.addEventListener('keydown', function(e){
            if(e.ctrlKey && e.shiftKey && e.key.toLowerCase()==='e'){
                document.querySelectorAll('.chapter-block.collapsed').forEach(b=>{
                    b.classList.remove('collapsed'); b.classList.add('expanded');
                    b.querySelector('.chapter-content').style.display='block';
                    b.querySelector('.triangle').textContent='▼';
                });
            }
            if(e.ctrlKey && e.shiftKey && e.key.toLowerCase()==='c'){
                document.querySelectorAll('.chapter-block.expanded').forEach(b=>{
                    b.classList.add('collapsed'); b.classList.remove('expanded');
                    b.querySelector('.chapter-content').style.display='none';
                    b.querySelector('.triangle').textContent='►';
                });
            }
        });
    </script>
</body>
</html>
""")

    print(f"Successfully generated {output_file}")
    print(f"Total sloks processed: {len(slok_data)} | Messages displayed: {len(grouped_sloks)}")


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
