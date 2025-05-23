#!/usr/bin/env python3

import os
import json
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests
from dotenv import load_dotenv
from airtable import Airtable
from slugify import slugify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
PUBPUB_API_KEY = os.getenv('PUBPUB_API_KEY')
COMMUNITY_SLUG = os.getenv('COMMUNITY_SLUG', 'rrid')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

PUBPUB_BASE_URL = f'https://api.pubpub.org/communities/{COMMUNITY_SLUG}'
PUBPUB_HEADERS = {
    'Authorization': f'Bearer {PUBPUB_API_KEY}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Publication Type IDs from site dump
PREPRINT_TYPE_ID = '88a68e83-a516-4400-9991-57038fd1e1bd'
REVIEW_TYPE_ID = '5b011313-59bc-44a1-a87a-d68660449b8e'
REVIEWER_TYPE_ID = 'a259328d-5748-412f-a7c4-98d4dfef01f9'

@dataclass
class TestResult:
    """Represents a test result with timing and status information."""
    operation: str
    success: bool
    duration: float
    details: str
    api_calls: List[Dict]

class TestReport:
    """Manages test results and generates reports."""
    def __init__(self, dry_run: bool = False):
        self.results: List[TestResult] = []
        self.dry_run = dry_run
        self.start_time = datetime.now()
        
    def add_result(self, result: TestResult):
        self.results.append(result)
        
    def generate_report(self) -> str:
        """Generate a markdown report of test results."""
        duration = datetime.now() - self.start_time
        
        report = [
            f"# PubPub API Test Report",
            f"\nGenerated: {datetime.now().isoformat()}",
            f"\nMode: {'DRY RUN' if self.dry_run else 'LIVE RUN'}",
            f"\nTotal Duration: {duration.total_seconds():.2f}s",
            "\n## Test Results\n"
        ]
        
        for result in self.results:
            status = "✅" if result.success else "❌"
            report.extend([
                f"### {status} {result.operation}",
                f"- Duration: {result.duration:.2f}s",
                f"- Details: {result.details}",
                "\nAPI Calls:"
            ])
            for call in result.api_calls:
                report.append(f"- {call['method']} {call['url']}")
            report.append("")
            
        return "\n".join(report)

class PubPubAPI:
    """Handles interactions with the PubPub API."""
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.api_calls = []
        
    def _record_api_call(self, method: str, url: str, data: Optional[Dict] = None):
        self.api_calls.append({
            'method': method,
            'url': url,
            'data': data
        })
        if self.dry_run:
            logger.info(f"DRY RUN: Would make {method} request to {url}")
            if data:
                logger.info(f"With data: {json.dumps(data, indent=2)}")
            return {'id': 'dry-run-id'}
            
    def create_publication(self, pub_type_id: str, data: Dict) -> Dict:
        """Create a new publication."""
        url = f"{PUBPUB_BASE_URL}/pubs"
        payload = {
            'publicationTypeId': pub_type_id,
            'title': data.get('title', 'Untitled'),
            'attributions': [],
            'customFields': data
        }
        
        self._record_api_call('POST', url, payload)
        if not self.dry_run:
            response = requests.post(url, headers=PUBPUB_HEADERS, json=payload)
            response.raise_for_status()
            return response.json()
        return {'id': 'dry-run-id'}
        
    def update_publication_stage(self, pub_id: str, stage_id: str) -> Dict:
        """Move a publication to a new stage."""
        url = f"{PUBPUB_BASE_URL}/pubs/{pub_id}/stage"
        payload = {'stageId': stage_id}
        
        self._record_api_call('PUT', url, payload)
        if not self.dry_run:
            response = requests.put(url, headers=PUBPUB_HEADERS, json=payload)
            response.raise_for_status()
            return response.json()
        return {'id': 'dry-run-id'}
        
    def update_publication_relations(self, pub_id: str, relations: List[Dict]) -> Dict:
        """Update publication relationships."""
        url = f"{PUBPUB_BASE_URL}/pubs/{pub_id}/relations"
        payload = {'relations': relations}
        
        self._record_api_call('PUT', url, payload)
        if not self.dry_run:
            response = requests.put(url, headers=PUBPUB_HEADERS, json=payload)
            response.raise_for_status()
            return response.json()
        return {'id': 'dry-run-id'}

class AirtableReader:
    """Handles reading data from Airtable."""
    def __init__(self, base_id: str, api_key: str):
        self.base_id = base_id
        self.api_key = api_key
        
    def get_sample_preprints(self, limit: int = 3) -> List[Dict]:
        """Get sample preprints from Airtable."""
        table = Airtable(self.base_id, 'Preprints', api_key=self.api_key)
        records = table.get_all(maxRecords=limit)
        return [record['fields'] for record in records]
        
    def get_sample_reviewers(self, limit: int = 5) -> List[Dict]:
        """Get sample reviewers from Airtable."""
        table = Airtable(self.base_id, 'Reviewers', api_key=self.api_key)
        records = table.get_all(maxRecords=limit)
        return [record['fields'] for record in records]

class TestRunner:
    """Orchestrates the test execution."""
    def __init__(self, dry_run: bool = False):
        self.pubpub = PubPubAPI(dry_run)
        self.airtable = AirtableReader(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)
        self.report = TestReport(dry_run)
        self.dry_run = dry_run
        
    def test_preprint_creation(self) -> TestResult:
        """Test creating a preprint."""
        start_time = time.time()
        api_calls = []
        
        try:
            preprints = self.airtable.get_sample_preprints(1)
            if not preprints:
                raise ValueError("No preprints found in Airtable")
                
            preprint = preprints[0]
            result = self.pubpub.create_publication(PREPRINT_TYPE_ID, preprint)
            api_calls.extend(self.pubpub.api_calls)
            
            return TestResult(
                operation="Create Preprint",
                success=True,
                duration=time.time() - start_time,
                details=f"Created preprint with ID: {result['id']}",
                api_calls=api_calls
            )
        except Exception as e:
            return TestResult(
                operation="Create Preprint",
                success=False,
                duration=time.time() - start_time,
                details=f"Error: {str(e)}",
                api_calls=api_calls
            )
            
    def test_reviewer_creation(self) -> TestResult:
        """Test creating reviewer profiles."""
        start_time = time.time()
        api_calls = []
        
        try:
            reviewers = self.airtable.get_sample_reviewers(2)
            if not reviewers:
                raise ValueError("No reviewers found in Airtable")
                
            created_reviewers = []
            for reviewer in reviewers:
                result = self.pubpub.create_publication(REVIEWER_TYPE_ID, reviewer)
                created_reviewers.append(result['id'])
            api_calls.extend(self.pubpub.api_calls)
            
            return TestResult(
                operation="Create Reviewers",
                success=True,
                duration=time.time() - start_time,
                details=f"Created {len(created_reviewers)} reviewers",
                api_calls=api_calls
            )
        except Exception as e:
            return TestResult(
                operation="Create Reviewers",
                success=False,
                duration=time.time() - start_time,
                details=f"Error: {str(e)}",
                api_calls=api_calls
            )
            
    def run_all_tests(self):
        """Run all test scenarios."""
        logger.info(f"Starting tests in {'DRY RUN' if self.dry_run else 'LIVE'} mode")
        
        # Run tests
        self.report.add_result(self.test_preprint_creation())
        self.report.add_result(self.test_reviewer_creation())
        
        # Generate report
        report_content = self.report.generate_report()
        report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_filename, 'w') as f:
            f.write(report_content)
            
        logger.info(f"Test report generated: {report_filename}")
        return report_filename

def main():
    parser = argparse.ArgumentParser(description='Test PubPub API with Airtable data')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    args = parser.parse_args()
    
    try:
        runner = TestRunner(dry_run=args.dry_run)
        report_file = runner.run_all_tests()
        logger.info("Tests completed successfully")
        logger.info(f"See {report_file} for detailed results")
    except Exception as e:
        logger.error(f"Test run failed: {str(e)}")
        raise

if __name__ == '__main__':
    main() 