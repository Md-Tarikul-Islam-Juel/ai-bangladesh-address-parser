import json
import re
from pathlib import Path

def tokenize(text):
    """
    Simple tokenizer that handles English and Bangla.
    Splits by whitespace and keeps punctuation as separate tokens.
    """
    # Pattern to match words (Bangla/English) or punctuation
    tokens = re.findall(r'[\u0980-\u09FF\w]+|[^\w\s]', text, re.UNICODE)
    return tokens

def prepare_ner_dataset(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ner_data = []

    for item in data:
        full_address = item['address']
        components = item['components']
        
        tokens = tokenize(full_address)
        labels = ['O'] * len(tokens)
        
        # Sort components by length descending to match longer strings first (e.g., "North Mirpur" before "Mirpur")
        sorted_keys = sorted(components.keys(), key=lambda k: len(str(components[k])), reverse=True)
        
        for key in sorted_keys:
            val = str(components[key]).strip()
            if not val:
                continue
                
            val_tokens = tokenize(val)
            if not val_tokens:
                continue
                
            # Find sequence of tokens in full_address tokens
            n = len(val_tokens)
            for i in range(len(tokens) - n + 1):
                if tokens[i:i+n] == val_tokens:
                    # Check if already labeled (avoid overwriting)
                    if all(l == 'O' for l in labels[i:i+n]):
                        labels[i] = f'B-{key.upper()}'
                        for j in range(i + 1, i + n):
                            labels[j] = f'I-{key.upper()}'
                        break # Only label the first occurrence for now to be safe
        
        ner_data.append({
            "id": item['id'],
            "tokens": tokens,
            "ner_tags": labels
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ner_data, f, ensure_ascii=False, indent=2)

    print(f"Successfully converted {len(ner_data)} records to BIO format.")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    input_path = 'Raw data/real-customer-address-dataset.json'
    output_path = 'Processed data/ner_training_data.json'
    
    # Ensure Processed data directory exists
    Path('Processed data').mkdir(exist_ok=True)
    
    prepare_ner_dataset(input_path, output_path)
