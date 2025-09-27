import requests
from bs4 import BeautifulSoup
import re
from collections import Counter

# Lao news website (Change this URL to other sources)
URL = "https://laotiantimes.com/"  # Example Lao news website

def get_lao_text(url):
    """Scrape text from a Lao news website"""
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to fetch the website.")
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text() for p in paragraphs)

    # Keep only Lao words
    lao_words = re.findall(r"[\u0E80-\u0EFF]+", text)
    return lao_words

def update_lao_dictionary(word_list, dict_file="lao_words.txt"):
    """Update Lao word dictionary with new words"""
    try:
        with open(dict_file, "r", encoding="utf-8") as f:
            existing_words = {line.split()[0]: int(line.split()[1]) for line in f.readlines()}
    except FileNotFoundError:
        existing_words = {}

    # Count new words
    new_counts = Counter(word_list)

    # Merge with existing words
    for word, count in new_counts.items():
        existing_words[word] = existing_words.get(word, 0) + count

    # Save updated dictionary
    with open(dict_file, "w", encoding="utf-8") as f:
        for word, freq in sorted(existing_words.items(), key=lambda x: -x[1]):
            f.write(f"{word} {freq}\n")

    print(f"Updated {dict_file} with {len(new_counts)} new words.")

# Run the script
lao_words = get_lao_text(URL)
if lao_words:
    update_lao_dictionary(lao_words)
