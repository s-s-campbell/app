# File that will parse the data from the GCS bucket and save it to BigQuery

import json
from bs4 import BeautifulSoup

def main():
    # Step 1: Read the data_example.json file and extract the data section
    with open('data_example.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Check if HTTP status is 200 before processing
    if data['http_status'] != 200:
        print(f"HTTP status is {data['http_status']}, not 200. Skipping data processing.")
        return
    
    # Extract the HTML data section from the JSON
    html_data = data['html']
    print("Successfully extracted HTML data section from JSON file")
    
    # Step 2: Use BeautifulSoup to get the outer tables
    soup = BeautifulSoup(html_data, 'html.parser')
    
    # Find all outer tables in the HTML
    outer_tables = soup.find_all('table')
    print(f"Found {len(outer_tables)} outer tables in the HTML data")
    
    # Filter and process only tables that have nested tables
    for i, table in enumerate(outer_tables):
        # Check if this table has any nested tables within it
        nested_tables = table.find_all('table')
        has_nested = len(nested_tables) > 0
        
        # Only process tables with nested tables
        if has_nested:
            print(f"\n{'='*60}")
            print(f"TABLE {i+1}: Processing table with {len(nested_tables)} nested tables")
            print(f"{'='*60}")
            
            # Print data of each nested table
            for j, nested_table in enumerate(nested_tables):
                nested_rows = len(nested_table.find_all('tr'))
                print(f"\n  NESTED TABLE {j+1} ({nested_rows} rows):")
                print(f"  {'-'*50}")
                
                # Extract and print the text content of the nested table
                nested_text = nested_table.get_text(strip=True, separator=' | ')
                print(f"  {nested_text}")
                print(f"  {'-'*50}")
        else:
            print(f"Table {i+1}: Skipping - no nested tables found")

if __name__ == "__main__":
    main()
