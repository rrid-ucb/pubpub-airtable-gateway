#!/usr/bin/env python3

import os
import json
import requests
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
from airtable import Airtable
from slugify import slugify

# Load environment variables
load_dotenv()

# Setup timestamp
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Configuration variables
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
PUBPUB_API_KEY_RRID = os.getenv("PUBPUB_API_KEY_RRID")
PUBPUB_API_KEY_DEMO = os.getenv("PUBPUB_API_KEY_DEMO")

# Unset PUBPUB_API_KEY to avoid confusion
if "PUBPUB_API_KEY" in os.environ:
    del os.environ["PUBPUB_API_KEY"]

# Setup logging with debug mode
log_file = f"dryrun_log_{TIMESTAMP}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define Airtable tables we're interested in
AIRTABLE_TABLES = [
    "Preprint Info ONLY",
    "Student Reviewer Inputs",
    "Completed Review",
    "Contributor roles",
    "Role assignments",
    "Person",
    "Institution"
]

def setup_pubpub_api(slug):
    """Setup PubPub API configuration for a given slug"""
    if slug == "rrid":
        api_key = PUBPUB_API_KEY_RRID
    elif slug == "rr-demo":
        api_key = PUBPUB_API_KEY_DEMO
    else:
        raise ValueError(f"Invalid slug: {slug}")
    
    base_url = f"https://app.pubpub.org/api/v0/c/{slug}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    return base_url, headers

def fetch_airtable_data(cache_dir="airtable_cache"):
    """Fetch and cache Airtable data"""
    logger.info("Fetching data from Airtable...")
    
    # Create cache directory
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = f"{cache_dir}/airtable_data_{TIMESTAMP}.json"
    
    airtable_data = {}
    
    for table_name in AIRTABLE_TABLES:
        try:
            logger.info(f"Fetching data from '{table_name}' table...")
            table = Airtable(AIRTABLE_BASE_ID, table_name, api_key=AIRTABLE_API_KEY)
            
            # For the first attempt, try to get all records to verify access
            records = table.get_all(view="PubPub Platform Import", maxRecords=5)
            
            if records:
                serializable_records = [dict(r) for r in records]
                airtable_data[table_name] = serializable_records
                logger.info(f"✅ Retrieved {len(records)} records from '{table_name}'")
                
                # Log a sample record for debugging
                if records:
                    logger.debug(f"Sample record from '{table_name}': {json.dumps(serializable_records[0], indent=2)}")
            else:
                logger.warning(f"⚠️ No records found in '{table_name}'")
        except Exception as e:
            logger.error(f"❌ Failed to fetch '{table_name}': {str(e)}")
    
    # Cache the data
    with open(cache_file, "w") as f:
        json.dump(airtable_data, f, indent=2)
    
    logger.info(f"Cached Airtable data to {cache_file}")
    return airtable_data, cache_file

def get_pubpub_configuration(base_url, headers):
    """Get current configuration from PubPub"""
    logger.info("Fetching current PubPub configuration...")
    configuration = {}
    
    # Get pub types
    response = requests.get(f"{base_url}/site/pub-types", headers=headers)
    if response.status_code == 200:
        configuration["pub_types"] = response.json()
        logger.info(f"✅ Found {len(configuration['pub_types'])} pub types")
    else:
        logger.error(f"❌ Failed to get pub types: {response.status_code}")
        configuration["pub_types"] = []
    
    # Get stages
    response = requests.get(f"{base_url}/site/stages", headers=headers)
    if response.status_code == 200:
        configuration["stages"] = response.json()
        logger.info(f"✅ Found {len(configuration['stages'])} stages")
    else:
        logger.error(f"❌ Failed to get stages: {response.status_code}")
        configuration["stages"] = []
    
    # Get fields
    response = requests.get(f"{base_url}/site/fields", headers=headers)
    if response.status_code == 200:
        configuration["fields"] = response.json()
        logger.info(f"✅ Found {len(configuration['fields'])} fields")
    else:
        logger.error(f"❌ Failed to get fields: {response.status_code}")
        configuration["fields"] = []
    
    return configuration

