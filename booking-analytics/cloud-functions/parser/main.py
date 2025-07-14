# File that will parse the data from the GCS bucket and save it to BigQuery

import json
from bs4 import BeautifulSoup

# Constants for table positioning (0-based indexing)
TARGET_OUTER_TABLE_INDEX = 0  # Outer table 1 (0-based)
TARGET_NESTED_TABLE_INDEX = 1  # Nested table 2 (0-based)

def load_color_mapping():
    """Load color mapping from booking_colour_map.txt file."""
    color_map = {}
    with open('booking_colour_map.txt', 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):  # Skip empty lines and comments
                key, value = line.split('=')
                color_map[value] = key.replace('_COLOR', '').lower()
    return color_map

def load_and_validate_json_data():
    """Load JSON data and validate HTTP status."""
    with open('data_example.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Check if HTTP status is 200 before processing
    if data['http_status'] != 200:
        print(f"HTTP status is {data['http_status']}, not 200. Skipping data processing.")
        return None
    
    print("Successfully extracted HTML data section from JSON file")
    return data['html']

def extract_target_table(html_data):
    """Extract the specific target table using constants."""
    soup = BeautifulSoup(html_data, 'html.parser')
    outer_tables = soup.find_all('table')
    print(f"Found {len(outer_tables)} outer tables in the HTML data")
    
    # Access the specific target table using constants
    if len(outer_tables) > TARGET_OUTER_TABLE_INDEX:
        target_outer_table = outer_tables[TARGET_OUTER_TABLE_INDEX]
        nested_tables = target_outer_table.find_all('table')
        
        if len(nested_tables) > TARGET_NESTED_TABLE_INDEX:
            target_nested_table = nested_tables[TARGET_NESTED_TABLE_INDEX]
            table_rows = target_nested_table.find_all('tr')
            
            print(f"\n{'='*60}")
            print(f"PROCESSING TARGET TABLE:")
            print(f"Outer table index: {TARGET_OUTER_TABLE_INDEX + 1}")
            print(f"Nested table index: {TARGET_NESTED_TABLE_INDEX + 1}")
            print(f"Rows in target nested table: {len(table_rows)}")
            print(f"{'='*60}")
            
            return table_rows
        else:
            print(f"Error: Nested table index {TARGET_NESTED_TABLE_INDEX + 1} not found in outer table {TARGET_OUTER_TABLE_INDEX + 1}")
            return None
    else:
        print(f"Error: Outer table index {TARGET_OUTER_TABLE_INDEX + 1} not found")
        return None

def extract_headers(table_rows):
    """Extract headers from the first table row."""
    if len(table_rows) == 0:
        return []
    
    first_row = table_rows[0]
    headers = []
    for td in first_row.find_all('td'):
        header_text = td.get_text(strip=True)
        headers.append(header_text)
    
    print(f"\nHEADERS STORED:")
    print(f"Headers: {headers}")
    return headers

def create_time_bgcolor_map(table_rows):
    """Create map from time slots to status values using color mapping."""
    # Load color mapping from file
    color_map = load_color_mapping()
    time_bgcolor_map = {}
    
    for i, row in enumerate(table_rows[1:-2], start=2):  # Start from 2nd row, skip last 2 rows
        tds = row.find_all('td')
        if len(tds) > 0:
            # 2a) Extract text from first <td> (time slot)
            time_slot = tds[0].get_text(strip=True)
            
            # 2b) Extract status values from subsequent <td> tags using color mapping
            status_values = []
            for td in tds[1:]:  # Skip first <td>
                bgcolor = td.get('bgcolor', '')  # Get bgcolor attribute or empty string
                
                # If bgcolor is not present, check if it's bookable
                if not bgcolor:
                    onmouseover = td.get('onmouseover', '')
                    if onmouseover == 'booknow(this)':
                        status_values.append('available')
                    else:
                        status_values.append('')  # Use empty string for unknown status
                else:
                    # Map bgcolor to status using color mapping, fallback to "unavailable"
                    mapped_status = color_map.get(bgcolor, 'unavailable')
                    status_values.append(mapped_status)
            
            time_bgcolor_map[time_slot] = status_values
    
    return time_bgcolor_map

def filter_hourly_timeslots(time_bgcolor_map):
    """Filter time slots to only include times on the hour (e.g., 7:00am, 8:00am)."""
    hourly_map = {}
    
    for time_slot, status_list in time_bgcolor_map.items():
        # Check if time slot is on the hour (contains ":00")
        if ":00" in time_slot:
            hourly_map[time_slot] = status_list
    
    print(f"\nFILTERED HOURLY TIMESLOTS:")
    print(f"{'-'*50}")
    for time_slot, status_list in hourly_map.items():
        print(f'"{time_slot}": {status_list}')
    print(f"{'-'*50}")
    print(f"Filtered from {len(time_bgcolor_map)} to {len(hourly_map)} time slots")
    
    return hourly_map

def main():
    # Step 1: Load and validate JSON data
    html_data = load_and_validate_json_data()
    if html_data is None:
        return
    
    # Step 2: Extract the target table
    table_rows = extract_target_table(html_data)
    if table_rows is None:
        return
    
    # Step 3: Process the table rows
    if len(table_rows) > 0:
        headers = extract_headers(table_rows)
        time_bgcolor_map = create_time_bgcolor_map(table_rows)
        
        # Step 4: Filter to only hourly time slots
        hourly_timeslots = filter_hourly_timeslots(time_bgcolor_map)

if __name__ == "__main__":
    main()
