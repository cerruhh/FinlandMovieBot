import json

def clean_json_file(input_file: str, output_file: str) -> None:
    """
    Removes entries with TomatoYear = "NA" from a JSON file.

    Args:
        input_file: Path to the input JSON file
        output_file: Path to save the cleaned JSON file
    """
    try:
        # Read the JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)

        # Filter out entries with TomatoYear = "NA"
        cleaned_data = {
            title: details for title, details in data.items()
            if details.get('TomatoYear') != "NA"
        }

        # Write cleaned data to new file
        with open(output_file, 'w') as f:
            json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

        print(f"Cleaned data saved to {output_file}")

    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {input_file}")


# Usage
clean_json_file('Data/tomato.json', 'Data/tomato_clean.json')