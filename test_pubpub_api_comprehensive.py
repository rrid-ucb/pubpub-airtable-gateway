#!/usr/bin/env python

import os
import json
import requests
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from airtable import Airtable
import slugify

# Create timestamp for this run
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Set up logging
log_file = f"test_run_{TIMESTAMP}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API credentials
PUBPUB_API_KEY = os.getenv("PUBPUB_API_KEY")
COMMUNITY_SLUG = os.getenv("COMMUNITY_SLUG", "rrid")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# URLs
PUBPUB_BASE_URL = f"https://app.pubpub.org/api/v0/c/{COMMUNITY_SLUG}/site"
PUBPUB_COMMUNITY_URL = f"https://app.pubpub.org/{COMMUNITY_SLUG}"
AIRTABLE_BASE_URL = f"https://airtable.com/{AIRTABLE_BASE_ID}"

# PubPub headers
headers = {
    "Authorization": f"Bearer {PUBPUB_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Pub types from environment variables
pub_types = {
    "narrative": os.getenv("NARRATIVE_TYPE_ID"),
    "type": os.getenv("TYPE_TYPE_ID"),
    "person": os.getenv("PERSON_TYPE_ID"),
    "contributor": os.getenv("CONTRIBUTOR_TYPE_ID"),
    "pub": os.getenv("PUB_TYPE_ID"),
    "institutions": os.getenv("INSTITUTIONS_TYPE_ID"),
    "roles": os.getenv("ROLES_TYPE_ID"),
    "preprint": os.getenv("PREPRINT_TYPE_ID"),
    "reviewer": os.getenv("REVIEWER_TYPE_ID")
}

# Stages from environment variables
stages = {
    "airtable": os.getenv("AIRTABLE_STAGE_ID"),
    "nonPubs": os.getenv("NONPUBS_STAGE_ID")
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
    url = f"{PUBPUB_BASE_URL}/pub-types"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting pub types: {response.status_code}")
        print(response.text)
        return None

def get_stages():
    """Get all stages from PubPub"""
    url = f"{PUBPUB_BASE_URL}/stages"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting stages: {response.status_code}")
        print(response.text)
        return None

def get_pubs(pub_type_id=None, limit=10):
    """Get pubs from PubPub"""
    url = f"{PUBPUB_BASE_URL}/pubs"
    params = {"limit": limit}
    if pub_type_id:
        params["pubTypeId"] = pub_type_id
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting pubs: {response.status_code}")
        print(response.text)
        return None

def create_pub(pub_type_id, stage_id, field_values):
    """Create a pub in PubPub"""
    url = f"{PUBPUB_BASE_URL}/pubs"
    data = {
        "pubTypeId": pub_type_id,
        "stageId": stage_id,
        "values": field_values
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Error creating pub: {response.status_code}")
        print(response.text)
        return None

def update_pub(pub_id, field_values):
    """Update a pub in PubPub"""
    url = f"{PUBPUB_BASE_URL}/pubs/{pub_id}"
    data = field_values
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error updating pub: {response.status_code}")
        print(response.text)
        return None

def delete_pub(pub_id):
    """Delete a pub from PubPub"""
    url = f"{PUBPUB_BASE_URL}/pubs/{pub_id}"
    response = requests.delete(url, headers=headers)
    return response.status_code in [200, 204]

def update_pub_relations(pub_id, field_values):
    """Update pub relations in PubPub"""
    url = f"{PUBPUB_BASE_URL}/pubs/{pub_id}/relations"
    response = requests.put(url, headers=headers, json=field_values)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error updating pub relations: {response.status_code}")
        print(response.text)
        return None

def get_airtable_records(table_name, view_name="PubPub Platform Import"):
    """Get records from Airtable"""
    try:
        table = Airtable(AIRTABLE_BASE_ID, table_name, api_key=AIRTABLE_API_KEY)
        records = table.get_all(view=view_name)
        return records
    except Exception as e:
        print(f"Error getting Airtable records: {str(e)}")
        return None

def test_pub_types_api():
    """Test pub types API"""
    pub_types_data = get_pub_types()
    if pub_types_data:
        log_result("Get Pub Types", True, f"Found {len(pub_types_data)} pub types")
        return pub_types_data
    else:
        log_result("Get Pub Types", False, "Failed to get pub types")
        return None

def test_stages_api():
    """Test stages API"""
    stages_data = get_stages()
    if stages_data:
        log_result("Get Stages", True, f"Found {len(stages_data)} stages")
        return stages_data
    else:
        log_result("Get Stages", False, "Failed to get stages")
        return None

def test_create_person_pub():
    """Test creating a person pub"""
    # Get a person record from Airtable
    person_records = get_airtable_records("Person")
    if not person_records or len(person_records) == 0:
        log_result("Create Person Pub", False, "No person records found in Airtable")
        return None
    
    person_record = person_records[0]
    
    # Create a person pub
    field_values = {
        f"{COMMUNITY_SLUG}:full-name": person_record["fields"].get("Name", ""),
        f"{COMMUNITY_SLUG}:slug": person_record["fields"].get("Slug") or slugify.slugify(person_record["fields"].get("Name", ""), lowercase=True),
    }
    
    if "ORCID" in person_record["fields"] and person_record["fields"]["ORCID"]:
        orcid = person_record["fields"]["ORCID"]
        if slugify.slugify(orcid, lowercase=True).match(r"^(\d{4}-){3}\d{3}(\d|x)$"):
            field_values[f"{COMMUNITY_SLUG}:orcid"] = f"https://orcid.org/{orcid}"
    
    result = create_pub(pub_types["person"], stages["nonPubs"], field_values)
    if result:
        log_result("Create Person Pub", True, f"Created person pub with ID {result.get('id')}")
        return result
    else:
        log_result("Create Person Pub", False, "Failed to create person pub")
        return None

def test_create_institution_pub():
    """Test creating an institution pub"""
    # Get an institution record from Airtable
    institution_records = get_airtable_records("Institution")
    if not institution_records or len(institution_records) == 0:
        log_result("Create Institution Pub", False, "No institution records found in Airtable")
        return None
    
    institution_record = institution_records[0]
    
    # Create an institution pub
    field_values = {
        f"{COMMUNITY_SLUG}:title": institution_record["fields"].get("Name", ""),
    }
    
    result = create_pub(pub_types["institutions"], stages["nonPubs"], field_values)
    if result:
        log_result("Create Institution Pub", True, f"Created institution pub with ID {result.get('id')}")
        return result
    else:
        log_result("Create Institution Pub", False, "Failed to create institution pub")
        return None

def test_create_role_pub():
    """Test creating a role pub"""
    # Get a role record from Airtable
    role_records = get_airtable_records("Contributor roles")
    if not role_records or len(role_records) == 0:
        log_result("Create Role Pub", False, "No role records found in Airtable")
        return None
    
    role_record = role_records[0]
    
    # Create a role pub
    field_values = {
        f"{COMMUNITY_SLUG}:title": role_record["fields"].get("Role", ""),
        f"{COMMUNITY_SLUG}:byline-role": role_record["fields"].get("Byline", ""),
    }
    
    result = create_pub(pub_types["roles"], stages["nonPubs"], field_values)
    if result:
        log_result("Create Role Pub", True, f"Created role pub with ID {result.get('id')}")
        return result
    else:
        log_result("Create Role Pub", False, "Failed to create role pub")
        return None

def test_create_contributor_pub(person_pub, institution_pub, role_pub):
    """Test creating a contributor pub with relations"""
    # Get a contributor record from Airtable
    contributor_records = get_airtable_records("Role assignments")
    if not contributor_records or len(contributor_records) == 0:
        log_result("Create Contributor Pub", False, "No contributor records found in Airtable")
        return None
    
    contributor_record = contributor_records[0]
    
    # Create a contributor pub
    field_values = {
        f"{COMMUNITY_SLUG}:full-name": contributor_record["fields"].get("Contributors", ""),
    }
    
    result = create_pub(pub_types["contributor"], stages["nonPubs"], field_values)
    if not result:
        log_result("Create Contributor Pub", False, "Failed to create contributor pub")
        return None
    
    # Update relations
    relations = {}
    
    if person_pub:
        relations[f"{COMMUNITY_SLUG}:contributor-person"] = [
            {"value": None, "relatedPubId": person_pub["id"]}
        ]
    
    if institution_pub:
        relations[f"{COMMUNITY_SLUG}:affiliations"] = [
            {"value": None, "relatedPubId": institution_pub["id"]}
        ]
    
    if role_pub:
        relations[f"{COMMUNITY_SLUG}:roles"] = [
            {"value": None, "relatedPubId": role_pub["id"]}
        ]
    
    if relations:
        relation_result = update_pub_relations(result["id"], relations)
        if relation_result:
            log_result("Create Contributor Pub", True, f"Created contributor pub with ID {result.get('id')} and relations")
        else:
            log_result("Create Contributor Pub", False, f"Created contributor pub with ID {result.get('id')} but failed to update relations")
    else:
        log_result("Create Contributor Pub", True, f"Created contributor pub with ID {result.get('id')}")
    
    return result

def test_create_preprint_pub():
    """Test creating a preprint pub"""
    # Get a preprint record from Airtable
    preprint_records = get_airtable_records("Preprint Info ONLY")
    if not preprint_records or len(preprint_records) == 0:
        log_result("Create Preprint Pub", False, "No preprint records found in Airtable")
        return None
    
    preprint_record = preprint_records[0]
    
    # Create a preprint pub
    field_values = {
        f"{COMMUNITY_SLUG}:title": preprint_record["fields"].get("Title (from Selected)", ""),
        f"{COMMUNITY_SLUG}:abstract": preprint_record["fields"].get("Abstract", ""),
        f"{COMMUNITY_SLUG}:domain": preprint_record["fields"].get("Domain", ""),
        f"{COMMUNITY_SLUG}:team": preprint_record["fields"].get("Team/Domain", ""),
        f"{COMMUNITY_SLUG}:slug": preprint_record["fields"].get("Slug") or slugify.slugify(preprint_record["fields"].get("Title (from Selected)", ""), lowercase=True),
    }
    
    if "Link/DOI (from Selected)" in preprint_record["fields"]:
        doi_url = preprint_record["fields"]["Link/DOI (from Selected)"]
        field_values[f"{COMMUNITY_SLUG}:doi-url"] = doi_url
        if doi_url and "https://doi.org/" in doi_url:
            field_values[f"{COMMUNITY_SLUG}:doi"] = doi_url.split("https://doi.org/")[1]
    
    if "Author Email" in preprint_record["fields"]:
        field_values[f"{COMMUNITY_SLUG}:author-email"] = preprint_record["fields"]["Author Email"]
    
    if "Preprint ID" in preprint_record["fields"]:
        field_values[f"{COMMUNITY_SLUG}:preprint-id"] = preprint_record["fields"]["Preprint ID"]
    
    result = create_pub(pub_types["preprint"], stages["airtable"], field_values)
    if result:
        log_result("Create Preprint Pub", True, f"Created preprint pub with ID {result.get('id')}")
        return result
    else:
        log_result("Create Preprint Pub", False, "Failed to create preprint pub")
        return None

def test_create_reviewer_pub(preprint_pub):
    """Test creating a reviewer pub with relations"""
    # Get a reviewer record from Airtable
    reviewer_records = get_airtable_records("Student Reviewer Inputs")
    if not reviewer_records or len(reviewer_records) == 0:
        log_result("Create Reviewer Pub", False, "No reviewer records found in Airtable")
        return None
    
    reviewer_record = reviewer_records[0]
    
    # Create a reviewer pub
    field_values = {
        f"{COMMUNITY_SLUG}:reviewer-name": reviewer_record["fields"].get("First + Last Name", ""),
        f"{COMMUNITY_SLUG}:email": reviewer_record["fields"].get("Reviewer Email", ""),
        f"{COMMUNITY_SLUG}:justification-for-invite": reviewer_record["fields"].get("Justification for Invite", ""),
        f"{COMMUNITY_SLUG}:affiliation": reviewer_record["fields"].get("Affiliation", ""),
        f"{COMMUNITY_SLUG}:reviewer-title": reviewer_record["fields"].get("Reviewer Title", ""),
        f"{COMMUNITY_SLUG}:highest-degree": reviewer_record["fields"].get("Highest Degree", ""),
        f"{COMMUNITY_SLUG}:subdiscipline": reviewer_record["fields"].get("Subdiscipline", ""),
        f"{COMMUNITY_SLUG}:link-to-profile": reviewer_record["fields"].get("Link to Profile", ""),
        f"{COMMUNITY_SLUG}:slug": reviewer_record["fields"].get("Slug") or slugify.slugify(
            f"{reviewer_record['fields'].get('First Name (Proposed Reviewer)', '')}-{reviewer_record['fields'].get('Last Name (Proposed Reviewer)', '')}", 
            lowercase=True
        ),
    }
    
    result = create_pub(pub_types["reviewer"], stages["airtable"], field_values)
    if not result:
        log_result("Create Reviewer Pub", False, "Failed to create reviewer pub")
        return None
    
    # Update relations if preprint pub exists
    if preprint_pub:
        relations = {
            f"{COMMUNITY_SLUG}:associated-preprint": [
                {"value": None, "relatedPubId": preprint_pub["id"]}
            ]
        }
        relation_result = update_pub_relations(result["id"], relations)
        if relation_result:
            log_result("Create Reviewer Pub", True, f"Created reviewer pub with ID {result.get('id')} and relations")
        else:
            log_result("Create Reviewer Pub", False, f"Created reviewer pub with ID {result.get('id')} but failed to update relations")
    else:
        log_result("Create Reviewer Pub", True, f"Created reviewer pub with ID {result.get('id')}")
    
    return result

def test_update_pub(pub_id):
    """Test updating a pub"""
    if not pub_id:
        log_result("Update Pub", False, "No pub ID provided")
        return False
    
    # Update the pub
    field_values = {
        f"{COMMUNITY_SLUG}:title": f"Updated Title {int(time.time())}"
    }
    
    result = update_pub(pub_id, field_values)
    if result:
        log_result("Update Pub", True, f"Updated pub with ID {pub_id}")
        return True
    else:
        log_result("Update Pub", False, f"Failed to update pub with ID {pub_id}")
        return False

def test_delete_pub(pub_id):
    """Test deleting a pub"""
    if not pub_id:
        log_result("Delete Pub", False, "No pub ID provided")
        return False
    
    # Delete the pub
    result = delete_pub(pub_id)
    if result:
        log_result("Delete Pub", True, f"Deleted pub with ID {pub_id}")
        return True
    else:
        log_result("Delete Pub", False, f"Failed to delete pub with ID {pub_id}")
        return False

def generate_report():
    """Generate a markdown report of the test run"""
    report_file = f"REPORT-{TIMESTAMP}.md"
    
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

def run_all_tests():
    """Run all tests"""
    logger.info("Starting PubPub API tests...")
    
    # Test pub types API
    pub_types_data = test_pub_types_api()
    
    # Test stages API
    stages_data = test_stages_api()
    
    # Test creating person pub
    person_pub = test_create_person_pub()
    
    # Test creating institution pub
    institution_pub = test_create_institution_pub()
    
    # Test creating role pub
    role_pub = test_create_role_pub()
    
    # Test creating contributor pub with relations
    contributor_pub = test_create_contributor_pub(person_pub, institution_pub, role_pub)
    
    # Test creating preprint pub
    preprint_pub = test_create_preprint_pub()
    
    # Test creating reviewer pub with relations
    reviewer_pub = test_create_reviewer_pub(preprint_pub)
    
    # Test updating a pub
    if person_pub:
        test_update_pub(person_pub["id"])
    
    # Test deleting a pub
    if person_pub:
        test_delete_pub(person_pub["id"])
    
    # Print test results summary
    logger.info("\nTest Results Summary:")
    logger.info(f"✅ Successful tests: {len(test_results['success'])}")
    logger.info(f"❌ Failed tests: {len(test_results['failure'])}")
    
    if test_results["failure"]:
        logger.error("\nFailed Tests:")
        for test in test_results["failure"]:
            logger.error(f"  - {test['test']}: {test['message']}")
    
    # Generate report
    generate_report()
    logger.info(f"\nTest report generated: REPORT-{TIMESTAMP}.md")
    
    return test_results

if __name__ == "__main__":
    run_all_tests() 