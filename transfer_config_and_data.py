#!/usr/bin/env python3

import os
import json
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
from airtable import Airtable
from slugify import slugify

# Load environment variables
load_dotenv()

# Unset PUBPUB_API_KEY to avoid confusion
if "PUBPUB_API_KEY" in os.environ:
    del os.environ["PUBPUB_API_KEY"]

# Setup logging
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"transfer_log_{TIMESTAMP}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SOURCE_SLUG = "rrid"
TARGET_SLUG = "rr-demo"
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
SOURCE_API_KEY = os.getenv("PUBPUB_API_KEY_RRID")
TARGET_API_KEY = os.getenv("PUBPUB_API_KEY_DEMO")

# Validate environment variables
if not SOURCE_API_KEY:
    raise ValueError("PUBPUB_API_KEY_RRID environment variable is not set")
if not TARGET_API_KEY:
    raise ValueError("PUBPUB_API_KEY_DEMO environment variable is not set")
if not AIRTABLE_API_KEY:
    raise ValueError("AIRTABLE_API_KEY environment variable is not set")
if not AIRTABLE_BASE_ID:
    raise ValueError("AIRTABLE_BASE_ID environment variable is not set")

# API URLs
SOURCE_URL = f"https://app.pubpub.org/api/v0/c/{SOURCE_SLUG}/site"
TARGET_URL = f"https://app.pubpub.org/api/v0/c/{TARGET_SLUG}/site"

