import json

# Load the JSON file
with open('/Users/satyam/Downloads/llava_noaug_test.json', 'r') as f:
    data = json.load(f)

# Pretty-print the JSON to the notebook output
formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
    
json_data = json.loads(formatted_json)

print(len(json_data))

new_json_data = json_data[:5]

with open('/Users/satyam/Downloads/llava_noaug_test_formatted_5.json', 'w') as f:
    json.dump(new_json_data, f, indent=None, ensure_ascii=False)
