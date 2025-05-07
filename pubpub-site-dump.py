#!/usr/bin/env python

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any

# Directory paths
REPORTS_DIR = Path("reports")
CONFIG_BACKUP_DIR = Path("config_backup")
LOGS_DIR = Path("logs")
OUTPUT_DIR = Path("output")

# Create directories if they don't exist
REPORTS_DIR.mkdir(exist_ok=True)
CONFIG_BACKUP_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Load environment variables
load_dotenv()

# API credentials from environment
API_KEY = os.getenv("PUBPUB_API_KEY")
COMMUNITY_SLUG = os.getenv("COMMUNITY_SLUG", "rrid")

if not API_KEY:
    raise ValueError("PUBPUB_API_KEY environment variable is not set")

# Create timestamp for this dump
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Create dump directory
DUMP_DIR = Path(f"pubpub_dump_{TIMESTAMP}")
DUMP_DIR.mkdir(exist_ok=True)

# API endpoints
BASE_URL = f"https://app.pubpub.org/api/v0/c/{COMMUNITY_SLUG}/site"
ENDPOINTS = {
    "pub_types": "/pub-types",
    "stages": "/stages",
    "pubs": "/pubs",
    "members": "/members",
    "fields": "/fields",
    "forms": "/forms",
    "actions": "/actions",
    "workflows": "/workflows",
    "settings": "/settings",
    "collections": "/collections",
    "tags": "/tags"
}

# Headers
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")

def save_json(data: Any, filename: str) -> None:
    """Save data to a JSON file with pretty printing"""
    filepath = DUMP_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {filename}")
    
    # Also save to CONFIG_BACKUP_DIR for important configuration files
    if filename in ["pub_types.json", "stages.json", "fields.json"]:
        backup_filename = f"{filename.split('.')[0]}_{TIMESTAMP}.json"
        backup_filepath = CONFIG_BACKUP_DIR / backup_filename
        with open(backup_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Backup saved to {backup_filepath}")

def fetch_data(endpoint: str, description: str) -> Optional[Any]:
    """Fetch data from an API endpoint with improved error handling"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\nFetching {description}...")
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data) if isinstance(data, list) else 1} items")
            return data
        elif response.status_code == 404:
            print(f"ℹ️ {description} endpoint not available")
            return None
        else:
            print(f"❌ Error {response.status_code} accessing {description}")
            return None
    except Exception as e:
        print(f"❌ Error accessing {description}: {str(e)}")
        return None

def fetch_pub_details(pub_id: str) -> Optional[Dict]:
    """Fetch detailed information for a specific pub"""
    url = f"{BASE_URL}/pubs/{pub_id}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def generate_workflow_diagram(stages: List[Dict]) -> str:
    """Generate a Mermaid diagram of the workflow stages"""
    mermaid = ["```mermaid", "graph LR"]
    
    # Track processed connections to avoid duplicates
    processed = set()
    
    # Add nodes
    for stage in stages:
        stage_id = stage["id"]
        stage_name = stage["name"].replace(" ", "_")
        mermaid.append(f'    {stage_id}["{stage["name"]}"]')
        
        # Add connections based on moveConstraints
        for constraint in stage.get("moveConstraints", []):
            connection = f"{stage_id}-->{constraint['id']}"
            if connection not in processed:
                target_name = next((s["name"] for s in stages if s["id"] == constraint["id"]), "Unknown")
                mermaid.append(f'    {stage_id}-->|"can move to"| {constraint["id"]}["{target_name}"]')
                processed.add(connection)
    
    mermaid.append("```")
    return "\n".join(mermaid)

def generate_stage_stats(stages: List[Dict]) -> str:
    """Generate a markdown table of stage statistics"""
    stats = ["## Stage Statistics\n"]
    stats.append("| Stage | Pubs | Actions | Members |")
    stats.append("|-------|------|----------|----------|")
    
    for stage in stages:
        name = stage["name"]
        pubs = stage.get("pubsCount", 0)
        actions = stage.get("actionInstancesCount", 0)
        members = stage.get("memberCount", 0)
        stats.append(f"| {name} | {pubs} | {actions} | {members} |")
    
    return "\n".join(stats)

def generate_report(stages: Optional[List[Dict]] = None) -> None:
    """Generate a markdown report of the dump"""
    report_file = DUMP_DIR / "DUMP_REPORT.md"
    
    with open(report_file, "w") as f:
        f.write(f"# PubPub Site Dump Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Community: {COMMUNITY_SLUG}\n\n")
        
        # List all dumped files
        f.write("## Dumped Files\n\n")
        for file in sorted(DUMP_DIR.glob("*.json")):
            f.write(f"- [{file.name}](./{file.name})\n")
        
        # Add workflow visualization if stages data is available
        if stages:
            f.write("\n## Workflow Visualization\n\n")
            f.write(generate_workflow_diagram(stages))
            f.write("\n\n")
            f.write(generate_stage_stats(stages))
            f.write("\n\n")
        
        # Add site URLs
        f.write("\n## Site URLs\n\n")
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
    
    # Also save a copy to the REPORTS_DIR
    report_copy_file = REPORTS_DIR / f"pubpub_dump_report_{TIMESTAMP}.md"
    with open(report_copy_file, "w") as f:
        f.write(f"# PubPub Site Dump Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Community: {COMMUNITY_SLUG}\n\n")
        f.write(f"Original dump directory: {DUMP_DIR}\n\n")
        
        # List all dumped files
        f.write("## Dumped Files\n\n")
        for file in sorted(DUMP_DIR.glob("*.json")):
            f.write(f"- {file.name}\n")
        
        # Add workflow visualization if stages data is available
        if stages:
            f.write("\n## Workflow Visualization\n\n")
            f.write(generate_workflow_diagram(stages))
            f.write("\n\n")
            f.write(generate_stage_stats(stages))
            f.write("\n\n")
        
        # Add site URLs
        f.write("\n## Site URLs\n\n")
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
    
    print(f"✅ Report saved to {report_file}")
    print(f"✅ Report copy saved to {report_copy_file}")

def main():
    """Main function to dump all site data"""
    print(f"\nStarting PubPub site dump for community: {COMMUNITY_SLUG}")
    print(f"Dump directory: {DUMP_DIR}")
    
    # Setup a log file
    log_file = LOGS_DIR / f"pubpub_dump_{TIMESTAMP}.log"
    print(f"Log file: {log_file}")
    
    # Dictionary to store all fetched data
    data = {}
    
    # Fetch data for each endpoint
    for endpoint_name, endpoint_path in ENDPOINTS.items():
        result = fetch_data(endpoint_path, endpoint_name.replace("_", " ").title())
        if result:
            data[endpoint_name] = result
            save_json(result, f"{endpoint_name}.json")
    
    # Fetch detailed pub information if pubs exist
    if "pubs" in data and data["pubs"]:
        print("\nFetching detailed information for each publication...")
        pub_details = {}
        for pub in data["pubs"]:
            pub_id = pub["id"]
            print(f"Fetching details for pub {pub_id}...")
            details = fetch_pub_details(pub_id)
            if details:
                pub_details[pub_id] = details
        
        if pub_details:
            save_json(pub_details, "pubs_details.json")
    
    # Generate report with workflow visualization if stages data is available
    generate_report(data.get("stages"))
    print(f"\n✅ Site dump completed! Check {DUMP_DIR} for the files.")

if __name__ == "__main__":
    main() 