#!/usr/bin/env python3

import os
import json
import random
import datetime
import string
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    if not os.path.exists('output'):
        os.makedirs('output')

def generate_uuid():
    """Generate a random UUID."""
    return str(uuid.uuid4())

def generate_random_string(length=10):
    """Generate a random string of specified length."""
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

def generate_random_date(start_date="2022-01-01", end_date=None):
    """Generate a random date between start_date and end_date."""
    if end_date is None:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + datetime.timedelta(days=random_days)).strftime("%Y-%m-%d")

def generate_mock_preprints(count=10):
    """Generate mock preprints data."""
    preprints = []
    for i in range(count):
        preprint = {
            "id": generate_uuid(),
            "Title": f"Preprint {i+1}: {generate_random_string(20)}",
            "Abstract": f"This is an abstract for preprint {i+1}. {generate_random_string(100)}",
            "DOI": f"10.1234/preprint-{i+1}",
            "URL": f"https://example.com/preprints/{i+1}",
            "SubmissionDate": generate_random_date(),
            "Status": random.choice(["submitted", "in_review", "accepted", "published"]),
            "Keywords": [generate_random_string(8) for _ in range(random.randint(3, 6))]
        }
        preprints.append(preprint)
    return preprints

def generate_mock_reviewers(count=20):
    """Generate mock reviewers data."""
    reviewers = []
    for i in range(count):
        reviewer = {
            "id": generate_uuid(),
            "Name": f"{generate_random_string(8)} {generate_random_string(10)}",
            "Email": f"{generate_random_string(8)}@example.com",
            "Institution": f"{generate_random_string(12)} University",
            "Expertise": [generate_random_string(8) for _ in range(random.randint(2, 5))],
            "ORCID": f"0000-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        }
        reviewers.append(reviewer)
    return reviewers

def generate_mock_reviews(preprints, reviewers, count=15):
    """Generate mock reviews data."""
    reviews = []
    for i in range(count):
        preprint = random.choice(preprints)
        reviewer = random.choice(reviewers)
        review = {
            "id": generate_uuid(),
            "PreprintID": preprint["id"],
            "ReviewerID": reviewer["id"],
            "SubmissionDate": generate_random_date(preprint["SubmissionDate"]),
            "Content": f"This is a review for {preprint['Title']}. {generate_random_string(200)}",
            "Rating": random.randint(1, 5),
            "Status": random.choice(["submitted", "accepted", "published"])
        }
        reviews.append(review)
    return reviews

def generate_mock_persons(count=30):
    """Generate mock persons data."""
    persons = []
    for i in range(count):
        person = {
            "id": generate_uuid(),
            "Name": f"{generate_random_string(8)} {generate_random_string(10)}",
            "Email": f"{generate_random_string(8)}@example.com",
            "Affiliation": f"{generate_random_string(12)} {random.choice(['University', 'Institute', 'Lab', 'Center'])}",
            "ORCID": f"0000-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        }
        persons.append(person)
    return persons

def generate_mock_institutions(count=15):
    """Generate mock institutions data."""
    institutions = []
    for i in range(count):
        institution = {
            "id": generate_uuid(),
            "Name": f"{generate_random_string(12)} {random.choice(['University', 'Institute', 'Lab', 'Center'])}",
            "Location": f"{generate_random_string(10)}, {generate_random_string(8)}",
            "Type": random.choice(["Academic", "Research", "Industry", "Government"]),
            "URL": f"https://{generate_random_string(8)}.edu"
        }
        institutions.append(institution)
    return institutions

def generate_mock_contributor_roles(count=5):
    """Generate mock contributor roles data."""
    roles = [
        {"id": generate_uuid(), "Name": "Author", "Description": "Primary author of the work"},
        {"id": generate_uuid(), "Name": "Reviewer", "Description": "Reviewer of the work"},
        {"id": generate_uuid(), "Name": "Editor", "Description": "Editor of the work"},
        {"id": generate_uuid(), "Name": "Data Curator", "Description": "Responsible for data curation"},
        {"id": generate_uuid(), "Name": "Methodology", "Description": "Responsible for methodology development"}
    ]
    return roles[:count]

def generate_mock_role_assignments(preprints, persons, roles, count=40):
    """Generate mock role assignments."""
    assignments = []
    for i in range(count):
        preprint = random.choice(preprints)
        person = random.choice(persons)
        role = random.choice(roles)
        assignment = {
            "id": generate_uuid(),
            "PreprintID": preprint["id"],
            "PersonID": person["id"],
            "RoleID": role["id"],
            "Order": random.randint(1, 5),
            "CreatedAt": generate_random_date(preprint["SubmissionDate"])
        }
        assignments.append(assignment)
    return assignments

def generate_mock_airtable_data():
    """Generate complete mock Airtable data."""
    preprints = generate_mock_preprints()
    reviewers = generate_mock_reviewers()
    reviews = generate_mock_reviews(preprints, reviewers)
    persons = generate_mock_persons()
    institutions = generate_mock_institutions()
    roles = generate_mock_contributor_roles()
    role_assignments = generate_mock_role_assignments(preprints, persons, roles)
    
    mock_data = {
        "preprints": preprints,
        "reviewers": reviewers,
        "reviews": reviews,
        "persons": persons,
        "institutions": institutions,
        "roles": roles,
        "role_assignments": role_assignments
    }
    
    return mock_data

def save_mock_data(data):
    """Save mock data to file with timestamp."""
    ensure_output_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/mock_airtable_data_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filename

def main():
    print("Generating mock Airtable data...")
    mock_data = generate_mock_airtable_data()
    filename = save_mock_data(mock_data)
    print(f"Mock data saved to {filename}")
    return filename

if __name__ == "__main__":
    main() 