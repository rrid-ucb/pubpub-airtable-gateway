#! /usr/bin/env python

import os
import json
import pickle
from pathlib import Path
from datetime import datetime
import requests
from dotenv import load_dotenv
from typing import Dict, Any, List
import re

# Load environment variables
load_dotenv()

# Configuration
COMMUNITY_SLUG = "rrid"  # Hardcode to rrid since that's what we want
API_KEY = os.getenv("PUBPUB_API_KEY_RRID")  # Always use the RRID key

if not API_KEY:
    raise ValueError("PUBPUB_API_KEY_RRID environment variable is not set")

# Constants
CACHE_DIR = Path("cache")
MAPPINGS_FILE = CACHE_DIR / "suggested_mappings.json"
SAMPLE_DATA_FILE = CACHE_DIR / "airtable_samples.pickle"
BASE_URL = f"https://app.pubpub.org/api/v0/c/{COMMUNITY_SLUG}/site"
PUBS_URL = f"{BASE_URL}/pubs"
PUB_TYPES_URL = f"{BASE_URL}/pub-types"

# Headers
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Table to PubPub type mapping rules
TABLE_TYPE_MAPPING = {
    "preprint": [
        r"preprint",
        r"article",
        r"manuscript",
        r"paper",
        r"publication"
    ],
    "review": [
        r"review",
        r"referee",
        r"evaluation",
        r"assessment"
    ]
}

# Field mapping rules
FIELD_MAPPING_RULES = {
    "title": [
        r"title",
        r"name",
        r"heading",
        r"subject"
    ],
    "description": [
        r"description",
        r"abstract",
        r"summary",
        r"notes"
    ],
    "pubTypeId": [
        r"type",
        r"category",
        r"kind"
    ],
    "relations": [
        r"related",
        r"link",
        r"reference",
        r"parent",
        r"child"
    ],
    "status": [
        r"status",
        r"state",
        r"phase"
    ],
    "assignee": [
        r"assignee",
        r"owner",
        r"responsible"
    ],
    "author": [
        r"author",
        r"creator",
        r"contributor"
    ],
    "email": [
        r"email",
        r"contact",
        r"mail"
    ],
    "url": [
        r"url",
        r"link",
        r"website"
    ],
    "date": [
        r"date",
        r"created",
        r"updated",
        r"timestamp"
    ]
}

def get_pub_types():
    """Get available pub types from PubPub"""
    print("📚 Fetching PubPub publication types...")
    try:
        response = requests.get(PUB_TYPES_URL, headers=HEADERS)
        response.raise_for_status()
        pub_types = response.json()
        
        print(f"Found {len(pub_types)} pub types:")
        for pub_type in pub_types:
            print(f"- {pub_type['name']} (ID: {pub_type['id']})")
            if pub_type.get("fields"):
                print("  Fields:")
                for field in pub_type["fields"]:
                    print(f"    - {field.get('name')} ({field.get('type')})")
        
        return pub_types
    except Exception as e:
        print(f"❌ Error fetching pub types: {str(e)}")
        if hasattr(e, 'response'):
            print("Response:", e.response.text)
        return None

def load_cached_data():
    """Load the cached mappings and sample data"""
    print("📂 Loading cached data...")
    
    if not MAPPINGS_FILE.exists():
        raise FileNotFoundError(f"Mappings file not found: {MAPPINGS_FILE}")
    if not SAMPLE_DATA_FILE.exists():
        raise FileNotFoundError(f"Sample data file not found: {SAMPLE_DATA_FILE}")
    
    with open(MAPPINGS_FILE, 'r') as f:
        mappings = json.load(f)
    
    with open(SAMPLE_DATA_FILE, 'rb') as f:
        sample_data = pickle.load(f)
    
    return mappings, sample_data

def format_field_value(value: Any, field_type: str) -> Any:
    """Format a field value based on its type"""
    if value is None:
        return None
    
    if field_type == "singleSelect":
        return str(value)
    elif field_type == "multipleSelects":
        return [str(v) for v in value] if isinstance(value, list) else [str(value)]
    elif field_type == "date":
        # Convert to ISO format if it's a date string
        try:
            date_obj = datetime.strptime(value, "%Y-%m-%d")
            return date_obj.isoformat()
        except:
            return value
    elif field_type == "dateTime":
        # Ensure datetime is in ISO format
        try:
            if isinstance(value, str):
                date_obj = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return date_obj.isoformat()
            return value
        except:
            return value
    elif field_type == "multilineText":
        return str(value)
    elif field_type == "richText":
        # Convert rich text to plain text for now
        # TODO: Implement proper rich text handling
        return str(value)
    elif field_type == "checkbox":
        return bool(value)
    elif field_type == "number":
        try:
            return float(value)
        except:
            return None
    elif field_type == "formula":
        # Try to convert formula result to appropriate type
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, bool):
            return value
        return str(value)
    elif field_type == "multipleRecordLinks":
        # Return list of record IDs
        if isinstance(value, list):
            return [str(v) for v in value]
        return [str(value)] if value else []
    elif field_type == "multipleLookupValues":
        # Handle lookup values
        if isinstance(value, list):
            return value
        return [value] if value else []
    elif field_type == "url":
        return str(value)
    elif field_type == "email":
        return str(value)
    
    return value

