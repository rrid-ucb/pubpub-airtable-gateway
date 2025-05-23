#!/usr/bin/env python3
import os
import json
import logging
import datetime
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
def setup_logging(debug=False):
    """Set up logging configuration."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/airtable_fetch_{timestamp}.log"
    
    log_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('airtable_fetch')
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger

def ensure_output_dir(directory="output"):
    """Create output directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

class AirtableFetcher:
    """Class to fetch data from Airtable and save it as a sample."""
    
    def __init__(self, base_id=None, api_key=None, debug=False):
        """Initialize the Airtable fetcher."""
        self.logger = logging.getLogger('airtable_fetch')
        
        # Get API key from environment if not provided
        self.api_key = api_key or os.getenv('AIRTABLE_API_KEY')
        if not self.api_key:
            self.logger.error("AIRTABLE_API_KEY not found in environment variables")
            raise ValueError("AIRTABLE_API_KEY not found")
        
        # Get base ID from environment if not provided
        self.base_id = base_id or os.getenv('AIRTABLE_BASE_ID')
        if not self.base_id:
            self.logger.error("AIRTABLE_BASE_ID not found in environment variables")
            raise ValueError("AIRTABLE_BASE_ID not found")
        
        self.api_url = f"https://api.airtable.com/v0/{self.base_id}"
        self.debug = debug
        self.data = {}
    
    def fetch_table(self, table_name, max_records=100):
        """Fetch records from an Airtable table."""
        self.logger.info(f"Fetching data from table: {table_name} (max {max_records} records)")
        
        url = f"{self.api_url}/{table_name}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "maxRecords": max_records,
            "view": "Grid view"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            records = data.get("records", [])
            self.logger.info(f"Successfully fetched {len(records)} records from {table_name}")
            
            # Extract the fields and add record ID
            processed_records = []
            for record in records:
                item = record.get("fields", {})
                item["id"] = record.get("id")
                processed_records.append(item)
            
            return processed_records
        
        except Exception as e:
            self.logger.error(f"Error fetching data from {table_name}: {e}")
            return []
    
    def fetch_all_tables(self):
        """Fetch data from all tables needed for the sample."""
        tables_to_fetch = [
            {"name": "Preprints", "key": "preprints"},
            {"name": "Reviewers", "key": "reviewers"},
            {"name": "Reviews", "key": "reviews"},
            {"name": "Persons", "key": "persons"},
            {"name": "Institutions", "key": "institutions"},
            {"name": "Roles", "key": "roles"},
            {"name": "RoleAssignments", "key": "role_assignments"}
        ]
        
        for table in tables_to_fetch:
            self.logger.info(f"Fetching {table['name']}...")
            records = self.fetch_table(table['name'])
            self.data[table['key']] = records
        
        return self.data
    
    def save_data(self, directory="output"):
        """Save the fetched data to a JSON file."""
        ensure_output_dir(directory)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{directory}/airtable_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.data, f, indent=2)
        
        self.logger.info(f"Airtable data saved to {filename}")
        return filename

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Airtable Data Fetcher")
    parser.add_argument("--base-id", help="Airtable Base ID (overrides .env)")
    parser.add_argument("--api-key", help="Airtable API Key (overrides .env)")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging")
    parser.add_argument("--output", "-o", default="output", help="Output directory for saved data")
    parser.add_argument("--max-records", "-m", type=int, default=100, help="Maximum records to fetch per table")
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(args.debug)
    
    try:
        # Create and run the Airtable fetcher
        logger.info("Initializing Airtable fetcher...")
        fetcher = AirtableFetcher(args.base_id, args.api_key, args.debug)
        
        logger.info("Fetching data from Airtable...")
        fetcher.fetch_all_tables()
        
        logger.info("Saving data...")
        output_file = fetcher.save_data(args.output)
        
        logger.info(f"Data fetching complete. Results saved to: {output_file}")
        
        # Print summary of fetched data
        for table_name, records in fetcher.data.items():
            logger.info(f"{table_name}: {len(records)} records")
    
    except Exception as e:
        logger.error(f"Error in data fetching process: {e}", exc_info=args.debug)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 