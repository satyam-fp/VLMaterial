import json

# Load the original backup JSON
with open('/workspace/VLMaterial/material_dataset_filtered/dataset_splits/llava_noaug_test.backup', 'r') as f:
    data = json.load(f)
# Get top 5 items
top5 = data[:2]
# Write to a new file
with open('/workspace/VLMaterial/material_dataset_filtered/dataset_splits/llava_noaug_test.json', 'w') as f:
    json.dump(top5, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(top5)} items.")
