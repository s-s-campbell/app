# File that will parse the data from the GCS bucket and save it to BigQuery

import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import re

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
    return data['html'], data['source'], data['scraped_at'], data['url']

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
    
    return hourly_map

def create_structured_data(hourly_timeslots, headers, data_source, scraped_at, source_url):
    """Create structured table data from the processed booking information."""
    # Extract venue name and suburb from source
    venue_name, suburb = data_source.split(':', 1)
    
    # Define AEST timezone
    aest_tz = pytz.timezone("Australia/Sydney")
    
    # Parse date from scraped_at timestamp and convert to AEST
    scraped_datetime = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
    scraped_aest = scraped_datetime.astimezone(aest_tz)
    date_iso = scraped_aest.date().isoformat()
    
    # Current timestamp for parsed_at in AEST
    parsed_at = datetime.now(aest_tz).isoformat()
    
    # Extract surface information from headers (skip first header which is "Time")
    surface_info = []
    for header in headers[1:]:  # Skip "Time" header
        # Extract surface type and number from headers like "Court 1", "Court 2"
        match = re.match(r'^(\w+)\s+(\d+)$', header.strip())
        if match:
            surface_type = match.group(1)
            surface_number = match.group(2)
            surface_info.append((surface_type, surface_number))
        else:
            # Fallback if header doesn't match expected pattern
            surface_info.append((header.strip(), ""))
    
    # Create structured rows
    structured_data = []
    
    for time_slot, status_list in hourly_timeslots.items():
        # Parse start time in AEST
        start_time = parse_time_slot(time_slot, date_iso, aest_tz)
        # Calculate end time (1 hour later) in AEST
        end_time = (datetime.fromisoformat(start_time) + timedelta(hours=1)).isoformat()
        
        # Create row for each court/surface
        for i, booking_status in enumerate(status_list):
            if i < len(surface_info):
                surface_type, surface_number = surface_info[i]
                
                row = {
                    'venue_name': venue_name,
                    'suburb': suburb,
                    'date': date_iso,
                    'start_time': start_time,
                    'end_time': end_time,
                    'surface_type': surface_type,
                    'surface_number': surface_number,
                    'booking_status': booking_status,
                    'source_url': source_url,
                    'scraped_at': scraped_aest.isoformat(),
                    'parsed_at': parsed_at
                }
                structured_data.append(row)
    
    return structured_data

def parse_time_slot(time_slot, date_iso, timezone):
    """Parse time slot string like '7:00am' into datetime string in specified timezone."""
    # Remove any extra spaces and convert to standard format
    time_slot = time_slot.strip()
    
    # Parse time using datetime
    time_obj = datetime.strptime(time_slot, '%I:%M%p')
    
    # Combine with date and timezone
    datetime_str = f"{date_iso}T{time_obj.strftime('%H:%M:%S')}"
    naive_datetime = datetime.fromisoformat(datetime_str)
    datetime_with_tz = timezone.localize(naive_datetime)
    
    return datetime_with_tz.isoformat()

def print_structured_data(structured_data):
    """Print structured data as a formatted table."""
    if not structured_data:
        print("No structured data to display")
        return
    
    # Print header
    print(f"\nSTRUCTURED BOOKING DATA:")
    print(f"{'='*196}")
    
    # Print column headers
    headers = ['venue_name', 'suburb', 'date', 'start_time', 'end_time', 
               'surface_type', 'surface_number', 'booking_status', 'source_url', 'scraped_at', 'parsed_at']
    
    print(" | ".join(f"{header:15}" for header in headers))
    print("-" * 196)
    
    # Print data rows
    for row in structured_data:
        values = [str(row.get(header, ''))[:15] for header in headers]
        print(" | ".join(f"{value:15}" for value in values))
    
    print(f"{'='*196}")
    print(f"Total rows: {len(structured_data)}")

def main():
    # Step 1: Load and validate JSON data
    html_data, data_source, scraped_at, source_url = load_and_validate_json_data()
    assert html_data, f"HTML data not found at {data_source}"
    
    # Step 2: Extract the target table
    table_rows = extract_target_table(html_data)
    assert table_rows is not None, f"Booking table not found at {data_source}"  
    
    # Step 3: Process the table rows
    if len(table_rows) > 0:
        headers = extract_headers(table_rows)
        time_bgcolor_map = create_time_bgcolor_map(table_rows)
        
        # Step 4: Filter to only hourly time slots
        hourly_timeslots = filter_hourly_timeslots(time_bgcolor_map)
        
        # Step 5: Create structured data and print to stdout
        structured_data = create_structured_data(hourly_timeslots, headers, data_source, scraped_at, source_url)
        print_structured_data(structured_data)
    else:
        raise ValueError(f"Booking table is empty at {data_source}")

if __name__ == "__main__":
    main()
