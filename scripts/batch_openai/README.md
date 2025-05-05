# How to Generate Profiles


### Before you begin:
Ensure you set the `apikey` in `batch_utils.py`, `check_batch.py`, `retrieve_save_batch.py`, and `submit_batch.py`.

Specify career list in `submit_batch.py`. You may also want to change `batch_fname` to your preferred naming convention.

### To submit a batch job:
```
python submit_batch.py
```
### To check the status of a batch job (will print batch status and metadata):
```
python check_batch.py
```
### Retrieve a batch
Once a batch is marked as completed, you can retrieve it. This will write a jsonl file to `profiles/openai/jsonls`. 
```
python retrieve_save_batch.py
```
### Convert to CSV

Change the `jsonl_file` variable in `jsonl_to_csv.py` to the filename of the jsonl you wrote to `profiles/openai/jsonls`. You can then run the following script to write all results to CSVs.
```
python jsonl_to_csv.py
```