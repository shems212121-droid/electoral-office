
import json
import glob
import os

batch_dir = "voter_batches"
print("Batch File | Last PK")
print("-" * 30)

files = sorted(glob.glob(os.path.join(batch_dir, "voters_batch_*.json")))

batch_info = {}

for filename in files:
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if data:
            last_item = data[-1]
            last_pk = last_item['pk']
            fname = os.path.basename(filename)
            print(f"{fname} | {last_pk}")
            batch_info[fname] = last_pk

print("\nPYTHON DICT:")
print(json.dumps(batch_info, indent=4))
