#!/usr/bin/env python3

import os
import json
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

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
SOURCE_API_KEY = os.getenv("PUBPUB_API_KEY_RRID")
TARGET_API_KEY = os.getenv("PUBPUB_API_KEY_DEMO")

# Validate environment variables
if not SOURCE_API_KEY:
    raise ValueError("PUBPUB_API_KEY_RRID environment variable is not set")
if not TARGET_API_KEY:
    raise ValueError("PUBPUB_API_KEY_DEMO environment variable is not set")

# API URLs
SOURCE_URL = f"https://app.pubpub.org/api/v0/c/{SOURCE_SLUG}"
TARGET_URL = f"https://app.pubpub.org/api/v0/c/{TARGET_SLUG}"

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

def test_api_access(name, base_url, headers):
    """Test API access to the community"""
    logger.info(f"Testing API access to {name}...")
    
    # Test pub types endpoint
    pub_types_url = f"{base_url}/site/pub-types"
    response = requests.get(pub_types_url, headers=headers)
    
    if response.status_code == 200:
        pub_types = response.json()
        logger.info(f"✅ Successfully accessed {name} API - found {len(pub_types)} pub types")
        return True
    else:
        logger.error(f"❌ Failed to access {name} API: {response.status_code} - {response.text}")
        return False

def get_source_configuration():
    """Get configuration data from source (rrid)"""
    logger.info("Fetching configuration from source (rrid)...")
    
    # Get pub types
    response = requests.get(f"{SOURCE_URL}/site/pub-types", headers=SOURCE_HEADERS)
    if response.status_code == 200:
        pub_types = response.json()
        logger.info(f"✅ Retrieved {len(pub_types)} pub types from source")
    else:
        logger.error(f"❌ Failed to get pub types from source: {response.status_code} - {response.text}")
        pub_types = []
    
    # Get stages
    response = requests.get(f"{SOURCE_URL}/site/stages", headers=SOURCE_HEADERS)
    if response.status_code == 200:
        stages = response.json()
        logger.info(f"✅ Retrieved {len(stages)} stages from source")
    else:
        logger.error(f"❌ Failed to get stages from source: {response.status_code} - {response.text}")
        stages = []
    
    # Save configuration to files for reference
    os.makedirs("config_backup", exist_ok=True)
    with open(f"config_backup/pub_types_{TIMESTAMP}.json", "w") as f:
        json.dump(pub_types, f, indent=2)
    with open(f"config_backup/stages_{TIMESTAMP}.json", "w") as f:
        json.dump(stages, f, indent=2)
    
    return {"pub_types": pub_types, "stages": stages}

