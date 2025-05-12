import json
import os

def convert_to_jsonl(input_file, output_file):
    """
    Convert training data from JSON format to JSONL format for OpenAI fine-tuning.
    """
    try:
        # Load the JSON data
        with open(input_file, 'r') as infile:
            data = json.load(infile)

        # Open the output file in write mode
        with open(output_file, 'w') as outfile:
            for entry in data:
                # Extract the title and description
                prompt = entry.get('title', '').strip()
                completion = entry.get('description', '').strip()

                # Skip entries with missing fields
                if not prompt or not completion:
                    continue

                # Write to JSONL format
                json.dump({"prompt": prompt, "completion": completion}, outfile)
                outfile.write('\n')

        print(f"Conversion successful! JSONL file saved at: {output_file}")

    except Exception as e:
        print(f"Error during conversion: {e}")

if __name__ == "__main__":
    # Define input and output paths
    input_path = os.path.join(os.path.dirname(__file__), '../data/training_data.json')
    output_path = os.path.join(os.path.dirname(__file__), '../data/training_data.jsonl')

    # Perform the conversion
    convert_to_jsonl(input_path, output_path)
