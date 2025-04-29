import csv
import re

with open('Maid_Housekeepers_openai.csv', 'r', newline='', encoding='utf-8') as infile, \
     open('Maid_Housekeepers_openai1.csv', 'w', newline='', encoding='utf-8') as outfile:

    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    header = next(reader)
    writer.writerow(header)

    salary_index = header.index("Salary")

    for row in reader:
        new_row = []
        for i, cell in enumerate(row):
            if i == salary_index:
                # Remove $ and commas, but keep digits and decimal
                cleaned = re.sub(r"[$,]", "", cell)
                # Optionally remove ".00" if present
                if cleaned.endswith(".00"):
                    cleaned = cleaned[:-3]
            else:
                cleaned = cell
            new_row.append(cleaned)
        writer.writerow(new_row)