def suggest_field_mapping(field_name: str, field_type: str) -> Dict[str, Any]:
    """Suggest a PubPub field mapping based on field name and type"""
    field_name_lower = field_name.lower()
    
    # Check each mapping rule
    for pubpub_field, patterns in FIELD_MAPPING_RULES.items():
        for pattern in patterns:
            if re.search(pattern, field_name_lower):
                confidence = "high" if pattern == field_name_lower else "medium"
                return {
                    "pubpub_field": pubpub_field,
                    "confidence": confidence
                }
    
    # Type-based fallback mappings
    if field_type == "multipleRecordLinks":
        return {
            "pubpub_field": "relations",
            "confidence": "medium"
        }
    elif field_type == "url":
        return {
            "pubpub_field": "url",
            "confidence": "medium"
        }
    elif field_type == "email":
        return {
            "pubpub_field": "email",
            "confidence": "medium"
        }
    
    return None

def suggest_pub_type(table_name: str, record: dict, pub_types: list) -> str:
    """Suggest a PubPub type based on table name and record content"""
    table_name_lower = table_name.lower()
    
    # Check table name against mapping rules
    for type_name, patterns in TABLE_TYPE_MAPPING.items():
        for pattern in patterns:
            if re.search(pattern, table_name_lower):
                # Find matching pub type
                for pub_type in pub_types:
                    if pub_type["name"].lower() == type_name:
                        return pub_type["id"]
    
    # Default to first available type
    return pub_types[0]["id"] if pub_types else None

def verify_pub(pub_id: str):
    """Verify that a pub exists by making a GET request"""
    verify_url = f"{PUBS_URL}/{pub_id}"
    try:
        print(f"\n🔍 Verifying pub {pub_id}...")
        print(f"GET {verify_url}")
        print(f"Using community: {COMMUNITY_SLUG}")
        print(f"Headers: {json.dumps({k: v if k != 'Authorization' else '...last 8 chars: ' + v[-8:] for k, v in HEADERS.items()}, indent=2)}")
        
        response = requests.get(verify_url, headers=HEADERS)
        response.raise_for_status()
        pub = response.json()
        
        print("✅ Successfully verified pub:")
        print(f"Title: {pub.get('title')}")
        print(f"Community: {pub.get('communityId')}")
        print(f"Type: {pub.get('pubTypeId')}")
        print(f"Values: {json.dumps(pub.get('values', {}), indent=2)}")
        return pub
    except Exception as e:
        print(f"❌ Error verifying pub: {str(e)}")
        if hasattr(e, 'response'):
            print("Response:", e.response.text)
        return None

