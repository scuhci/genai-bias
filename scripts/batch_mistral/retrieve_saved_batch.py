import batch_utils

def main():
    # Hardcoded batch ID (you can also load from file if needed)
    batch_id = "80afda06-04f9-4dbe-a9ba-8ede992d2281"

    batch_utils.retrieve_results(batch_id)

if __name__ == "__main__":
    main()