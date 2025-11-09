import json
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer

# --- Configuration ---
INPUT_FILENAME = 'all_xsd_data.json'
OUTPUT_FILENAME = 'generated_embeddings.json'
MODEL_NAME = 'all-MiniLM-L6-v2'

def load_data(filename: str) -> Dict:
    """Loads the structured XSD data from a JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Input file '{filename}' not found.")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{filename}'.")
        return {}
    except Exception as e:
        print(f"❌ An unexpected error occurred while loading the file: {e}")
        return {}

def extract_prompts(data: Dict) -> Tuple[Dict[str, str], List[str]]:
    """
    Traverses the nested XSD data, creates a unique key and an embedding prompt 
    for every element that has documentation.
    
    Returns: (mapping of unique_key -> prompt, list of all prompts)
    """
    key_to_prompt_map: Dict[str, str] = {}
    all_prompts: List[str] = []
    
    for filename, file_data in data.items():
        # Ensure we are dealing with a valid file structure that has an 'elements' list
        elements = file_data.get('elements', [])
        
        for element in elements:
            name = element.get('name')
            documentation = element.get('documentation')
            
            # We only generate an embedding if we have both a name and documentation
            if name and documentation:
                # 1. Create a unique key for the output JSON
                unique_key = f"{filename}/{name}"
                
                # 2. Create a comprehensive prompt for the model
                prompt = (
                    f"XSD File: {filename}. Element Name: {name}. "
                    f"Function/Documentation: {documentation}"
                )
                
                key_to_prompt_map[unique_key] = prompt
                all_prompts.append(prompt)
                
    return key_to_prompt_map, all_prompts

def generate_and_save_embeddings(data: Dict):
    """
    Main function to generate embeddings using SentenceTransformer and save the result.
    """
    key_to_prompt_map, prompts_list = extract_prompts(data)
    
    if not prompts_list:
        print("⚠️ No elements with documentation found to generate embeddings.")
        return

    print(f"--- Loading SentenceTransformer model: {MODEL_NAME} ---")
    try:
        # Load the pre-trained model
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"❌ Error loading model. Details: {e}")
        return

    print(f"\nStarting batch embedding generation for {len(prompts_list)} elements...")
    
    # Generate embeddings in a single batch (highly efficient)
    # convert_to_numpy=True is the default, normalize_embeddings=True is good for search
    embeddings = model.encode(prompts_list, normalize_embeddings=True)
    
    print("Generation complete. Mapping vectors to element keys.")

    # Convert the list of keys and the array of vectors into the final dictionary
    generated_embeddings: Dict[str, List[float]] = {}
    
    # Match the order of prompts to the order of embeddings
    unique_keys = list(key_to_prompt_map.keys())
    
    for i, key in enumerate(unique_keys):
        # Convert numpy array vector to standard Python list for JSON serialization
        generated_embeddings[key] = embeddings[i].tolist()
        
    # Save the final dictionary to a JSON file
    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(generated_embeddings, f, indent=4)
        
        print(f"\n✅ Successfully generated {len(generated_embeddings)} embeddings.")
        print(f"   Embeddings saved to '{OUTPUT_FILENAME}'.")
        print(f"   Each vector has a dimension of {len(embeddings[0])}.")
    
    except IOError as e:
        print(f"❌ Error saving file: {e}")


if __name__ == "__main__":
    # 1. Load the data
    xsd_data = load_data(INPUT_FILENAME)
    
    # 2. Generate and save embeddings
    if xsd_data:
        generate_and_save_embeddings(xsd_data)