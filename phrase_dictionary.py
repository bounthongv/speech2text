import json
import os
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
from Levenshtein import distance
from symspellpy import SymSpell, Verbosity

logger = logging.getLogger(__name__)

class PhraseDictionary:
    def __init__(self, dictionary_file: str = "phrase_dictionary.json"):
        self.dictionary_file = dictionary_file
        self.categories = {
            "general": {},
            "technical": {},
            "names": {},
            "acronyms": {}
        }
        self.frequency = {}
        self.sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        self.load_dictionary()
        
    def load_dictionary(self):
        """Load the dictionary from file if it exists"""
        if os.path.exists(self.dictionary_file):
            try:
                with open(self.dictionary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.categories = data.get('categories', self.categories)
                    self.frequency = data.get('frequency', {})
            except Exception as e:
                logger.error(f"Error loading dictionary: {str(e)}")
    
    def save_dictionary(self):
        """Save the dictionary to file"""
        try:
            with open(self.dictionary_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'categories': self.categories,
                    'frequency': self.frequency,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving dictionary: {str(e)}")
    
    def add_phrase(self, phrase: str, category: str = "general", alternatives: List[str] = None):
        """Add a phrase to the dictionary"""
        if category not in self.categories:
            raise ValueError(f"Invalid category: {category}")
        
        self.categories[category][phrase] = alternatives or []
        self.frequency[phrase] = self.frequency.get(phrase, 0)
        self.save_dictionary()
    
    def remove_phrase(self, phrase: str, category: str = None):
        """Remove a phrase from the dictionary"""
        if category:
            if category in self.categories and phrase in self.categories[category]:
                del self.categories[category][phrase]
        else:
            for cat in self.categories:
                if phrase in self.categories[cat]:
                    del self.categories[cat][phrase]
        
        if phrase in self.frequency:
            del self.frequency[phrase]
        
        self.save_dictionary()
    
    def find_closest_match(self, phrase: str, category: str = None) -> Tuple[Optional[str], float]:
        """Find the closest matching phrase in the dictionary"""
        min_distance = float('inf')
        best_match = None
        
        categories_to_search = [category] if category else self.categories.keys()
        
        for cat in categories_to_search:
            if cat not in self.categories:
                continue
                
            for dict_phrase in self.categories[cat]:
                # Calculate Levenshtein distance
                dist = distance(phrase.lower(), dict_phrase.lower())
                
                # Update best match if this distance is smaller
                if dist < min_distance:
                    min_distance = dist
                    best_match = dict_phrase
                
                # Also check alternatives
                for alt in self.categories[cat][dict_phrase]:
                    dist = distance(phrase.lower(), alt.lower())
                    if dist < min_distance:
                        min_distance = dist
                        best_match = dict_phrase
        
        if best_match:
            # Convert distance to similarity score (0 to 1)
            max_len = max(len(phrase), len(best_match))
            similarity = 1 - (min_distance / max_len if max_len > 0 else 0)
            return best_match, similarity
        
        return None, 0.0
    
    def update_frequency(self, phrase: str):
        """Update the usage frequency of a phrase"""
        if phrase in self.frequency:
            self.frequency[phrase] += 1
            self.save_dictionary()
    
    def get_alternatives(self, phrase: str, category: str = None) -> List[str]:
        """Get alternative spellings/forms of a phrase"""
        if category and category in self.categories:
            return self.categories[category].get(phrase, [])
        
        for cat in self.categories:
            if phrase in self.categories[cat]:
                return self.categories[cat][phrase]
        
        return []
    
    def get_frequent_phrases(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get the most frequently used phrases"""
        return sorted(self.frequency.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def correct_text(self, text: str, min_similarity: float = 0.8) -> Tuple[str, List[Tuple[str, str, float]]]:
        """Correct text using the phrase dictionary"""
        words = text.split()
        corrections = []
        corrected_words = []
        
        for word in words:
            match, similarity = self.find_closest_match(word)
            
            if match and similarity >= min_similarity:
                corrections.append((word, match, similarity))
                corrected_words.append(match)
                self.update_frequency(match)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections

def main():
    """Test the phrase dictionary functionality"""
    pd = PhraseDictionary()
    
    # Add some example phrases
    example_phrases = {
        'general': [
            'action item',
            'follow up',
            'next steps',
            'any other business'
        ],
        'technical': [
            'API endpoint',
            'database schema',
            'pull request',
            'deployment pipeline'
        ],
        'names': [
            'John Smith',
            'Sarah Johnson',
            'Tech Solutions Inc.',
            'Development Team'
        ],
        'acronyms': [
            'ASAP',
            'ROI',
            'API',
            'MVP'
        ]
    }
    
    print("Adding example phrases...")
    for category, phrases in example_phrases.items():
        for phrase in phrases:
            try:
                pd.add_phrase(phrase, category)
                print(f"Added: {phrase} ({category})")
            except Exception as e:
                print(f"Error adding {phrase}: {e}")
    
    # Test correction
    test_texts = [
        "We need to check the api endpont",
        "Please follow-up with jon smith",
        "The roi calculation is pending",
        "Let's discuss the next step"
    ]
    
    print("\nTesting text correction:")
    for text in test_texts:
        corrected, corrections = pd.correct_text(text)
        print(f"\nOriginal: {text}")
        print(f"Corrected: {corrected}")
        print(f"Corrections: {corrections}")
    
    print(f"\nDictionary saved to: {pd.dictionary_file}")

if __name__ == "__main__":
    main() 