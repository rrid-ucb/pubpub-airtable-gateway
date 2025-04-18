# Type IDs Usage and Configuration in PubPub (2025-04-07 09:34:09)

_**User**_

look through the codebase and tell us two things: 1) how are type ids used? and is there any indication where in pubpub we can get the correct type ids we need to put in the .env file?

---

_**Assistant**_


---

Let me analyze how type IDs are used and where to find them:

1. How Type IDs are Used:
- Type IDs are used to identify different types of content in PubPub when creating or updating publications
- They are stored in environment variables and used in the `pubTypes` object in both `import.js` and `import_dev.js`
- The main types used are:
  - `NARRATIVE_TYPE_ID`: For project narratives
  - `TYPE_TYPE_ID`: For pub types
  - `PERSON_TYPE_ID`: For person records
  - `CONTRIBUTOR_TYPE_ID`: For contributor records
  - `PUB_TYPE_ID`: For main publications
  - `INSTITUTIONS_TYPE_ID`: For institutions
  - `ROLES_TYPE_ID`: For contributor roles
  - `PREPRINT_TYPE_ID`: For preprints (in newer versions)
  - `REVIEWER_TYPE_ID`: For reviewers (in newer versions)
- These IDs are used when:
  - Creating new publications via the PubPub API
  - Updating existing publications
  - Managing relationships between different types of content
  - Filtering and querying publications

2. Where to Get Type IDs:
Looking at the `requests_template` file, there's an API endpoint that can be used to get the type IDs:

```
GET https://app.pubpub.org/api/v0/c/<slug>/site/pub-types
```

To get the correct type IDs:
1. You need to be logged into PubPub with appropriate permissions
2. Replace `<slug>` with your community slug (which is set in the .env file as `COMMUNITY_SLUG`)
3. Make sure to include your PubPub API key in the Authorization header
4. This endpoint will return all available pub types for your community, including their IDs

The process would be:
1. Make an authenticated request to this endpoint
2. The response will contain all pub types with their IDs
3. Match the type names with what you need (narrative, person, etc.)
4. Use those IDs in your .env file

I notice in your attached files that you have a template .env file and an actual .env file with real values. The template shows the structure needed, while the actual .env file shows example values like `type_narrative_001`, `type_pubtype_001`, etc. These appear to follow a pattern of `type_[typename]_[number]`, which suggests they are generated by PubPub when pub types are created in your community.

Would you like me to help you make the API request to get the current type IDs for your community?

---

_**User**_

can we try using the .env file which has our API secrets to write a quick test curl or python script to test the PUBPUB api key to try to query the API endpoint to get the type ids for our community_slug?

---

_**Assistant**_

I'll help you create a simple Python script to test the API and get the type IDs. First, let me check the .env file to get the necessary credentials.

From the attached .env file, I can see:
- PUBPUB_API_KEY: REDACTED
- COMMUNITY_SLUG: rrid

---

Great! The API call was successful and we got the pub types for your community. Let me break down what we found:

1. There are three pub types currently defined in your community:

- **Reviewer** (ID: `a259328d-5748-412f-a7c4-98d4dfef01f9`)
  - Description: "Reviewer information"
  - Has fields for reviewer name, email, justification, affiliation, title, degree, etc.

- **Review** (ID: `5b011313-59bc-44a1-a87a-d68660449b8e`)
  - Description: "The rapid reviews of the preprint"
  - Currently only has a title field

- **Preprint** (ID: `88a68e83-a516-4400-9991-57038fd1e1bd`)
  - Description: "The preprint being reviewed"
  - Has fields for title, abstract, domain, team, and DOI

These IDs match what we see in your .env file where you have:
```
PREPRINT_TYPE_ID=<your-pubpub-type-id>
REVIEWER_TYPE_ID=<your-pubpub-type-id>
REVIEW_TYPE_ID=<your-pubpub-type-id>
```

You can now update your .env file with these actual IDs:
- `PREPRINT_TYPE_ID=88a68e83-a516-4400-9991-57038fd1e1bd`
- `REVIEWER_TYPE_ID=a259328d-5748-412f-a7c4-98d4dfef01f9`
- `REVIEW_TYPE_ID=5b011313-59bc-44a1-a87a-d68660449b8e`

