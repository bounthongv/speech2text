import json
import os
from google.cloud import speech_v1p1beta1 as speech

class LaoMeetingPhrases:
    def __init__(self):
        self.phrases_file = 'meeting_phrases.json'
        self.categories = {
            'greetings': 'ການທັກທາຍ',
            'agenda': 'ວາລະ',
            'discussion': 'ການສົນທະນາ',
            'decisions': 'ການຕັດສິນໃຈ',
            'closing': 'ການປິດ',
            'custom': 'ກຳນົດເອງ'
        }
        self.phrases = self.load_phrases()

    def load_phrases(self):
        """Load phrases from JSON file or create default if not exists"""
        if os.path.exists(self.phrases_file):
            try:
                with open(self.phrases_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.get_default_phrases()
        return self.get_default_phrases()

    def get_default_phrases(self):
        """Return default Lao meeting phrases"""
        return {
            'greetings': [
                'ສະບາຍດີ',
                'ຂໍຂອບໃຈ',
                'ຍິນດີຕ້ອນຮັບ'
            ],
            'agenda': [
                'ວາລະການປະຊຸມ',
                'ຫົວຂໍ້ຕໍ່ໄປ',
                'ບັນຫາທີ່ຕ້ອງພິຈາລະນາ'
            ],
            'discussion': [
                'ຂໍ້ສະເໜີ',
                'ຄວາມຄິດເຫັນ',
                'ການສົນທະນາ'
            ],
            'decisions': [
                'ມະຕິທີ່ປະຊຸມ',
                'ຂໍ້ຕົກລົງ',
                'ການຕັດສິນໃຈ'
            ],
            'closing': [
                'ສະຫຼຸບ',
                'ປິດການປະຊຸມ',
                'ຂໍຂອບໃຈ'
            ],
            'custom': []
        }

    def save_phrases(self):
        """Save phrases to JSON file"""
        with open(self.phrases_file, 'w', encoding='utf-8') as f:
            json.dump(self.phrases, f, ensure_ascii=False, indent=2)

    def add_phrase(self, category, phrase):
        """Add a new phrase to a category"""
        if category in self.phrases:
            if phrase not in self.phrases[category]:
                self.phrases[category].append(phrase)
                self.save_phrases()
                return True
        return False

    def remove_phrase(self, category, phrase):
        """Remove a phrase from a category"""
        if category in self.phrases and phrase in self.phrases[category]:
            self.phrases[category].remove(phrase)
            self.save_phrases()
            return True
        return False

    def get_all_phrases(self):
        """Get all phrases as a flat list"""
        all_phrases = []
        for category in self.phrases:
            all_phrases.extend(self.phrases[category])
        return all_phrases

    def create_speech_config(self, base_config=None):
        """Create speech recognition config with phrase hints"""
        if base_config is None:
            base_config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="lo-LA",
                enable_automatic_punctuation=True,
                use_enhanced=True
            )

        # Get all phrases
        phrases = self.get_all_phrases()
        
        # Add speech adaptation configuration
        speech_contexts = [speech.SpeechContext(phrases=phrases)]
        
        # Create new config with speech adaptation
        config = speech.RecognitionConfig(
            encoding=base_config.encoding,
            sample_rate_hertz=base_config.sample_rate_hertz,
            language_code=base_config.language_code,
            enable_automatic_punctuation=base_config.enable_automatic_punctuation,
            use_enhanced=base_config.use_enhanced,
            speech_contexts=speech_contexts
        )
        
        return config

def main():
    """Interactive CLI for managing Lao meeting phrases"""
    phrases = LaoMeetingPhrases()
    
    while True:
        print("\nLao Meeting Phrases Manager")
        print("=" * 30)
        print("1. View all phrases")
        print("2. Add new phrase")
        print("3. Remove phrase")
        print("4. Export phrases")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            print("\nCurrent Phrases:")
            for category, cat_name in phrases.categories.items():
                print(f"\n{cat_name} ({category}):")
                for phrase in phrases.phrases[category]:
                    print(f"  - {phrase}")
        
        elif choice == '2':
            print("\nCategories:")
            for i, (category, cat_name) in enumerate(phrases.categories.items(), 1):
                print(f"{i}. {cat_name} ({category})")
            
            cat_choice = input("\nSelect category number: ")
            try:
                category = list(phrases.categories.keys())[int(cat_choice)-1]
                phrase = input("Enter new phrase: ")
                if phrases.add_phrase(category, phrase):
                    print("Phrase added successfully!")
                else:
                    print("Failed to add phrase (might be duplicate)")
            except:
                print("Invalid category selection")
        
        elif choice == '3':
            print("\nCurrent Phrases:")
            all_phrases = []
            for category, phrases_list in phrases.phrases.items():
                for phrase in phrases_list:
                    all_phrases.append((category, phrase))
                    print(f"{len(all_phrases)}. [{category}] {phrase}")
            
            try:
                idx = int(input("\nEnter number to remove: ")) - 1
                category, phrase = all_phrases[idx]
                if phrases.remove_phrase(category, phrase):
                    print("Phrase removed successfully!")
                else:
                    print("Failed to remove phrase")
            except:
                print("Invalid selection")
        
        elif choice == '4':
            phrases.save_phrases()
            print(f"\nPhrases exported to {phrases.phrases_file}")
        
        elif choice == '5':
            break
        
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