def map_airtable_to_pubpub(airtable_data, pubpub_config, slug):
    """Map Airtable data to PubPub objects for dry-run"""
    logger.info("Mapping Airtable data to PubPub objects...")
    
    # Define mappings between Airtable tables and PubPub pub types
    type_mappings = {
        "Preprint Info ONLY": "Preprint",
        "Completed Review": "Review",
        "Student Reviewer Inputs": "Reviewer",
        "Person": "Person",
        "Institution": "Institution",
        "Contributor roles": "Role",
        "Role assignments": "Contributor"
    }
    
    # Find PubPub type IDs by name
    type_name_to_id = {}
    for pub_type in pubpub_config["pub_types"]:
        type_name_to_id[pub_type["name"]] = pub_type["id"]
    
    # Use first stage if available
    default_stage_id = pubpub_config["stages"][0]["id"] if pubpub_config["stages"] else None
    
    # Define special field mappings per table
    field_mappings = {
        "Preprint Info ONLY": {
            "Title": "title",
            "DOI": "doi",
            "Abstract": "abstract",
            "Team": "team",
            "Domain": "domain"
        },
        "Student Reviewer Inputs": {
            "Name": "reviewer-name",
            "Email": "reviewer-email",
            "Justification for invite": "justification-for-invite",
            "Affiliation": "affiliation",
            "Title": "reviewer-title",
            "Highest Degree": "highest-degree",
            "Subdiscipline": "subdiscipline",
            "Link to Profile": "link-to-profile"
        },
        "Completed Review": {
            "Title": "title",
        }
    }
    
    # Prepare mock operations
    mock_operations = []
    
    # Process each table
    for table_name, records in airtable_data.items():
        # Map to PubPub type
        pub_type_name = type_mappings.get(table_name)
        if not pub_type_name:
            logger.warning(f"⚠️ No mapping defined for '{table_name}', skipping")
            continue
        
        # Get PubPub type ID
        pub_type_id = type_name_to_id.get(pub_type_name)
        if not pub_type_id:
            logger.warning(f"⚠️ PubPub type '{pub_type_name}' not found in configuration, skipping")
            continue
        
        logger.info(f"Processing {len(records)} records from '{table_name}' as '{pub_type_name}'")
        
        # Process each record
        for record in records:
            # Prepare a PubPub pub
            pub_data = {
                "pubType": pub_type_id,
                "airtableId": record["id"]
            }
            
            # Add stage if available
            if default_stage_id:
                pub_data["initialStageId"] = default_stage_id
            
            # Map fields from Airtable to PubPub
            fields_map = field_mappings.get(table_name, {})
            for airtable_field, pubpub_field in fields_map.items():
                if airtable_field in record["fields"]:
                    pub_data[pubpub_field] = record["fields"][airtable_field]
            
            # Set a title if not mapped
            if "title" not in pub_data and "Title" in record["fields"]:
                pub_data["title"] = record["fields"]["Title"]
            elif "title" not in pub_data and "Name" in record["fields"]:
                pub_data["title"] = record["fields"]["Name"]
            elif "title" not in pub_data:
                pub_data["title"] = f"Import from {table_name} ({record['id']})"
            
            # Generate a slug
            pub_data["slug"] = slugify(pub_data["title"])
            
            # Add to mock operations
            mock_operations.append({
                "operation": "CREATE_PUB",
                "endpoint": f"https://app.pubpub.org/api/v0/c/{slug}/pubs",
                "method": "POST",
                "data": pub_data
            })
    
    return mock_operations

def perform_dry_run(airtable_data, slug):
    """Perform a dry run with mock operations"""
    logger.info(f"Performing dry run for slug '{slug}'...")
    
    # Setup API
    base_url, headers = setup_pubpub_api(slug)
    
    # Get current configuration
    pubpub_config = get_pubpub_configuration(base_url, headers)
    
    # Map data to operations
    mock_operations = map_airtable_to_pubpub(airtable_data, pubpub_config, slug)
    
    # Output operations
    logger.info(f"Dry run complete. Generated {len(mock_operations)} mock operations.")
    
    # Save operations to file
    dry_run_file = f"dryrun_{slug}_{TIMESTAMP}.json"
    with open(dry_run_file, "w") as f:
        json.dump(mock_operations, f, indent=2)
    
    logger.info(f"Saved dry run operations to {dry_run_file}")
    
    # Log each operation
    for i, op in enumerate(mock_operations):
        logger.debug(f"MOCK OPERATION {i+1}: {op['operation']} to {op['endpoint']}")
        logger.debug(f"Data: {json.dumps(op['data'], indent=2)}")
    
    return mock_operations, dry_run_file

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Fetch Airtable data and perform PubPub API dry run")
    parser.add_argument("--skip-airtable", action="store_true", help="Skip fetching Airtable data (use cached)")
    parser.add_argument("--skip-rrid", action="store_true", help="Skip dry run for rrid slug")
    parser.add_argument("--skip-demo", action="store_true", help="Skip dry run for rr-demo slug")
    parser.add_argument("--cache-file", help="Path to cached Airtable data file")
    args = parser.parse_args()
    
    # Display environment status
    if not AIRTABLE_API_KEY:
        logger.warning("⚠️ AIRTABLE_API_KEY is not set")
    if not AIRTABLE_BASE_ID:
        logger.warning("⚠️ AIRTABLE_BASE_ID is not set")
    if not PUBPUB_API_KEY_RRID:
        logger.warning("⚠️ PUBPUB_API_KEY_RRID is not set")
    if not PUBPUB_API_KEY_DEMO:
        logger.warning("⚠️ PUBPUB_API_KEY_DEMO is not set")
    
    # Fetch or load Airtable data
    if args.skip_airtable and args.cache_file:
        logger.info(f"Loading cached Airtable data from {args.cache_file}")
        with open(args.cache_file, "r") as f:
            airtable_data = json.load(f)
        cache_file = args.cache_file
    else:
        airtable_data, cache_file = fetch_airtable_data()
    
    # Perform dry runs
    if not args.skip_demo:
        logger.info("Starting dry run for rr-demo...")
        demo_operations, demo_file = perform_dry_run(airtable_data, "rr-demo")
        logger.info(f"rr-demo dry run complete: {len(demo_operations)} operations")
    
    if not args.skip_rrid:
        logger.info("Starting dry run for rrid...")
        rrid_operations, rrid_file = perform_dry_run(airtable_data, "rrid")
        logger.info(f"rrid dry run complete: {len(rrid_operations)} operations")
    
    logger.info(f"All operations complete. Log file: {log_file}")

if __name__ == "__main__":
    main() 