def transfer_pub_types(pub_types):
    """Transfer pub types to target"""
    logger.info("Transferring pub types to target...")
    
    type_id_mapping = {}
    target_types = []
    
    # Get existing pub types
    try:
        response = requests.get(f"{TARGET_URL}/site/pub-types", headers=TARGET_HEADERS)
        if response.status_code == 200:
            target_types = response.json()
            logger.info(f"Target already has {len(target_types)} pub types")
        else:
            logger.warning(f"⚠️ Could not get existing pub types: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"❌ Error getting existing pub types: {str(e)}")
    
    # Map existing pub types by name
    existing_types = {t["name"]: t for t in target_types}
    
    # Process each pub type
    for pub_type in pub_types:
        type_name = pub_type["name"]
        
        # Check if type already exists
        if type_name in existing_types:
            logger.info(f"⚠️ Pub type '{type_name}' already exists, skipping creation")
            type_id_mapping[pub_type["id"]] = existing_types[type_name]["id"]
            continue
        
        # Prepare data for creation
        transfer_data = {
            "name": type_name,
            "description": pub_type.get("description", ""),
            "icon": pub_type.get("icon", "")
        }
        
        # Try to create the pub type
        try:
            logger.info(f"Creating pub type '{type_name}'...")
            
            # Direct API call to correct endpoint
            url = f"{TARGET_URL}/pub-types"
            response = requests.post(
                url,
                headers=TARGET_HEADERS,
                json=transfer_data
            )
            
            if response.status_code == 200:
                new_type = response.json()
                logger.info(f"✅ Created pub type: {type_name} (ID: {new_type['id']})")
                type_id_mapping[pub_type["id"]] = new_type["id"]
            else:
                logger.error(f"❌ Failed to create pub type: {type_name}")
                logger.error(f"URL: {url}")
                logger.error(f"Response ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"❌ Error creating pub type {type_name}: {str(e)}")
    
    return type_id_mapping

def transfer_stages(stages):
    """Transfer stages to target"""
    logger.info("Transferring stages to target...")
    
    stage_id_mapping = {}
    target_stages = []
    
    # Get existing stages
    try:
        response = requests.get(f"{TARGET_URL}/site/stages", headers=TARGET_HEADERS)
        if response.status_code == 200:
            target_stages = response.json()
            logger.info(f"Target already has {len(target_stages)} stages")
        else:
            logger.warning(f"⚠️ Could not get existing stages: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"❌ Error getting existing stages: {str(e)}")
    
    # Map existing stages by name
    existing_stages = {s["name"]: s for s in target_stages}
    
    # Process each stage
    for stage in stages:
        stage_name = stage["name"]
        
        # Check if stage already exists
        if stage_name in existing_stages:
            logger.info(f"⚠️ Stage '{stage_name}' already exists, skipping creation")
            stage_id_mapping[stage["id"]] = existing_stages[stage_name]["id"]
            continue
        
        # Prepare data for creation
        transfer_data = {
            "name": stage_name,
            "description": stage.get("description", ""),
            "color": stage.get("color", "#000000")
        }
        
        # Try to create the stage
        try:
            logger.info(f"Creating stage '{stage_name}'...")
            
            # Direct API call to correct endpoint
            url = f"{TARGET_URL}/stages"
            response = requests.post(
                url,
                headers=TARGET_HEADERS,
                json=transfer_data
            )
            
            if response.status_code == 200:
                new_stage = response.json()
                logger.info(f"✅ Created stage: {stage_name} (ID: {new_stage['id']})")
                stage_id_mapping[stage["id"]] = new_stage["id"]
            else:
                logger.error(f"❌ Failed to create stage: {stage_name}")
                logger.error(f"URL: {url}")
                logger.error(f"Response ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"❌ Error creating stage {stage_name}: {str(e)}")
    
    # Configure move constraints (if any stages were created)
    if stage_id_mapping:
        configure_move_constraints(stages, stage_id_mapping)
    
    return stage_id_mapping

def configure_move_constraints(stages, stage_id_mapping):
    """Configure stage move constraints"""
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
                    # Direct API call to correct endpoint
                    url = f"{TARGET_URL}/stages/{target_id}/move-constraints"
                    response = requests.put(
                        url,
                        headers=TARGET_HEADERS,
                        json=constraints
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Set move constraints for stage: {stage['name']}")
                    else:
                        logger.error(f"❌ Failed to set move constraints for stage: {stage['name']}")
                        logger.error(f"URL: {url}")
                        logger.error(f"Response ({response.status_code}): {response.text}")
                except Exception as e:
                    logger.error(f"❌ Error setting move constraints for {stage['name']}: {str(e)}")

def create_test_pubs(pub_type_mapping, stage_id_mapping):
    """Create a few test pubs to verify the configuration"""
    logger.info("Creating test publications...")
    
    created_pubs = []
    
    # Get existing pub types in target
    response = requests.get(f"{TARGET_URL}/site/pub-types", headers=TARGET_HEADERS)
    if response.status_code != 200:
        logger.error(f"❌ Failed to get pub types from target: {response.status_code} - {response.text}")
        return created_pubs
    
    target_pub_types = response.json()
    
    # Get the first stage in target (if any)
    response = requests.get(f"{TARGET_URL}/site/stages", headers=TARGET_HEADERS)
    if response.status_code == 200:
        target_stages = response.json()
        initial_stage_id = target_stages[0]["id"] if target_stages else None
    else:
        initial_stage_id = None
        logger.warning("⚠️ No stages found in target, pubs will be created without a stage")
    
    # Create a test pub for each pub type
    for pub_type in target_pub_types:
        # Basic test pub data
        pub_data = {
            "title": f"Test {pub_type['name']} ({TIMESTAMP})",
            "slug": f"test-{pub_type['name'].lower()}-{TIMESTAMP}",
            "pubType": pub_type["id"]
        }
        
        # Add initial stage if available
        if initial_stage_id:
            pub_data["initialStageId"] = initial_stage_id
        
        try:
            # Create the pub directly with correct endpoint
            url = f"{TARGET_URL}/pubs"
            response = requests.post(
                url,
                headers=TARGET_HEADERS,
                json=pub_data
            )
            
            if response.status_code == 200:
                new_pub = response.json()
                logger.info(f"✅ Created test pub: {pub_data['title']} (ID: {new_pub['id']})")
                created_pubs.append(new_pub)
            else:
                logger.error(f"❌ Failed to create test pub: {pub_data['title']}")
                logger.error(f"URL: {url}")
                logger.error(f"Response ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"❌ Error creating test pub {pub_data['title']}: {str(e)}")
    
    return created_pubs

def main():
    """Main function to transfer configuration and data"""
    logger.info("Starting improved configuration transfer process")
    logger.info(f"Source: {SOURCE_SLUG}, Target: {TARGET_SLUG}")
    
    # Step 1: Test API access to both communities
    source_access = test_api_access("source", SOURCE_URL, SOURCE_HEADERS)
    target_access = test_api_access("target", TARGET_URL, TARGET_HEADERS)
    
    if not source_access or not target_access:
        logger.error("❌ API access test failed, aborting transfer")
        return
    
    # Step 2: Get source configuration
    source_config = get_source_configuration()
    
    # Step 3: Transfer pub types
    type_id_mapping = transfer_pub_types(source_config["pub_types"])
    
    # Step 4: Transfer stages
    stage_id_mapping = transfer_stages(source_config["stages"])
    
    # Step 5: Create test pubs
    created_pubs = create_test_pubs(type_id_mapping, stage_id_mapping)
    
    # Generate a report
    report_path = f"transfer_report_{TIMESTAMP}.md"
    with open(report_path, "w") as f:
        f.write(f"# Improved Transfer Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Source: {SOURCE_SLUG}, Target: {TARGET_SLUG}\n\n")
        
        f.write("## Configuration Summary\n\n")
        f.write(f"- Transferred {len(type_id_mapping)} pub types\n")
        f.write(f"- Transferred {len(stage_id_mapping)} stages\n\n")
        
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
        
        f.write("\n## Test Publications\n\n")
        f.write("| Title | ID | URL |\n")
        f.write("|-------|----|---------|\n")
        for pub in created_pubs:
            pub_url = f"https://app.pubpub.org/{TARGET_SLUG}/pub/{pub.get('slug', pub['id'])}"
            f.write(f"| {pub['title']} | {pub['id']} | [View]({pub_url}) |\n")
    
    logger.info(f"Process complete! Report saved to {report_path}")
    logger.info(f"Log file: {log_file}")

if __name__ == "__main__":
    main() 