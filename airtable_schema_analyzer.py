#! /usr/bin/env python

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from pyairtable import Api
from dotenv import load_dotenv
from typing import Dict, List, Any
import pickle

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")  # Add this to your .env file
if not AIRTABLE_API_KEY:
    raise ValueError("AIRTABLE_API_KEY environment variable is not set")
if not AIRTABLE_BASE_ID:
    raise ValueError("AIRTABLE_BASE_ID environment variable is not set")

# Constants
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
SCHEMA_CACHE_FILE = CACHE_DIR / "airtable_schema.pickle"
SAMPLE_DATA_CACHE_FILE = CACHE_DIR / "airtable_samples.pickle"
PUBPUB_SCHEMA_FILE = "PubPub-Site-building-API-Bundled.json"

class AirtableSchemaAnalyzer:
    def __init__(self):
        self.api = Api(AIRTABLE_API_KEY)
        self.base = self.api.base(AIRTABLE_BASE_ID)
        self.schema: Dict[str, Any] = {}
        self.sample_data: Dict[str, List[Dict]] = {}
        
    def fetch_schema(self):
        """Fetch schema for the specified base"""
        print("🔍 Fetching Airtable schema...")
        
        # Get metadata about the base
        base_url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
        headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
        
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        tables = response.json()["tables"]
        
        for table in tables:
            table_name = table["name"]
            print(f"📋 Analyzing table: {table_name}")
            
            # Get table schema
            fields = {}
            for field in table["fields"]:
                fields[field["id"]] = {
                    "name": field["name"],
                    "type": field["type"]
                }
            
            self.schema[table_name] = {
                "name": table_name,
                "id": table["id"],
                "fields": fields
            }
            
            # Fetch sample data
            self.fetch_sample_data(table_name, table["id"])
    
    def fetch_sample_data(self, table_name: str, table_id: str, sample_size: int = 5):
        """Fetch sample records from a table"""
        print(f"📝 Fetching sample data from {table_name}...")
        try:
            table = self.base.table(table_name)
            records = table.all(max_records=sample_size)
            self.sample_data[table_name] = records
        except Exception as e:
            print(f"⚠️ Error fetching sample data for {table_name}: {str(e)}")
    
    def analyze_pubpub_schema(self) -> Dict[str, Any]:
        """Analyze PubPub API schema for pub creation requirements"""
        print("🔍 Analyzing PubPub API schema...")
        with open(PUBPUB_SCHEMA_FILE, 'r') as f:
            schema = json.load(f)
        
        # Extract pub creation endpoint requirements
        pub_endpoints = {
            path: data
            for path, data in schema["paths"].items()
            if "/pubs" in path and "post" in data
        }
        
        # Extract required fields for pub creation
        required_fields = set()
        if "/api/v0/c/rrid/site/pubs" in pub_endpoints:
            post_schema = pub_endpoints["/api/v0/c/rrid/site/pubs"]["post"]
            if "requestBody" in post_schema:
                body_schema = post_schema["requestBody"]["content"]["application/json"]["schema"]
                required_fields.update(body_schema.get("required", []))
        
        return {
            "endpoints": pub_endpoints,
            "required_fields": list(required_fields)
        }
    
    def suggest_mappings(self) -> Dict[str, Any]:
        """Suggest mappings between Airtable fields and PubPub fields"""
        print("🔄 Generating field mapping suggestions...")
        mappings = {}
        pubpub_schema = self.analyze_pubpub_schema()
        required_fields = pubpub_schema["required_fields"]
        
        for table_name, table_info in self.schema.items():
            field_mappings = {}
            
            # Analyze fields and suggest mappings
            for field_id, field_info in table_info["fields"].items():
                field_name = field_info["name"].lower()
                field_type = field_info["type"]
                
                # Map fields based on name similarity and type compatibility
                if "title" in field_name or "name" in field_name:
                    field_mappings[field_id] = {
                        "pubpub_field": "title",
                        "confidence": "high" if "title" in field_name else "medium"
                    }
                elif "description" in field_name:
                    field_mappings[field_id] = {
                        "pubpub_field": "description",
                        "confidence": "high"
                    }
                elif "type" in field_name and field_type in ["singleSelect", "multipleSelects"]:
                    field_mappings[field_id] = {
                        "pubpub_field": "pubTypeId",
                        "confidence": "medium"
                    }
                elif field_type == "multipleRecordLinks":
                    field_mappings[field_id] = {
                        "pubpub_field": "relations",
                        "confidence": "medium"
                    }
            
            mappings[table_name] = {
                "field_mappings": field_mappings,
                "sample_record": self.sample_data.get(table_name, [])[0] if self.sample_data.get(table_name) else None
            }
        
        return mappings
    
    def save_to_cache(self):
        """Save schema and sample data to cache"""
        print("💾 Saving data to cache...")
        with open(SCHEMA_CACHE_FILE, 'wb') as f:
            pickle.dump(self.schema, f)
        
        with open(SAMPLE_DATA_CACHE_FILE, 'wb') as f:
            pickle.dump(self.sample_data, f)
    
    def load_from_cache(self) -> bool:
        """Load schema and sample data from cache if available"""
        try:
            if SCHEMA_CACHE_FILE.exists() and SAMPLE_DATA_CACHE_FILE.exists():
                print("📂 Loading data from cache...")
                with open(SCHEMA_CACHE_FILE, 'rb') as f:
                    self.schema = pickle.load(f)
                with open(SAMPLE_DATA_CACHE_FILE, 'rb') as f:
                    self.sample_data = pickle.load(f)
                return True
        except Exception as e:
            print(f"⚠️ Error loading cache: {str(e)}")
        return False

def main():
    analyzer = AirtableSchemaAnalyzer()
    
    # Try to load from cache first
    if not analyzer.load_from_cache():
        # If cache doesn't exist or is invalid, fetch fresh data
        analyzer.fetch_schema()
        analyzer.save_to_cache()
    
    # Generate and display mapping suggestions
    mappings = analyzer.suggest_mappings()
    
    # Save mapping suggestions to file
    mapping_file = CACHE_DIR / "suggested_mappings.json"
    with open(mapping_file, 'w') as f:
        json.dump(mappings, f, indent=2)
    
    print("\n📊 Schema Analysis Results:")
    print("-" * 50)
    for table_name, table_info in analyzer.schema.items():
        print(f"\nTable: {table_name}")
        print("Fields:")
        for field_id, field_info in table_info["fields"].items():
            print(f"  - {field_info['name']} ({field_info['type']})")
            if table_name in mappings:
                field_mappings = mappings[table_name]["field_mappings"]
                if field_id in field_mappings:
                    mapping = field_mappings[field_id]
                    print(f"    → Suggested PubPub mapping: {mapping['pubpub_field']} (confidence: {mapping['confidence']})")
    
    print(f"\n✅ Analysis complete! Results saved to {CACHE_DIR}/")
    print(f"  - Schema cache: {SCHEMA_CACHE_FILE}")
    print(f"  - Sample data cache: {SAMPLE_DATA_CACHE_FILE}")
    print(f"  - Suggested mappings: {mapping_file}")

if __name__ == "__main__":
    main() 