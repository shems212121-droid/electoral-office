
import json
import glob
import os

target_voter = "33037821"
batch_dir = "voter_batches"

print(f"Searching for voter {target_voter} in {batch_dir}...")

for filename in glob.glob(os.path.join(batch_dir, "voters_batch_*.json")):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            if item['model'] == 'elections.voter':
                if item['fields'].get('voter_number') == target_voter:
                    print(f"FOUND in file: {filename}")
                    # Print details
                    print(json.dumps(item, indent=2, ensure_ascii=False))
                    break
