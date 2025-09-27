"""
Lightweight Phrase Dictionary - Fallback version without external dependencies
This version provides basic functionality when optional packages are not available
"""
import json
import os
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

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
    
    def simple_distance(self, s1: str, s2: str) -> int:
        """Simple Levenshtein distance implementation (fallback)"""
        if len(s1) < len(s2):
            return self.simple_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def find_closest_match(self, phrase: str, category: str = None) -> Tuple[Optional[str], float]:
        """Find the closest matching phrase in the dictionary"""
        min_distance = float('inf')
        best_match = None
        
        categories_to_search = [category] if category else self.categories.keys()
        
        for cat in categories_to_search:
            if cat not in self.categories:
                continue
                
            for dict_phrase in self.categories[cat]:
                # Calculate simple distance
                dist = self.simple_distance(phrase.lower(), dict_phrase.lower())
                
                # Update best match if this distance is smaller
                if dist < min_distance:
                    min_distance = dist
                    best_match = dict_phrase
                
                # Also check alternatives
                for alt in self.categories[cat][dict_phrase]:
                    dist = self.simple_distance(phrase.lower(), alt.lower())
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