Would you like me to help you update the .env file with these values? Also, I notice that some of the other type IDs mentioned in your .env file (like NARRATIVE_TYPE_ID, TYPE_TYPE_ID, etc.) don't appear in the API response. This might mean they need to be created in PubPub first, or they might be in a different community. Would you like me to help investigate those as well?

---

_**User**_

explain chmod and runnig scripts, also the shebang that i added

---

_**Assistant**_

I'll explain the shebang line you added and how it relates to making scripts executable:

1. **The Shebang Line (`#!/usr/bin/env python`)**
- This is called a "shebang" or "hashbang" line
- It tells the operating system which interpreter to use to run the script
- `#!/usr/bin/env python` is preferred over `#!/usr/bin/python` because:
  - It uses the `env` command to locate the Python interpreter in the user's PATH
  - This makes the script more portable across different systems where Python might be installed in different locations
  - It will use whatever Python version is first in your PATH

2. **Making Scripts Executable (chmod)**
To make a script executable, you need to use the `chmod` command. Here are the common ways:

```bash
# Make the script executable for the owner only
chmod u+x test_pubpub_api.py

# Make the script executable for everyone
chmod +x test_pubpub_api.py

# Make the script executable with specific permissions (read, write, execute)
chmod 755 test_pubpub_api.py  # Owner can read/write/execute, others can read/execute
```

Let's make your script executable:

```bash
chmod +x test_pubpub_api.py
```
---

Now you can run the script in two ways:

1. Using Python explicitly:
```bash
python3 test_pubpub_api.py
```

2. Directly as an executable (because of the shebang):
```bash
./test_pubpub_api.py
```


---

The script ran successfully! This demonstrates that:
1. The shebang line is working correctly
2. The file permissions are set properly
3. The script can be executed directly

A few additional tips about script execution:
1. If you get a "Permission denied" error, you need to run `chmod +x` first
2. If you get a "command not found" error, make sure you're in the correct directory or use the full path
3. The `./` prefix is needed when running scripts from the current directory to distinguish them from system commands
4. You can check a file's permissions using `ls -l test_pubpub_api.py`

Would you like me to show you how to check the current permissions of your script or explain any other aspects of script execution?

---

_**User**_

i fixed the .env so can you now please re run the @test_pubpub_api.py to get the correct type ids and fill those into the @.env 

---

_**Assistant**_

I'll help you update the .env file with the correct type IDs from the API response. First, let's run the script again to get the latest data:

---

Now I'll update the .env file with the correct type IDs from the API response:



---

```diff
  NONPUBS_STAGE_ID=stage_nonpubs_001
  
- PREPRINT_TYPE_ID=<your-pubpub-type-id> #added for preprint
- REVIEWER_TYPE_ID=<your-pubpub-type-id> #added for reviewers
- REVIEW_TYPE_ID=<your-pubpub-type-id>
+ PREPRINT_TYPE_ID=88a68e83-a516-4400-9991-57038fd1e1bd
+ REVIEWER_TYPE_ID=a259328d-5748-412f-a7c4-98d4dfef01f9
+ REVIEW_TYPE_ID=5b011313-59bc-44a1-a87a-d68660449b8e
  
  # STAGES
```

---

I've updated the .env file with the correct type IDs from the API response:

1. `PREPRINT_TYPE_ID=88a68e83-a516-4400-9991-57038fd1e1bd`
2. `REVIEWER_TYPE_ID=a259328d-5748-412f-a7c4-98d4dfef01f9`
3. `REVIEW_TYPE_ID=5b011313-59bc-44a1-a87a-d68660449b8e`

I notice that the other type IDs (NARRATIVE_TYPE_ID, TYPE_TYPE_ID, etc.) are still using placeholder values like `type_narrative_001`. These don't appear in the API response, which suggests they might need to be created in PubPub first. Would you like me to help you:

1. Verify if these other types exist in PubPub?
2. Create these types if they don't exist?
3. Or keep the current placeholder values for now?

Please let me know how you'd like to proceed with the other type IDs.

---

_**User**_

@import_dev.js explain this code in import_dev

---

_**Assistant**_

I'll explain the `import_dev.js` code, which appears to be a development version of an import script that syncs data between Airtable and PubPub. Let me break it down:

