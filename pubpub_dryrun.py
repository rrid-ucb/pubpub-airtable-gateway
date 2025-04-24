#!/usr/bin/env python3

import os
import json
import requests
import logging
import argparse
import sys
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import glob

# Import the mock data generator
from airtable_mock_data import save_mock_data

# Generate a timestamp for logs and output files
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Set up logging
def setup_logging(debug=False):
    """Set up logging configuration."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/pubpub_dryrun_{timestamp}.log"
    
    log_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('pubpub_dryrun')
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger

# Load environment variables
load_dotenv()
PUBPUB_API_KEY = os.getenv("PUBPUB_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

# PubPub API setup
def setup_pubpub_api(community_slug):
    """Set up the PubPub API configuration for a specific community"""
    api_base_url = "https://api.pubpub.org/communities/"
    
    headers = {
        "Authorization": f"Bearer {PUBPUB_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    return {
        "base_url": api_base_url + community_slug,
        "headers": headers,
        "community_slug": community_slug
    }

# Get current PubPub configuration
def get_pubpub_config(api_config, logger):
    """Get the current configuration from PubPub for a specific community"""
    config = {
        "pub_types": [],
        "stages": [],
        "fields": []
    }
    
    # Get publication types
    try:
        logger.info(f"Fetching publication types for {api_config['community_slug']}...")
        response = requests.get(f"{api_config['base_url']}/pub-types", headers=api_config["headers"])
        response.raise_for_status()
        config["pub_types"] = response.json()["pubTypes"]
        logger.info(f"Retrieved {len(config['pub_types'])} publication types")
    except Exception as e:
        logger.error(f"Error fetching publication types: {str(e)}")
    
    # Get stages
    try:
        logger.info(f"Fetching stages for {api_config['community_slug']}...")
        response = requests.get(f"{api_config['base_url']}/stages", headers=api_config["headers"])
        response.raise_for_status()
        config["stages"] = response.json()["stages"]
        logger.info(f"Retrieved {len(config['stages'])} stages")
    except Exception as e:
        logger.error(f"Error fetching stages: {str(e)}")
    
    # Get custom fields
    try:
        logger.info(f"Fetching custom fields for {api_config['community_slug']}...")
        response = requests.get(f"{api_config['base_url']}/customFields", headers=api_config["headers"])
        response.raise_for_status()
        config["fields"] = response.json()["customFields"]
        logger.info(f"Retrieved {len(config['fields'])} custom fields")
    except Exception as e:
        logger.error(f"Error fetching custom fields: {str(e)}")
    
    return config

# Map Airtable data to PubPub objects
def map_airtable_to_pubpub(airtable_data, pubpub_config, logger):
    """Map Airtable data to PubPub objects based on current configuration"""
    logger.info("Mapping Airtable data to PubPub objects...")
    
    # Initialize mappings
    mappings = {
        "publications": [],
        "authors": [],
        "reviews": [],
        "contributors": []
    }
    
    # Process preprints
    if "Preprint Info ONLY" in airtable_data:
        for record in airtable_data["Preprint Info ONLY"]:
            pub = {
                "airtable_id": record["id"],
                "title": record["fields"].get("Title", "Untitled Preprint"),
                "description": record["fields"].get("Abstract", ""),
                "doi": record["fields"].get("DOI", ""),
                "pub_type": None,
                "stage": None
            }
            
            # Try to match to a publication type
            if pubpub_config["pub_types"]:
                # Default to the first pub type
                pub["pub_type"] = pubpub_config["pub_types"][0]["id"]
            
            # Try to match to a stage
            if pubpub_config["stages"]:
                # Default to the first stage
                pub["stage"] = pubpub_config["stages"][0]["id"]
            
            mappings["publications"].append(pub)
    
    # Process persons
    if "Person" in airtable_data:
        for record in airtable_data["Person"]:
            author = {
                "airtable_id": record["id"],
                "name": record["fields"].get("Name", ""),
                "orcid": record["fields"].get("ORCID", ""),
                "email": record["fields"].get("Email", "")
            }
            mappings["authors"].append(author)
    
    # Process reviews
    if "Completed Review" in airtable_data:
        for record in airtable_data["Completed Review"]:
            review = {
                "airtable_id": record["id"],
                "title": record["fields"].get("Title", "Untitled Review"),
                "comments": record["fields"].get("Comments", ""),
                "rating": record["fields"].get("Rating", 0),
                "preprint_title": record["fields"].get("Preprint", [""])[0],
                "reviewer_name": record["fields"].get("Reviewer", [""])[0]
            }
            mappings["reviews"].append(review)
    
    # Process role assignments
    if "Role assignments" in airtable_data:
        for record in airtable_data["Role assignments"]:
            contributor = {
                "airtable_id": record["id"],
                "person_name": record["fields"].get("Person", [""])[0],
                "role": record["fields"].get("Role", [""])[0],
                "institution": record["fields"].get("Institution", [""])[0],
                "publication_title": record["fields"].get("Publication", [""])[0]
            }
            mappings["contributors"].append(contributor)
    
    logger.info(f"Mapped {len(mappings['publications'])} publications")
    logger.info(f"Mapped {len(mappings['authors'])} authors")
    logger.info(f"Mapped {len(mappings['reviews'])} reviews")
    logger.info(f"Mapped {len(mappings['contributors'])} contributors")
    
    return mappings

# Generate mock operations
def generate_mock_operations(mappings, api_config, logger):
    """Generate mock operations based on the mapped data"""
    operations = []
    
    # Generate publication operations
    for pub in mappings["publications"]:
        operation = {
            "type": "CREATE_PUBLICATION",
            "status": "MOCK",
            "url": f"{api_config['base_url']}/pubs",
            "method": "POST",
            "payload": {
                "title": pub["title"],
                "description": pub["description"],
                "pubMetadata": {
                    "doi": pub["doi"]
                },
                "pubTypeId": pub["pub_type"],
                "stageId": pub["stage"],
                "communityId": api_config["community_slug"]
            }
        }
        operations.append(operation)
    
    # Generate author operations
    for author in mappings["authors"]:
        operation = {
            "type": "CREATE_USER",
            "status": "MOCK",
            "url": f"{api_config['base_url']}/users",
            "method": "POST",
            "payload": {
                "name": author["name"],
                "orcid": author["orcid"],
                "email": author["email"]
            }
        }
        operations.append(operation)
    
    # Generate review operations
    for review in mappings["reviews"]:
        # Find the publication ID based on the title
        pub_id = "mock-pub-id"
        for pub in mappings["publications"]:
            if pub["title"] == review["preprint_title"]:
                pub_id = pub.get("pubpub_id", "mock-pub-id")
        
        operation = {
            "type": "CREATE_REVIEW",
            "status": "MOCK",
            "url": f"{api_config['base_url']}/pubs/{pub_id}/reviews",
            "method": "POST",
            "payload": {
                "title": review["title"],
                "comments": review["comments"],
                "rating": review["rating"]
            }
        }
        operations.append(operation)
    
    # Generate contributor operations
    for contributor in mappings["contributors"]:
        # Find the publication ID based on the title
        pub_id = "mock-pub-id"
        for pub in mappings["publications"]:
            if pub["title"] == contributor["publication_title"]:
                pub_id = pub.get("pubpub_id", "mock-pub-id")
        
        operation = {
            "type": "ADD_CONTRIBUTOR",
            "status": "MOCK",
            "url": f"{api_config['base_url']}/pubs/{pub_id}/contributors",
            "method": "POST",
            "payload": {
                "name": contributor["person_name"],
                "role": contributor["role"],
                "affiliation": contributor["institution"]
            }
        }
        operations.append(operation)
    
    logger.info(f"Generated {len(operations)} mock operations")
    return operations

# Perform dry run
def perform_dry_run(api_config, airtable_data_file, logger):
    """Perform a dry run against the PubPub API using the specified Airtable data"""
    logger.info(f"Starting dry run for {api_config['community_slug']}...")
    
    # Load Airtable data
    with open(airtable_data_file, 'r') as f:
        airtable_data = json.load(f)
    
    # Get current PubPub configuration
    pubpub_config = get_pubpub_config(api_config, logger)
    
    # Map Airtable data to PubPub objects
    mappings = map_airtable_to_pubpub(airtable_data, pubpub_config, logger)
    
    # Generate mock operations
    operations = generate_mock_operations(mappings, api_config, logger)
    
    # Save operations to file
    output_dir = "dryrun_results"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f"{output_dir}/dryrun_{api_config['community_slug']}_{TIMESTAMP}.json"
    with open(output_file, 'w') as f:
        json.dump(operations, f, indent=2)
    
    logger.info(f"Dry run complete. {len(operations)} operations generated.")
    logger.info(f"Results saved to: {output_file}")
    
    return operations

def ensure_output_dir(directory="dryrun_results"):
    """Create output directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_mock_data(file_path=None):
    """Load mock data from a JSON file."""
    logger = logging.getLogger('pubpub_dryrun')
    
    if not file_path:
        file_path = find_latest_mock_data()
    
    if not file_path or not os.path.exists(file_path):
        logger.error(f"Mock data file not found: {file_path}")
        raise FileNotFoundError(f"Mock data file not found: {file_path}")
    
    logger.info(f"Loading mock data from {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Mock data loaded successfully")
    return data

