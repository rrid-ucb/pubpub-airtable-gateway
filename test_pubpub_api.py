#!/usr/bin/env python

import requests
import json

# API credentials
API_KEY = "42d5f584-c510-433c-b403-337ebea8dc92.2bAqgpy1wiU1a_aHn4L-KA"
COMMUNITY_SLUG = "rrid"

# API endpoint
url = f"https://app.pubpub.org/api/v0/c/{COMMUNITY_SLUG}/site/pub-types"

# Headers
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "*/*",
    "Prefer": "return=representation"
}

try:
    # Make the request
    response = requests.get(url, headers=headers)
    
    # Check if request was successful
    if response.status_code == 200:
        # Parse and pretty print the response
        data = response.json()
        print("\nPub Types found:")
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: Status code {response.status_code}")
        print("Response:", response.text)

except Exception as e:
    print(f"An error occurred: {str(e)}") 