## Overview of `import_dev.js`

This script is designed to import data from Airtable into PubPub, mapping Airtable records to PubPub publications. It's essentially a data synchronization tool that:

1. Connects to both Airtable and PubPub APIs
2. Maps Airtable records to PubPub publication types
3. Creates or updates publications in PubPub based on Airtable data
4. Handles relationships between different types of publications

## Key Components

### 1. Configuration and Setup

```javascript
const pubTypes = {
  narrative: process.env.NARRATIVE_TYPE_ID,
  type: process.env.TYPE_TYPE_ID,
  person: process.env.PERSON_TYPE_ID,
  contributor: process.env.CONTRIBUTOR_TYPE_ID,
  pub: process.env.PUB_TYPE_ID,
  institutions: process.env.INSTITUTIONS_TYPE_ID,
  roles: process.env.ROLES_TYPE_ID,
  
  //added for preprint and reviewer
  preprint: process.env.PREPRINT_TYPE_ID,
  reviewer: process.env.REVIEWER_TYPE_ID,
};

const stages = {
  airtable: process.env.AIRTABLE_STAGE_ID,
  nonPubs: process.env.NONPUBS_STAGE_ID,
};
```

This section defines the mapping between PubPub publication types and their IDs from the environment variables. It also defines stages (like "airtable" and "nonPubs") which are used to categorize publications in PubPub.

### 2. Airtable Connection

```javascript
Airtable.configure({
  apiKey: process.env.AIRTABLE_API_KEY,
});

const airtable = Airtable.base(process.env.AIRTABLE_BASE_ID);
```

This establishes a connection to the Airtable API using the API key and base ID from environment variables.

### 3. Data Import Functions

The script then defines several import functions, each targeting a specific Airtable table and mapping it to a corresponding PubPub publication type:

#### TYPE_PUBS
```javascript
const TYPE_PUBS = await airtableToPubPub(
  airtable,
  "Pub type",
  pubTypes.type,
  stages.nonPubs,
  {
    title: (record) => record.get("Name"),
    slug: (record) =>
      record.get("Slug") ?? slugify(record.get("Name"), { lower: true }),
    "preview-image": (record) => record.get("Preview Image"),
  },
  "airtable-id"
);
```

This imports "Pub type" records from Airtable into PubPub, mapping:
- Airtable "Name" field to PubPub "title"
- Airtable "Slug" field to PubPub "slug" (or generates a slug from the name)
- Airtable "Preview Image" field to PubPub "preview-image"

#### NARRATIVE_PUBS
```javascript
const NARRATIVE_PUBS = await airtableToPubPub(
  airtable,
  "Project narratives",
  pubTypes.narrative,
  stages.nonPubs,
  {
    title: (record) => record.get("Name"),
    slug: (record) =>
      record.get("Slug") ??
      (record.get("Link to PubPub") &&
        record.get("Link to PubPub").split("/")[3]),
    "google-drive-folder-url": (record) => record.get("Link to narrative"),
    "icing-hashtags": (record) =>
      record.get("Icing hashtag (from Icing status)"),
  },
  "airtable-id"
);
```

This imports "Project narratives" from Airtable, with similar field mappings.

#### PEOPLE_PUBS
```javascript
const PEOPLE_PUBS = await airtableToPubPub(
  airtable,
  "Person",
  pubTypes.person,
  stages.nonPubs,
  {
    "full-name": (record) => record.get("Name"),
    slug: (record) =>
      record.get("Slug") ?? slugify(record.get("Name"), { lower: true }),
    orcid: (record) =>
      /^(\d{4}-){3}\d{3}(\d|X)$/.test(record.get("ORCID"))
        ? `https://orcid.org/${record.get("ORCID")}`
        : undefined,
    // avatar: (record) => record.get("Headshot"),
  },
  "airtable-id"
);
```

This imports "Person" records, with special handling for ORCID IDs to ensure they're properly formatted.

#### ROLE_PUBS, INSTITUTION_PUBS, CONTRIBUTOR_PUBS

These sections import various types of records related to roles, institutions, and contributors, with appropriate field mappings.

#### PUB_PUBS
```javascript
const PUB_PUBS = await airtableToPubPub(
    airtable,
    "Pub",
    pubTypes.pub,
    stages.airtable,
    {
      title: (record) => record.get("Title"),
      "pub-contributors": (record) =>
        getRelatedPubsArray(
          record.get("Active pub contributors"),
          CONTRIBUTOR_PUBS,
          "airtable-id"
        ),
      // ... more field mappings
    },
    "airtable-id",
    ["Internal pub for now", "New versions"]
  );