def find_latest_mock_data(directory="output"):
    """Find the latest mock data file in the output directory."""
    logger = logging.getLogger('pubpub_dryrun')
    
    # Find all airtable_data_*.json files
    pattern = os.path.join(directory, "airtable_data_*.json")
    files = glob.glob(pattern)
    
    if not files:
        logger.error(f"No mock data files found in {directory}")
        return None
    
    # Sort by modification time (newest first)
    latest_file = max(files, key=os.path.getmtime)
    logger.info(f"Found latest mock data file: {latest_file}")
    return latest_file

class PubPubDryRun:
    """Class to perform a dry run against the PubPub API."""
    
    def __init__(self, community_slug, mock_data, debug=False):
        """Initialize the PubPub dry run."""
        self.logger = logging.getLogger('pubpub_dryrun')
        self.community_slug = community_slug
        self.mock_data = mock_data
        self.debug = debug
        self.api_url = "https://api.pubpub.org/graphql"
        self.results = {
            "community": {},
            "collections": [],
            "publications": [],
            "attributions": [],
            "mock_calls": [],
            "errors": []
        }
        
        self.logger.info(f"PubPub dry run initialized for community: {community_slug}")
    
    def execute_query(self, query, variables=None):
        """Execute a GraphQL query against the PubPub API."""
        self.logger.debug(f"Executing GraphQL query: {query}")
        if variables:
            self.logger.debug(f"Query variables: {json.dumps(variables)}")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                for error in data["errors"]:
                    self.logger.error(f"GraphQL error: {error['message']}")
                self.results["errors"].append({
                    "type": "graphql",
                    "message": data["errors"][0]["message"],
                    "query": query,
                    "variables": variables
                })
            
            return data
        
        except Exception as e:
            self.logger.error(f"Error executing GraphQL query: {e}")
            self.results["errors"].append({
                "type": "request",
                "message": str(e),
                "query": query,
                "variables": variables
            })
            return None
    
    def get_community(self):
        """Get information about the community."""
        self.logger.info(f"Getting information for community: {self.community_slug}")
        
        query = """
        query GetCommunity($slug: String!) {
            community(slug: $slug) {
                id
                name
                slug
                description
                createDate
                updatedDate
            }
        }
        """
        
        variables = {
            "slug": self.community_slug
        }
        
        result = self.execute_query(query, variables)
        
        if result and "data" in result and "community" in result["data"]:
            community = result["data"]["community"]
            self.logger.info(f"Community found: {community['name']} ({community['id']})")
            self.results["community"] = community
            return community
        
        self.logger.error(f"Community not found: {self.community_slug}")
        return None
    
    def get_collections(self):
        """Get collections for the community."""
        if not self.results["community"] or "id" not in self.results["community"]:
            self.logger.error("Community not loaded, cannot get collections")
            return []
        
        community_id = self.results["community"]["id"]
        self.logger.info(f"Getting collections for community: {community_id}")
        
        query = """
        query GetCollections($communityId: String!) {
            collections(communityId: $communityId) {
                id
                title
                slug
                description
                isPublic
                createdAt
                updatedAt
            }
        }
        """
        
        variables = {
            "communityId": community_id
        }
        
        result = self.execute_query(query, variables)
        
        if result and "data" in result and "collections" in result["data"]:
            collections = result["data"]["collections"]
            self.logger.info(f"Found {len(collections)} collections")
            self.results["collections"] = collections
            return collections
        
        self.logger.error("Failed to retrieve collections")
        return []
    
    def mock_create_publication(self, title, description, collection_id=None):
        """Mock creating a publication."""
        self.logger.info(f"MOCK: Creating publication: {title}")
        
        # Generate a mock ID
        mock_id = f"mock-pub-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        mock_call = {
            "type": "create_publication",
            "title": title,
            "description": description,
            "collection_id": collection_id,
            "mock_id": mock_id,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.results["mock_calls"].append(mock_call)
        self.logger.debug(f"Mock publication created with ID: {mock_id}")
        
        # Create a mock publication result
        mock_publication = {
            "id": mock_id,
            "title": title,
            "description": description,
            "collection_id": collection_id,
            "is_mock": True,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        self.results["publications"].append(mock_publication)
        return mock_publication
    
    def mock_update_publication(self, pub_id, updates):
        """Mock updating a publication."""
        self.logger.info(f"MOCK: Updating publication: {pub_id}")
        
        # Find the publication in our results
        pub_index = None
        for i, pub in enumerate(self.results["publications"]):
            if pub["id"] == pub_id:
                pub_index = i
                break
        
        if pub_index is None:
            self.logger.error(f"Publication not found for update: {pub_id}")
            return None
        
        mock_call = {
            "type": "update_publication",
            "pub_id": pub_id,
            "updates": updates,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.results["mock_calls"].append(mock_call)
        
        # Update the mock publication
        for key, value in updates.items():
            self.results["publications"][pub_index][key] = value
        
        self.results["publications"][pub_index]["updated_at"] = datetime.datetime.now().isoformat()
        
        return self.results["publications"][pub_index]
    
    def mock_create_attribution(self, pub_id, attribution_data):
        """Mock creating an attribution for a publication."""
        self.logger.info(f"MOCK: Creating attribution for publication: {pub_id}")
        
        # Generate a mock ID
        mock_id = f"mock-attr-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        mock_call = {
            "type": "create_attribution",
            "pub_id": pub_id,
            "attribution_data": attribution_data,
            "mock_id": mock_id,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.results["mock_calls"].append(mock_call)
        
        # Create a mock attribution result
        mock_attribution = {
            "id": mock_id,
            "pub_id": pub_id,
            "name": attribution_data.get("name", ""),
            "roles": attribution_data.get("roles", []),
            "is_mock": True,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        self.results["attributions"].append(mock_attribution)
        return mock_attribution
    
    def process_mock_data(self):
        """Process the mock data to simulate API operations."""
        self.logger.info("Processing mock data to simulate API operations")
        
        # First, get real community and collections info
        community = self.get_community()
        if not community:
            self.logger.error("Cannot proceed without community information")
            return False
        
        collections = self.get_collections()
        collection_map = {}
        for collection in collections:
            collection_map[collection["title"]] = collection["id"]
        
        # Process preprints
        if "preprints" in self.mock_data:
            self.logger.info(f"Processing {len(self.mock_data['preprints'])} preprints")
            
            for preprint in self.mock_data["preprints"]:
                try:
                    title = preprint.get("Title", "Untitled Preprint")
                    description = preprint.get("Abstract", "")
                    
                    # Determine collection from preprint data
                    collection_name = preprint.get("Collection", "Default Collection")
                    collection_id = collection_map.get(collection_name)
                    
                    if not collection_id:
                        self.logger.warning(f"Collection not found: {collection_name}, using first available")
                        if collections:
                            collection_id = collections[0]["id"]
                    
                    # Create mock publication
                    pub = self.mock_create_publication(title, description, collection_id)
                    
                    # Add DOI if available
                    doi = preprint.get("DOI")
                    if doi:
                        self.mock_update_publication(pub["id"], {"doi": doi})
                    
                    # Process authors if available
                    authors = preprint.get("Authors", [])
                    if isinstance(authors, str):
                        # Handle case where authors are a comma-separated string
                        authors = [name.strip() for name in authors.split(",")]
                    
                    for author in authors:
                        if isinstance(author, str):
                            name = author
                            roles = ["Author"]
                        else:
                            # Handle case where author is a more complex object
                            name = author.get("Name", "Unknown Author")
                            roles = author.get("Roles", ["Author"])
                        
                        self.mock_create_attribution(pub["id"], {
                            "name": name,
                            "roles": roles
                        })
                
                except Exception as e:
                    self.logger.error(f"Error processing preprint: {e}")
                    self.results["errors"].append({
                        "type": "processing",
                        "message": str(e),
                        "preprint": preprint
                    })
        
        # Process reviews if available
        if "reviews" in self.mock_data:
            self.logger.info(f"Processing {len(self.mock_data['reviews'])} reviews")
            
            for review in self.mock_data["reviews"]:
                try:
                    # In a real implementation, we would link reviews to publications
                    # and create appropriate content
                    self.logger.debug(f"MOCK: Would process review: {review.get('id')}")
                except Exception as e:
                    self.logger.error(f"Error processing review: {e}")
        
        self.logger.info("Mock data processing complete")
        return True
    
    def save_results(self, directory="output"):
        """Save the results of the dry run to a JSON file."""
        ensure_output_dir(directory)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{directory}/pubpub_dryrun_{self.community_slug}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.logger.info(f"Dry run results saved to {filename}")
        return filename

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PubPub API Dry Run")
    parser.add_argument("--community", "-c", required=True, help="PubPub community slug to test against")
    parser.add_argument("--input", "-i", help="Path to mock data JSON file (defaults to latest)")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logging")
    parser.add_argument("--output", "-o", default="output", help="Output directory for saved results")
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(args.debug)
    
    try:
        # Load mock data
        logger.info("Loading mock data...")
        mock_data = load_mock_data(args.input)
        
        # Create and run the PubPub dry run
        logger.info(f"Starting PubPub dry run for community: {args.community}")
        dry_run = PubPubDryRun(args.community, mock_data, args.debug)
        
        # Process the mock data
        dry_run.process_mock_data()
        
        # Save the results
        output_file = dry_run.save_results(args.output)
        
        # Log summary
        logger.info(f"Dry run complete. Results saved to: {output_file}")
        logger.info(f"Summary:")
        logger.info(f"- Community: {dry_run.results['community'].get('name', 'Not found')}")
        logger.info(f"- Collections: {len(dry_run.results['collections'])}")
        logger.info(f"- Mock publications: {len(dry_run.results['publications'])}")
        logger.info(f"- Mock attributions: {len(dry_run.results['attributions'])}")
        logger.info(f"- Mock API calls: {len(dry_run.results['mock_calls'])}")
        logger.info(f"- Errors: {len(dry_run.results['errors'])}")
        
        if dry_run.results["errors"]:
            logger.warning("Errors occurred during dry run. Check the log file for details.")
            return 1
    
    except Exception as e:
        logger.error(f"Error in dry run process: {e}", exc_info=args.debug)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 