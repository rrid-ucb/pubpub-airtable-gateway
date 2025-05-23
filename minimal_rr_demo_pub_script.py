#! /usr/bin/env python

import os
import requests
import random
import string
import json
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from pprint import pprint

# Load environment variables
load_dotenv()

# API credentials from environment
#COMMUNITY_SLUG = os.getenv("COMMUNITY_SLUG", "rr-demo")
COMMUNITY_SLUG = "rrid"
API_KEY = os.getenv("PUBPUB_API_KEY_DEMO") if COMMUNITY_SLUG == "rr-demo" else os.getenv("PUBPUB_API_KEY_RRID")

if not API_KEY:
    raise ValueError("PUBPUB_API_KEY environment variable is not set")

# API endpoints
BASE_URL = f"https://app.pubpub.org/api/v0/c/{COMMUNITY_SLUG}/site"
PUBS_URL = f"{BASE_URL}/pubs"

# Headers
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def log_request_details(method, url, headers, data=None):
    """Log details about the API request"""
    print("\n🔍 API Request Details:")
    print(f"Method: {method}")
    print(f"URL: {url}")
    print("Headers:")
    for key, value in headers.items():
        # Don't show the full API key
        if key == "Authorization":
            print(f"  {key}: Bearer ...{value[-8:]}")
        else:
            print(f"  {key}: {value}")
    if data:
        print("Request Data:")
        print(json.dumps(data, indent=2))

def handle_api_error(e, context):
    """Handle API errors with detailed information"""
    print(f"\n❌ Error during {context}:")
    if isinstance(e, requests.exceptions.RequestException):
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print("Response Headers:")
            print(json.dumps(dict(e.response.headers), indent=2))
            try:
                error_detail = e.response.json()
                print("Error Response:")
                print(json.dumps(error_detail, indent=2))
            except json.JSONDecodeError:
                print("Response Text:")
                print(e.response.text)
        else:
            print(f"Error: {str(e)}")
    else:
        print(f"Unexpected error: {str(e)}")

def inspect_pub(pub):
    """Inspect and display all fields of a pub"""
    print("\n🔎 Pub Details:")
    print("-" * 50)
    print("Essential Fields:")
    essential_fields = ['id', 'title', 'slug', 'pubTypeId', 'stageId', 'values']
    for field in essential_fields:
        print(f"  {field}: {pub.get(field)}")
    
    print("\nAll Fields:")
    print(json.dumps(pub, indent=2))
    return pub

def list_pubs():
    """List all pubs in the community"""
    print(f"\n📚 Listing current pubs on {COMMUNITY_SLUG}...")
    
    try:
        log_request_details("GET", PUBS_URL, HEADERS)
        
        resp = requests.get(PUBS_URL, headers=HEADERS)
        resp.raise_for_status()
        pubs = resp.json()
        
        print("\n✅ Successfully retrieved pubs")
        print(f"Found {len(pubs)} publications:")
        
        # Get the first pub as a template
        template_pub = None
        if pubs:
            template_pub = inspect_pub(pubs[0])
        
        print("-" * 50)
        for pub in pubs:
            print(f"- Title: {pub.get('title')}")
            print(f"  ID: {pub.get('id')}")
            print(f"  Slug: {pub.get('slug', 'None')}")
            print(f"  Type ID: {pub.get('pubTypeId', 'None')}")
            print(f"  Stage ID: {pub.get('stageId', 'None')}")
            
            # Handle timestamp conversion more robustly
            created_at = pub.get('createdAt')
            if created_at:
                try:
                    if isinstance(created_at, str):
                        created_at = int(created_at)
                    timestamp = datetime.fromtimestamp(created_at/1000).strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    timestamp = "Unknown"
            else:
                timestamp = "Not available"
            print(f"  Created: {timestamp}")
            print("-" * 50)
        
        return pubs, template_pub
    except Exception as e:
        handle_api_error(e, "listing pubs")
        return None, None

def create_test_pub(template_pub=None):
    """Create a new test publication"""
    print(f"\n📝 Creating a test pub on {COMMUNITY_SLUG}...")
    
    # Generate a random title with timestamp to ensure uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    title = f"Test Pub {timestamp}_{random_suffix}"
    
    # Base the new pub data on the template if available
    data = {
        "title": title,
        "slug": title.lower().replace(" ", "-"),
        "description": "This is a test publication created via API",
        "isPublic": True,
    }
    
    if template_pub:
        # Copy essential fields from template
        data.update({
            "pubTypeId": template_pub.get("pubTypeId"),
            "stageId": template_pub.get("stageId"),
            "communityId": template_pub.get("communityId", COMMUNITY_SLUG)
        })
        
        # Format values as an object with fieldSlug as key
        values = {}
        if template_pub.get("values"):
            for value in template_pub["values"]:
                field_slug = value["fieldSlug"]
                # Update the value with our new title if it's the title field
                if field_slug == "rrid:title":
                    values[field_slug] = title
                else:
                    values[field_slug] = value["value"]
        
        data["values"] = values
    
    try:
        log_request_details("POST", PUBS_URL, HEADERS, data)
        
        resp = requests.post(PUBS_URL, headers=HEADERS, json=data)
        resp.raise_for_status()
        pub = resp.json()
        
        print("\n✅ Successfully created new pub:")
        print("-" * 50)
        print(f"Title: {pub.get('title')}")
        print(f"ID: {pub.get('id')}")
        print(f"Slug: {pub.get('slug')}")
        print(f"URL: https://app.pubpub.org/pub/{pub.get('slug')}")
        print("-" * 50)
        
        return pub
    except Exception as e:
        handle_api_error(e, "creating pub")
        return None

if __name__ == "__main__":
    print(f"🚀 Running PubPub API script for community: {COMMUNITY_SLUG}")
    print(f"Using API endpoint: {BASE_URL}")
    
    existing_pubs, template_pub = list_pubs()
    if existing_pubs is not None and template_pub is not None:
        new_pub = create_test_pub(template_pub)