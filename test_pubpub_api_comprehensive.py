#!/usr/bin/env python3

import os
import json
import requests
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from airtable import Airtable
from slugify import slugify
from pathlib import Path

# Directory paths
REPORTS_DIR = Path("reports")
LOGS_DIR = Path("logs")
OUTPUT_DIR = Path("output")
DATA_BACKUP_DIR = Path("data_backup")

# Create directories if they don't exist
REPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
DATA_BACKUP_DIR.mkdir(exist_ok=True)

# Load environment variables
load_dotenv()

# Constants
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
COMMUNITY_SLUG = "rrid"
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
PUBPUB_API_KEY = os.getenv("PUBPUB_API_KEY")

# Setup logging
log_file = LOGS_DIR / f"test_run_{TIMESTAMP}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# URLs
PUBPUB_BASE_URL = f"https://app.pubpub.org/api/v0/c/{COMMUNITY_SLUG}/site"
PUBPUB_COMMUNITY_URL = f"https://app.pubpub.org/{COMMUNITY_SLUG}"
AIRTABLE_BASE_URL = f"https://airtable.com/{AIRTABLE_BASE_ID}"

# PubPub headers
PUBPUB_HEADERS = {
    "Authorization": f"Bearer {PUBPUB_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Test results
test_results = {
    "success": [],
    "failure": [],
    "created_pubs": [],
    "airtable_sources": {}
}

def log_result(test_name, success, message=None, pub_data=None, airtable_data=None):
    """Log test results"""
    result = {
        "test": test_name,
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if pub_data:
        result["pub_data"] = pub_data
        if success and "id" in pub_data:
            test_results["created_pubs"].append({
                "type": test_name,
                "id": pub_data["id"],
                "url": f"{PUBPUB_COMMUNITY_URL}/pub/{pub_data.get('slug', pub_data['id'])}"
            })
    
    if airtable_data:
        result["airtable_data"] = airtable_data
        if "table" in airtable_data:
            test_results["airtable_sources"][test_name] = {
                "table": airtable_data["table"],
                "url": f"{AIRTABLE_BASE_URL}/{airtable_data['table']}"
            }
    
    if success:
        test_results["success"].append(result)
        logger.info(f"✅ {test_name}: {message if message else ''}")
    else:
        test_results["failure"].append(result)
        logger.error(f"❌ {test_name}: {message if message else ''}")

def get_pub_types():
    """Get all pub types from PubPub"""
    try:
        response = requests.get(f"{PUBPUB_BASE_URL}/pub-types", headers=PUBPUB_HEADERS)
        response.raise_for_status()
        pub_types = response.json()
        log_result("Get Pub Types", True, f"Found {len(pub_types)} pub types", pub_types)
        return pub_types
    except Exception as e:
        log_result("Get Pub Types", False, str(e))
        return None

def get_stages():
    """Get all stages from PubPub"""
    try:
        response = requests.get(f"{PUBPUB_BASE_URL}/stages", headers=PUBPUB_HEADERS)
        response.raise_for_status()
        stages = response.json()
        log_result("Get Stages", True, f"Found {len(stages)} stages", stages)
        return stages
    except Exception as e:
        log_result("Get Stages", False, str(e))
        return None

def get_airtable_records(table_name, view_name="Grid view"):
    """Get records from Airtable"""
    try:
        table = Airtable(AIRTABLE_BASE_ID, table_name, api_key=AIRTABLE_API_KEY)
        records = table.get_all(view=view_name)
        
        # Save retrieved records to data_backup
        backup_file = DATA_BACKUP_DIR / f"airtable_{table_name.lower().replace(' ', '_')}_{TIMESTAMP}.json"
        with open(backup_file, "w") as f:
            json.dump(records, f, indent=2)
        
        return records
    except Exception as e:
        logger.error(f"Error getting Airtable records: {str(e)}")
        return None

def create_person_pub():
    """Create a person pub from Airtable data"""
    records = get_airtable_records("Person")
    if not records:
        log_result("Create Person Pub", False, "No person records found in Airtable", 
                  airtable_data={"table": "Person"})
        return None
    
    try:
        record = records[0]
        pub_data = {
            "title": record.get("Name"),
            "slug": record.get("Slug") or slugify(record.get("Name"), lower=True),
            "orcid": f"https://orcid.org/{record.get('ORCID')}" if record.get("ORCID") else None,
            "avatar": record.get("Headshot")
        }
        response = requests.post(
            f"{PUBPUB_BASE_URL}/pubs",
            headers=PUBPUB_HEADERS,
            json=pub_data
        )
        response.raise_for_status()
        pub = response.json()
        log_result("Create Person Pub", True, f"Created person pub: {pub['title']}", 
                  pub_data=pub, airtable_data={"table": "Person", "record": record})
        return pub
    except Exception as e:
        log_result("Create Person Pub", False, str(e))
        return None

def create_institution_pub():
    """Create an institution pub from Airtable data"""
    records = get_airtable_records("Institution")
    if not records:
        log_result("Create Institution Pub", False, "No institution records found in Airtable",
                  airtable_data={"table": "Institution"})
        return None
    
    try:
        record = records[0]
        pub_data = {
            "title": record.get("Name"),
            "slug": slugify(record.get("Name"), lower=True)
        }
        response = requests.post(
            f"{PUBPUB_BASE_URL}/pubs",
            headers=PUBPUB_HEADERS,
            json=pub_data
        )
        response.raise_for_status()
        pub = response.json()
        log_result("Create Institution Pub", True, f"Created institution pub: {pub['title']}", 
                  pub_data=pub, airtable_data={"table": "Institution", "record": record})
        return pub
    except Exception as e:
        log_result("Create Institution Pub", False, str(e))
        return None

def create_role_pub():
    """Create a role pub from Airtable data"""
    records = get_airtable_records("Contributor roles")
    if not records:
        log_result("Create Role Pub", False, "No role records found in Airtable",
                  airtable_data={"table": "Contributor roles"})
        return None
    
    try:
        record = records[0]
        pub_data = {
            "title": record.get("Role"),
            "byline-role": record.get("Byline"),
            "slug": slugify(record.get("Role"), lower=True)
        }
        response = requests.post(
            f"{PUBPUB_BASE_URL}/pubs",
            headers=PUBPUB_HEADERS,
            json=pub_data
        )
        response.raise_for_status()
        pub = response.json()
        log_result("Create Role Pub", True, f"Created role pub: {pub['title']}", 
                  pub_data=pub, airtable_data={"table": "Contributor roles", "record": record})
        return pub
    except Exception as e:
        log_result("Create Role Pub", False, str(e))
        return None

def create_contributor_pub(person_pub=None, institution_pub=None, role_pub=None):
    """Create a contributor pub from Airtable data with relationships"""
    records = get_airtable_records("Role assignments")
    if not records:
        log_result("Create Contributor Pub", False, "No contributor records found in Airtable",
                  airtable_data={"table": "Role assignments"})
        return None
    
    try:
        record = records[0]
        pub_data = {
            "title": record.get("Contributors"),
            "slug": slugify(record.get("Contributors"), lower=True)
        }
        
        # Add relationships if we have the related pubs
        relations = {}
        if person_pub:
            relations["contributor-person"] = [{"relatedPubId": person_pub["id"]}]
        if institution_pub:
            relations["affiliations"] = [{"relatedPubId": institution_pub["id"]}]
        if role_pub:
            relations["roles"] = [{"relatedPubId": role_pub["id"]}]
        
        response = requests.post(
            f"{PUBPUB_BASE_URL}/pubs",
            headers=PUBPUB_HEADERS,
            json=pub_data
        )
        response.raise_for_status()
        pub = response.json()
        
        # Update relations if we have any
        if relations:
            response = requests.put(
                f"{PUBPUB_BASE_URL}/pubs/{pub['id']}/relations",
                headers=PUBPUB_HEADERS,
                json=relations
            )
            response.raise_for_status()
        
        log_result("Create Contributor Pub", True, f"Created contributor pub: {pub['title']}", 
                  pub_data=pub, airtable_data={"table": "Role assignments", "record": record})
        return pub
    except Exception as e:
        log_result("Create Contributor Pub", False, str(e))
        return None

def create_preprint_pub():
    """Create a preprint pub from Airtable data"""
    records = get_airtable_records("Preprint Info ONLY")
    if not records:
        log_result("Create Preprint Pub", False, "No preprint records found in Airtable",
                  airtable_data={"table": "Preprint Info ONLY"})
        return None
    
    try:
        record = records[0]
        pub_data = {
            "title": record.get("Title"),
            "slug": record.get("Slug") or slugify(record.get("Title"), lower=True),
            "doi": record.get("DOI"),
            "publication-date": record.get("Publication date"),
            "google-drive-folder-url": record.get("Link to folder with assets"),
            "typeform-url": record.get("Typeform link")
        }
        response = requests.post(
            f"{PUBPUB_BASE_URL}/pubs",
            headers=PUBPUB_HEADERS,
            json=pub_data
        )
        response.raise_for_status()
        pub = response.json()
        log_result("Create Preprint Pub", True, f"Created preprint pub: {pub['title']}", 
                  pub_data=pub, airtable_data={"table": "Preprint Info ONLY", "record": record})
        return pub
    except Exception as e:
        log_result("Create Preprint Pub", False, str(e))
        return None

def create_reviewer_pub():
    """Create a reviewer pub from Airtable data"""
    records = get_airtable_records("Student Reviewer Inputs")
    if not records:
        log_result("Create Reviewer Pub", False, "No reviewer records found in Airtable",
                  airtable_data={"table": "Student Reviewer Inputs"})
        return None
    
    try:
        record = records[0]
        pub_data = {
            "title": record.get("Name"),
            "slug": slugify(record.get("Name"), lower=True),
            "feedback-status": record.get("Current feedback status"),
            "author-email": record.get("Point person email")
        }
        response = requests.post(
            f"{PUBPUB_BASE_URL}/pubs",
            headers=PUBPUB_HEADERS,
            json=pub_data
        )
        response.raise_for_status()
        pub = response.json()
        log_result("Create Reviewer Pub", True, f"Created reviewer pub: {pub['title']}", 
                  pub_data=pub, airtable_data={"table": "Student Reviewer Inputs", "record": record})
        return pub
    except Exception as e:
        log_result("Create Reviewer Pub", False, str(e))
        return None

def generate_report():
    """Generate a markdown report of the test run"""
    report_file = REPORTS_DIR / f"REPORT-{TIMESTAMP}.md"
    
    with open(report_file, "w") as f:
        f.write(f"# PubPub API Test Report\n\n")
        f.write(f"Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Test Summary\n\n")
        f.write(f"- Total tests: {len(test_results['success']) + len(test_results['failure'])}\n")
        f.write(f"- Successful tests: {len(test_results['success'])}\n")
        f.write(f"- Failed tests: {len(test_results['failure'])}\n\n")
        
        if test_results["created_pubs"]:
            f.write("## Created Publications\n\n")
            f.write("| Type | PubPub URL |\n")
            f.write("|------|------------|\n")
            for pub in test_results["created_pubs"]:
                f.write(f"| {pub['type']} | [{pub['id']}]({pub['url']}) |\n")
            f.write("\n")
        
        if test_results["airtable_sources"]:
            f.write("## Airtable Data Sources\n\n")
            f.write("| Test Type | Airtable Table |\n")
            f.write("|-----------|----------------|\n")
            for test_name, source in test_results["airtable_sources"].items():
                f.write(f"| {test_name} | [{source['table']}]({source['url']}) |\n")
            f.write("\n")
        
        if test_results["failure"]:
            f.write("## Failed Tests\n\n")
            for test in test_results["failure"]:
                f.write(f"### {test['test']}\n")
                f.write(f"- Time: {test['timestamp']}\n")
                f.write(f"- Error: {test['message']}\n\n")
        
        f.write("## What to Expect in PubPub\n\n")
        f.write("After this test run, you should see the following in your PubPub community:\n\n")
        f.write(f"1. Visit your community at: {PUBPUB_COMMUNITY_URL}\n")
        f.write("2. You should see new publications created for:\n")
        for pub in test_results["created_pubs"]:
            f.write(f"   - {pub['type']}: [{pub['id']}]({pub['url']})\n")
        f.write("\n3. Each publication should have the fields and relationships as defined in the test cases.\n")
        
        f.write("\n## Log File\n\n")
        f.write(f"For detailed logs, see: `{log_file}`\n")
    
    # Also save the test results as JSON for later analysis
    results_file = OUTPUT_DIR / f"test_results_{TIMESTAMP}.json"
    with open(results_file, "w") as f:
        json.dump(test_results, f, indent=2)
    
    logger.info(f"Report saved to {report_file}")
    logger.info(f"Test results saved to {results_file}")
    
    return report_file

def main():
    """Run all tests"""
    logger.info("Starting PubPub API tests...")
    
    # Get pub types and stages
    pub_types = get_pub_types()
    stages = get_stages()
    
    # Create pubs in order of dependencies
    person_pub = create_person_pub()
    institution_pub = create_institution_pub()
    role_pub = create_role_pub()
    
    # Create contributor pub with relationships
    contributor_pub = create_contributor_pub(person_pub, institution_pub, role_pub)
    
    # Create preprint and reviewer pubs
    preprint_pub = create_preprint_pub()
    reviewer_pub = create_reviewer_pub()
    
    # Generate test report
    logger.info("\nTest Results Summary:")
    logger.info(f"✅ Successful tests: {len(test_results['success'])}")
    logger.info(f"❌ Failed tests: {len(test_results['failure'])}")
    
    if test_results["failure"]:
        logger.error("\nFailed Tests:")
        for test in test_results["failure"]:
            logger.error(f"  - {test['test']}: {test['message']}")
    
    report_file = generate_report()
    logger.info(f"\nTest report generated: {report_file}")

if __name__ == "__main__":
    main() 