def create_pub_from_record(table_name: str, record: dict, mappings: dict, pub_types: list):
    """Create a PubPub publication from an Airtable record using the mappings"""
    print(f"\n📝 Creating pub from {table_name} record...")
    
    # Get field mappings for this table
    table_mappings = mappings[table_name]["field_mappings"]
    
    # Suggest pub type based on table name and content
    pub_type_id = suggest_pub_type(table_name, record, pub_types)
    if not pub_type_id:
        print("❌ No pub types available")
        return None
    
    # Format values as an object with fieldSlug as key
    values = {}
    relations = []
    
    # First pass: Extract all mapped fields
    for field_id, field_info in mappings[table_name].get("fields", {}).items():
        field_value = record.get("fields", {}).get(field_id)
        
        if field_value is not None:
            # Get or suggest field mapping
            mapping = table_mappings.get(field_id)
            if not mapping:
                mapping = suggest_field_mapping(field_info["name"], field_info["type"])
                if mapping:
                    table_mappings[field_id] = mapping
            
            if mapping:
                # Format the value based on its type
                formatted_value = format_field_value(field_value, field_info["type"])
                
                if mapping["pubpub_field"] == "relations":
                    # Store relation IDs for later linking
                    relations.extend(formatted_value if isinstance(formatted_value, list) else [formatted_value])
                else:
                    # Add field to values with community slug prefix
                    field_key = f"{COMMUNITY_SLUG}:{mapping['pubpub_field']}"
                    values[field_key] = formatted_value
    
    # Extract or generate title
    title = None
    # Try to get title from mapped fields
    if f"{COMMUNITY_SLUG}:title" in values:
        title = values[f"{COMMUNITY_SLUG}:title"]
    
    # If no title found, try to find a suitable field
    if not title:
        # Look for fields that might contain good title candidates
        title_candidates = ["Name", "Title", "Subject", "ID"]
        for field_id, field_info in mappings[table_name].get("fields", {}).items():
            if field_info["name"] in title_candidates:
                field_value = record.get("fields", {}).get(field_id)
                if field_value:
                    title = str(field_value)
                    break
    
    # If still no title, use table name and record ID
    if not title:
        record_id = record.get("id", "unknown")
        title = f"{table_name} Record {record_id}"
    
    # Add timestamp to title
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = f"{title} [{timestamp}]"
    
    # Update title in values
    values[f"{COMMUNITY_SLUG}:title"] = title
    
    # Add description if not present
    if f"{COMMUNITY_SLUG}:description" not in values:
        # Try to create a meaningful description from available fields
        description_parts = []
        description_parts.append(f"Record from {table_name}")
        
        # Add a few key fields to the description
        for field_id, field_info in mappings[table_name].get("fields", {}).items():
            field_value = record.get("fields", {}).get(field_id)
            if field_value and len(description_parts) < 4:  # Limit to 3 fields
                description_parts.append(f"{field_info['name']}: {field_value}")
        
        values[f"{COMMUNITY_SLUG}:description"] = " | ".join(description_parts)
    
    # Prepare pub data with required fields
    pub_data = {
        "title": title,
        "slug": re.sub(r'[^a-z0-9-]', '', title.lower().replace(" ", "-")),
        "description": values.get(f"{COMMUNITY_SLUG}:description", f"Publication from {table_name}"),
        "isPublic": True,
        "pubTypeId": pub_type_id,
        "communityId": COMMUNITY_SLUG,
        "values": values
    }
    
    try:
        print("Pub data:", json.dumps(pub_data, indent=2))
        print(f"POST {PUBS_URL}")
        print(f"Using community: {COMMUNITY_SLUG}")
        response = requests.post(PUBS_URL, headers=HEADERS, json=pub_data)
        response.raise_for_status()
        pub = response.json()
        
        if pub:
            print("\n✅ Successfully created pub:")
            print(f"Title: {pub.get('title')}")
            print(f"ID: {pub.get('id')}")
            print(f"URL: https://app.pubpub.org/pub/{pub.get('id')}")
            print(f"Slug URL: https://app.pubpub.org/pub/{pub.get('slug')}")
            
            # Verify the pub exists
            verified_pub = verify_pub(pub.get('id'))
            if not verified_pub:
                print("⚠️ Warning: Could not verify pub after creation")
            
            # Return the created pub data and any relations to create
            return {
                "pub": pub,
                "relations": relations
            }
        return None
    except Exception as e:
        print(f"\n❌ Error creating pub: {str(e)}")
        if hasattr(e, 'response'):
            print("Response:", e.response.text)
        return None

def update_pub_relations(pub_id: str, related_ids: List[str]):
    """Update a pub's relations"""
    print(f"\n🔄 Updating relations for pub {pub_id}...")
    
    relations_url = f"{PUBS_URL}/{pub_id}/relations"
    relations_data = {
        f"{COMMUNITY_SLUG}:related": [
            {"relatedPubId": related_id}
            for related_id in related_ids
        ]
    }
    
    try:
        response = requests.patch(relations_url, headers=HEADERS, json=relations_data)
        response.raise_for_status()
        print("✅ Successfully updated relations")
        return True
    except Exception as e:
        print(f"❌ Error updating relations: {str(e)}")
        if hasattr(e, 'response'):
            print("Response:", e.response.text)
        return False

def main():
    print(f"🚀 Creating test pubs for community: {COMMUNITY_SLUG}")
    print(f"Using API endpoint: {BASE_URL}")
    print(f"Headers: {json.dumps({k: v if k != 'Authorization' else '...last 8 chars: ' + v[-8:] for k, v in HEADERS.items()}, indent=2)}")
    
    # Get available pub types
    pub_types = get_pub_types()
    if not pub_types:
        print("❌ Cannot proceed without pub types")
        return
    
    # Load cached data
    mappings, sample_data = load_cached_data()
    
    # Create test pubs from sample data
    created_pubs = []
    relations_to_update = []  # Store relations to update after all pubs are created
    
    for table_name, records in sample_data.items():
        if table_name in mappings:
            print(f"\n📊 Processing table: {table_name}")
            for record in records:  # Process all records
                result = create_pub_from_record(table_name, record, mappings, pub_types)
                if result:
                    created_pubs.append(result["pub"])
                    if result.get("relations"):
                        relations_to_update.append((result["pub"]["id"], result["relations"]))
    
    # Update relations after all pubs are created
    for pub_id, related_ids in relations_to_update:
        update_pub_relations(pub_id, related_ids)
    
    print(f"\n✨ Created {len(created_pubs)} test pubs")
    
    # Final verification of all created pubs
    print("\n🔍 Final verification of all created pubs...")
    verified_count = 0
    for pub in created_pubs:
        if verify_pub(pub.get('id')):
            verified_count += 1
    
    print(f"\n📊 Verification summary:")
    print(f"Total pubs created: {len(created_pubs)}")
    print(f"Successfully verified: {verified_count}")
    print(f"Failed to verify: {len(created_pubs) - verified_count}")

if __name__ == "__main__":
    main() 