```

This imports the main "Pub" records, which is more complex because it includes relationships to other publication types (like contributors, narratives, etc.).

#### PREPRINT_PUBS and REVIEWER_PUBS

These are newer additions to the script, handling preprints and reviewers:

```javascript
const PREPRINT_PUBS = await airtableToPubPub(
    airtable,
    "Preprint Info ONLY",
    pubTypes.preprint,
    stages.airtable,
    {
      "title": (record) => record.get("Title (from Selected)"),
      "abstract": (record) => record.get("Abstract"),
      // ... more field mappings
    },
    "airtable-id"
);

const REVIEWER_PUBS = await airtableToPubPub(
    airtable,
    "Student Reviewer Inputs",
    pubTypes.reviewer,
    stages.airtable,
    {
      "reviewer-name": (record) => record.get("First + Last Name"),
      // ... more field mappings
    },
    "airtable-id"
);
```

## The `airtableToPubPub` Function

The core of this script is the `airtableToPubPub` function (imported from `./lib/airtableToPubPub.js`), which:

1. Fetches existing publications from PubPub
2. Iterates through Airtable records
3. Maps Airtable fields to PubPub fields
4. Creates or updates publications in PubPub
5. Handles relationships between publications

## Key Features

1. **Field Mapping**: Each import function defines how Airtable fields map to PubPub fields
2. **Relationship Handling**: Uses `getRelatedPubsArray` to establish relationships between publications
3. **Data Transformation**: Includes logic to transform data (e.g., formatting ORCID IDs, generating slugs)
4. **Error Handling**: Includes comments about potential issues (e.g., "Sometimes the link is not a doi")
5. **Exclusion Logic**: Some imports exclude records based on specific fields (e.g., "Internal pub for now", "New versions")

## Development vs. Production

This is a development version (`import_dev.js`), which likely means:
1. It might include additional logging or debugging
2. It might have experimental features not yet in production
3. It might be used for testing before deploying to production

The script is designed to be run as a Node.js application, using environment variables for configuration.

Would you like me to explain any specific part of this code in more detail?

---

_**User**_

take a look at the two repositories in the upstream subdirectory and tell us how those two things fit together in the with this main repo that we're working with which is the airtable gateway repo and specifically we want to know what these contributor and narrative pubs are and how it fits into the overall system 

---

_**Assistant**_

I'll examine the repositories in the upstream subdirectory to understand how they fit together with the main airtable gateway repo. Let me first check what's in the upstream directory.

---

Based on my analysis of the codebase, I can now explain how the three repositories fit together and how the contributor and narrative pubs function in the overall system:

## How the Repositories Fit Together

1. **Main Repository (pubpub-airtable-gateway)**
   - This is the main repository we're working with
   - It contains scripts to sync data between Airtable and PubPub
   - The core functionality is in the `lib` directory, with the main import scripts in the root

2. **Upstream/platform Repository**
   - This appears to be the PubPub platform codebase
   - It's a monorepo structure with multiple packages
   - Contains the core PubPub platform functionality that the gateway interacts with
   - Provides the API endpoints that the gateway uses to create/update publications

3. **Upstream/pubpub Repository**
   - This appears to be the PubPub client application
   - Contains the frontend code for the PubPub platform
   - Provides the user interface for interacting with publications

## How the System Works

The airtable-gateway acts as a bridge between Airtable and PubPub:

1. **Data Flow**:
   - Airtable → airtable-gateway → PubPub Platform API → PubPub Database
   - The gateway reads data from Airtable tables
   - Maps Airtable fields to PubPub publication fields
   - Creates or updates publications in PubPub via the API

2. **Publication Types**:
   - The system uses different publication types to represent different kinds of content
   - Each type has its own set of fields and relationships
   - Type IDs 

---