# Headers
SOURCE_HEADERS = {
    "Authorization": f"Bearer {SOURCE_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

TARGET_HEADERS = {
    "Authorization": f"Bearer {TARGET_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def get_source_configuration():
    """Get configuration data from source (rrid)"""
    logger.info("Fetching configuration from source (rrid)...")
    
    # Get pub types
    response = requests.get(f"{SOURCE_URL}/pub-types", headers=SOURCE_HEADERS)
    pub_types = response.json() if response.status_code == 200 else []
    
    # Get stages
    response = requests.get(f"{SOURCE_URL}/stages", headers=SOURCE_HEADERS)
    stages = response.json() if response.status_code == 200 else []
    
    # Get fields (optional but useful)
    response = requests.get(f"{SOURCE_URL}/fields", headers=SOURCE_HEADERS)
    fields = response.json() if response.status_code == 200 else []
    
    # Save configuration to files for reference
    os.makedirs("config_backup", exist_ok=True)
    with open(f"config_backup/pub_types_{TIMESTAMP}.json", "w") as f:
        json.dump(pub_types, f, indent=2)
    with open(f"config_backup/stages_{TIMESTAMP}.json", "w") as f:
        json.dump(stages, f, indent=2)
    with open(f"config_backup/fields_{TIMESTAMP}.json", "w") as f:
        json.dump(fields, f, indent=2)
    
    logger.info(f"Found {len(pub_types)} pub types, {len(stages)} stages, and {len(fields)} fields")
    return {"pub_types": pub_types, "stages": stages, "fields": fields}

def clear_target_configuration():
    """Clear existing configuration in target (rr-demo)"""
    logger.info("Checking existing configuration in target (rr-demo)...")
    
    # We don't actually delete anything, just log what exists
    response = requests.get(f"{TARGET_URL}/pub-types", headers=TARGET_HEADERS)
    pub_types = response.json() if response.status_code == 200 else []
    
    response = requests.get(f"{TARGET_URL}/stages", headers=TARGET_HEADERS)
    stages = response.json() if response.status_code == 200 else []
    
    logger.info(f"Target has {len(pub_types)} existing pub types and {len(stages)} existing stages")
    
    # Return existing IDs for reference
    return {
        "pub_types": [p["id"] for p in pub_types],
        "stages": [s["id"] for s in stages]
    }

def transfer_pub_types(pub_types):
    """Transfer pub types to target"""
    logger.info("Transferring pub types to target...")
    
    type_id_mapping = {}
    
    for pub_type in pub_types:
        transfer_data = {
            "name": pub_type["name"],
            "description": pub_type.get("description", ""),
            "icon": pub_type.get("icon", ""),
            "pubTitleSingular": pub_type.get("pubTitleSingular", pub_type["name"]),
            "pubTitlePlural": pub_type.get("pubTitlePlural", f"{pub_type['name']}s"),
        }
        
        try:
            response = requests.post(
                f"{TARGET_URL}/pub-types",
                headers=TARGET_HEADERS,
                json=transfer_data
            )
            
            if response.status_code == 200:
                new_type = response.json()
                type_id_mapping[pub_type["id"]] = new_type["id"]
                logger.info(f"✅ Created pub type: {pub_type['name']} (ID: {new_type['id']})")
            else:
                logger.error(f"❌ Failed to create pub type: {pub_type['name']}")
                logger.error(f"Response ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"❌ Error creating pub type {pub_type['name']}: {str(e)}")
    
    return type_id_mapping

def transfer_stages(stages):
    """Transfer stages to target"""
    logger.info("Transferring stages to target...")
    
    stage_id_mapping = {}
    
    # Create stages
    for stage in stages:
        transfer_data = {
            "name": stage["name"],
            "description": stage.get("description", ""),
            "color": stage.get("color", "#000000")
        }
        
        try:
            response = requests.post(
                f"{TARGET_URL}/stages",
                headers=TARGET_HEADERS,
                json=transfer_data
            )
            
            if response.status_code == 200:
                new_stage = response.json()
                stage_id_mapping[stage["id"]] = new_stage["id"]
                logger.info(f"✅ Created stage: {stage['name']} (ID: {new_stage['id']})")
            else:
                logger.error(f"❌ Failed to create stage: {stage['name']}")
                logger.error(f"Response ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"❌ Error creating stage {stage['name']}: {str(e)}")
    
    # Set up move constraints
    logger.info("Configuring stage move constraints...")
    for stage in stages:
        if "moveConstraints" in stage and stage["moveConstraints"]:
            source_id = stage["id"]
            target_id = stage_id_mapping.get(source_id)
            
            if not target_id:
                logger.warning(f"⚠️ Could not find target ID for stage {stage['name']}")
                continue
            
            constraints = []
            for constraint in stage["moveConstraints"]:
                constraint_id = constraint["id"]
                if constraint_id in stage_id_mapping:
                    constraints.append({"id": stage_id_mapping[constraint_id]})
                else:
                    logger.warning(f"⚠️ Could not find target ID for constraint {constraint_id}")
            
            if constraints:
                try:
                    response = requests.put(
                        f"{TARGET_URL}/stages/{target_id}/move-constraints",
                        headers=TARGET_HEADERS,
                        json=constraints
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Set move constraints for stage: {stage['name']}")
                    else:
                        logger.error(f"❌ Failed to set move constraints for stage: {stage['name']}")
                        logger.error(f"Response ({response.status_code}): {response.text}")
                except Exception as e:
                    logger.error(f"❌ Error setting move constraints for {stage['name']}: {str(e)}")
    
    return stage_id_mapping

def transfer_fields(fields, type_id_mapping):
    """Transfer custom fields to target"""
    logger.info("Transferring custom fields to target...")
    
    for field in fields:
        # Skip fields without a pubType
        if not field.get("pubType"):
            continue
        
        # Map the pub type ID
        source_type_id = field["pubType"]
        if source_type_id not in type_id_mapping:
            logger.warning(f"⚠️ Skipping field {field.get('name')}: could not map pub type {source_type_id}")
            continue
        
        transfer_data = {
            "name": field["name"],
            "description": field.get("description", ""),
            "required": field.get("required", False),
            "type": field.get("type", "string"),
            "pubType": type_id_mapping[source_type_id]
        }
        
        # Add other field properties based on type
        if field.get("type") == "select":
            transfer_data["options"] = field.get("options", [])
        elif field.get("type") == "multi-select":
            transfer_data["options"] = field.get("options", [])
        
        try:
            response = requests.post(
                f"{TARGET_URL}/fields",
                headers=TARGET_HEADERS,
                json=transfer_data
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Created field: {field['name']}")
            else:
                logger.error(f"❌ Failed to create field: {field['name']}")
                logger.error(f"Response ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"❌ Error creating field {field['name']}: {str(e)}")

def get_airtable_sample_data():
    """Get a small sample of data from Airtable for testing"""
    logger.info("Fetching sample data from Airtable...")
    
    sample_data = {}
    
    try:
        # Try a few common table names or adjust based on your Airtable structure
        possible_tables = [
            "Preprint Info ONLY", 
            "Reviewers", 
            "Reviews",
            "Persons",
            "Institutions",
            "Contributor roles"
        ]
        
        for table_name in possible_tables:
            try:
                table = Airtable(AIRTABLE_BASE_ID, table_name, api_key=AIRTABLE_API_KEY)
                records = table.get_all(maxRecords=2)  # Get just 2 records for testing
                
                if records:
                    sample_data[table_name] = records
                    logger.info(f"✅ Retrieved {len(records)} records from '{table_name}'")
            except Exception as e:
                logger.warning(f"⚠️ Could not access table '{table_name}': {str(e)}")
        
        # Save sample data for reference
        os.makedirs("data_backup", exist_ok=True)
        with open(f"data_backup/airtable_sample_{TIMESTAMP}.json", "w") as f:
            # Convert to plain dict for JSON serialization
            serializable_data = {}
            for table, records in sample_data.items():
                serializable_data[table] = [dict(r) for r in records]
            json.dump(serializable_data, f, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Error fetching Airtable data: {str(e)}")
    
    return sample_data

def create_pub_from_airtable(record, pub_type_id, stage_id, field_mapping=None):
    """Create a PubPub publication from an Airtable record"""
    if field_mapping is None:
        field_mapping = {}
    
    # Start with a basic pub data structure
    pub_data = {
        "pubType": pub_type_id,
        "initialStageId": stage_id
    }
    
    # Use field_mapping to map Airtable fields to PubPub fields
    # For now, just use some common fields as examples
    if "Title" in record["fields"]:
        pub_data["title"] = record["fields"]["Title"]
    elif "Name" in record["fields"]:
        pub_data["title"] = record["fields"]["Name"]
    else:
        # Generate a title from the record ID if no obvious title field
        pub_data["title"] = f"Import from Airtable ({record['id']})"
    
    # Generate a slug
    pub_data["slug"] = slugify(pub_data["title"])
    
    # Add Airtable ID as custom metadata
    pub_data["airtableId"] = record["id"]
    
    # Add other fields based on mapping
    for airtable_field, pubpub_field in field_mapping.items():
        if airtable_field in record["fields"]:
            pub_data[pubpub_field] = record["fields"][airtable_field]
    
    # Create the pub
    try:
        response = requests.post(
            f"{TARGET_URL}/pubs",
            headers=TARGET_HEADERS,
            json=pub_data
        )
        
        if response.status_code == 200:
            new_pub = response.json()
            logger.info(f"✅ Created pub: {pub_data['title']} (ID: {new_pub['id']})")
            return new_pub
        else:
            logger.error(f"❌ Failed to create pub: {pub_data['title']}")
            logger.error(f"Response ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Error creating pub {pub_data['title']}: {str(e)}")
        return None

def import_airtable_data(airtable_data, pub_type_mapping, stage_id_mapping):
    """Import Airtable data to target PubPub"""
    logger.info("Importing Airtable data to target PubPub...")
    
    # Example mappings - these would need to be customized based on your actual data model
    type_mappings = {
        "Preprint Info ONLY": "Preprint",
        "Reviews": "Review",
        "Reviewers": "Reviewer",
        "Persons": "Person",
        "Institutions": "Institution",
        "Contributor roles": "Role"
    }
    
    # Get all pub types from target to find correct IDs
    response = requests.get(f"{TARGET_URL}/pub-types", headers=TARGET_HEADERS)
    target_pub_types = response.json() if response.status_code == 200 else []
    
    type_name_to_id = {t["name"]: t["id"] for t in target_pub_types}
    
    # Use the first stage as default initial stage
    response = requests.get(f"{TARGET_URL}/stages", headers=TARGET_HEADERS)
    target_stages = response.json() if response.status_code == 200 else []
    default_stage_id = target_stages[0]["id"] if target_stages else None
    
    created_pubs = []
    
    for table_name, records in airtable_data.items():
        # Map the table to a pub type
        pub_type_name = type_mappings.get(table_name)
        if not pub_type_name or pub_type_name not in type_name_to_id:
            logger.warning(f"⚠️ Skipping table '{table_name}': no matching pub type found")
            continue
        
        pub_type_id = type_name_to_id[pub_type_name]
        
        # Use a basic field mapping for this table
        # This would need to be customized based on your data model
        field_mapping = {}
        
        # Process each record
        for record in records:
            new_pub = create_pub_from_airtable(
                record, 
                pub_type_id, 
                default_stage_id, 
                field_mapping
            )
            
            if new_pub:
                created_pubs.append(new_pub)
    
    logger.info(f"Created {len(created_pubs)} pubs from Airtable data")
    return created_pubs

def main():
    """Main function to transfer configuration and data"""
    logger.info("Starting configuration and data transfer process")
    logger.info(f"Source: {SOURCE_SLUG}, Target: {TARGET_SLUG}")
    
    # Step 1: Get source configuration
    source_config = get_source_configuration()
    
    # Step 2: Check existing target configuration
    existing_ids = clear_target_configuration()
    
    # Step 3: Transfer pub types
    type_id_mapping = transfer_pub_types(source_config["pub_types"])
    
    # Step 4: Transfer stages
    stage_id_mapping = transfer_stages(source_config["stages"])
    
    # Step 5: Transfer fields
    transfer_fields(source_config["fields"], type_id_mapping)
    
    # Step 6: Get sample Airtable data
    airtable_data = get_airtable_sample_data()
    
    # Step 7: Import Airtable data
    created_pubs = import_airtable_data(airtable_data, type_id_mapping, stage_id_mapping)
    
    # Generate a report
    report_path = f"transfer_report_{TIMESTAMP}.md"
    with open(report_path, "w") as f:
        f.write(f"# Transfer Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Source: {SOURCE_SLUG}, Target: {TARGET_SLUG}\n\n")
        
        f.write("## Configuration Summary\n\n")
        f.write(f"- Transferred {len(type_id_mapping)} pub types\n")
        f.write(f"- Transferred {len(stage_id_mapping)} stages\n")
        f.write(f"- Transferred {len(source_config['fields'])} custom fields\n\n")
        
        f.write("## Data Summary\n\n")
        f.write(f"- Created {len(created_pubs)} pubs from Airtable data\n\n")
        
        f.write("## ID Mappings\n\n")
        f.write("### Pub Types\n\n")
        f.write("| Source ID | Target ID |\n")
        f.write("|-----------|----------|\n")
        for source_id, target_id in type_id_mapping.items():
            f.write(f"| {source_id} | {target_id} |\n")
        
        f.write("\n### Stages\n\n")
        f.write("| Source ID | Target ID |\n")
        f.write("|-----------|----------|\n")
        for source_id, target_id in stage_id_mapping.items():
            f.write(f"| {source_id} | {target_id} |\n")
        
        f.write("\n## Created Pubs\n\n")
        f.write("| Title | ID | URL |\n")
        f.write("|-------|----|---------|\n")
        for pub in created_pubs:
            pub_url = f"https://app.pubpub.org/{TARGET_SLUG}/pub/{pub.get('slug', pub['id'])}"
            f.write(f"| {pub['title']} | {pub['id']} | [View]({pub_url}) |\n")
    
    logger.info(f"Process complete! Report saved to {report_path}")
    logger.info(f"Log file: {log_file}")

if __name__ == "__main__":
    main() 