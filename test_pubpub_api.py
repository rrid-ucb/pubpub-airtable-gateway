#!/usr/bin/env python

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Directory paths
REPORTS_DIR = Path("reports")
CONFIG_BACKUP_DIR = Path("config_backup")
LOGS_DIR = Path("logs")

# Create directories if they don't exist
REPORTS_DIR.mkdir(exist_ok=True)
CONFIG_BACKUP_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Load environment variables
load_dotenv()

# API credentials from environment
API_KEY = os.getenv("PUBPUB_API_KEY")
# COMMUNITY_SLUG = os.getenv("COMMUNITY_SLUG", "rr-demo")
COMMUNITY_SLUG = os.getenv("COMMUNITY_SLUG", "rrid")
if COMMUNITY_SLUG == "rrid":
    API_KEY = os.getenv("PUBPUB_API_KEY_RRID")
elif COMMUNITY_SLUG == "rr-demo":
    API_KEY = os.getenv("PUBPUB_API_KEY_DEMO")


if not API_KEY:
    raise ValueError("PUBPUB_API_KEY environment variable is not set")

# API endpoints
base_url = f"https://app.pubpub.org/api/v0/c/{COMMUNITY_SLUG}/site"
pub_types_url = f"{base_url}/pub-types"
stages_url = f"{base_url}/stages"

# Headers
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def save_report(pub_types_data, stages_data):
    """Save discovered type IDs and stages to a report file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = REPORTS_DIR / f"pubpub_config_{timestamp}.md"
    
    with open(report_file, "w") as f:
        f.write("# PubPub Configuration Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Publication Types
        f.write("## Publication Types\n\n")
        f.write("| Name | ID | Description |\n")
        f.write("|------|----|--------------|\n")
        
        for type_info in pub_types_data:
            name = type_info.get("name", "N/A")
            id = type_info.get("id", "N/A")
            desc = type_info.get("description", "N/A")
            f.write(f"| {name} | `{id}` | {desc} |\n")
        
        # Stages
        f.write("\n## Stages\n\n")
        f.write("| Name | ID | Order |\n")
        f.write("|------|-----|-------|\n")
        
        for stage in stages_data:
            name = stage.get("name", "N/A")
            id = stage.get("id", "N/A")
            order = stage.get("order", "N/A")
            f.write(f"| {name} | `{id}` | {order} |\n")
        
        # Environment Variables
        f.write("\n## Environment Variables\n\n")
        f.write("Update your `.env` file with these values:\n\n")
        f.write("```bash\n")
        f.write("# PUB TYPES\n")
        for type_info in pub_types_data:
            name = type_info.get("name", "").upper().replace(" ", "_")
            id = type_info.get("id", "")
            f.write(f"{name}_TYPE_ID={id}\n")
        
        f.write("\n# STAGES\n")
        for stage in stages_data:
            name = stage.get("name", "").upper().replace(" ", "_")
            id = stage.get("id", "")
            f.write(f"{name}_STAGE_ID={id}\n")
        f.write("```\n")
        
        f.write("\n## Available URLs\n\n")
        urls = [
            "https://app.pubpub.org/c/rrid",
            "https://app.pubpub.org/c/rrid/pubs",
            "https://app.pubpub.org/c/rrid/stages",
            "https://app.pubpub.org/c/rrid/activity/actions",
            "https://app.pubpub.org/c/rrid/stages/manage",
            "https://app.pubpub.org/c/rrid/forms",
            "https://app.pubpub.org/c/rrid/types",
            "https://app.pubpub.org/c/rrid/fields",
            "https://app.pubpub.org/c/rrid/members",
            "https://app.pubpub.org/c/rrid/settings/tokens",
            "https://app.pubpub.org/c/rrid/developers/docs#/"
        ]
        for url in urls:
            f.write(f"- [{url}]({url})\n")
            
    # Also save the raw JSON data to the config_backup directory
    pub_types_file = CONFIG_BACKUP_DIR / f"pub_types_{timestamp}.json"
    with open(pub_types_file, "w") as f:
        json.dump(pub_types_data, f, indent=2)
        
    stages_file = CONFIG_BACKUP_DIR / f"stages_{timestamp}.json"
    with open(stages_file, "w") as f:
        json.dump(stages_data, f, indent=2)
        
    print(f"✅ Report saved to {report_file}")
    print(f"✅ JSON data saved to {pub_types_file} and {stages_file}")

def test_api_endpoint(url, description):
    """Test an API endpoint and return the data"""
    print(f"\nTesting {description}...")
    print(f"Using endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data)} {description.lower()}")
            return data
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print("Response:", response.text)
            return None
    except Exception as e:
        print(f"❌ Error accessing {description}: {str(e)}")
        return None

def main():
    """Main function to test PubPub API access"""
    print(f"\nTesting PubPub API access for community: {COMMUNITY_SLUG}")
    
    # Get pub types
    pub_types_data = test_api_endpoint(pub_types_url, "Publication Types")
    if pub_types_data:
        print("\nPublication Types:")
        print(json.dumps(pub_types_data, indent=2))
    
    # Get stages
    stages_data = test_api_endpoint(stages_url, "Stages")
    if stages_data:
        print("\nStages:")
        print(json.dumps(stages_data, indent=2))
    
    # Generate report if we have both pub types and stages
    if pub_types_data and stages_data:
        save_report(pub_types_data, stages_data)
        print("\n✅ Generated configuration report with environment variable values")

if __name__ == "__main__":
    main() 