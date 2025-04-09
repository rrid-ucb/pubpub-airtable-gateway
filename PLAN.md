# PubPub API Testing Plan

## Overview

This document outlines a plan to test the PubPub API by creating a representative sample of content from Airtable data. The test will be read-only from Airtable and will create test content in PubPub following the established workflow.

## Current Site Configuration

Based on the latest site dump, we have:

### Publication Types
1. **Preprint** (`88a68e83-a516-4400-9991-57038fd1e1bd`)
   - Fields: Title, Abstract, Domain, Team, DOI
   - Primary content type for the review process

2. **Review** (`5b011313-59bc-44a1-a87a-d68660449b8e`)
   - Fields: Title
   - Represents the reviews of preprints

3. **Reviewer** (`a259328d-5748-412f-a7c4-98d4dfef01f9`)
   - Fields: Name, Email, Justification, Affiliation, Title, Degree, Subdiscipline, Profile Link
   - Contains reviewer information

### Workflow Stages
1. Content Creation:
   - Build Content/Preprint Initiation → Preprint Unassigned

2. Review Process:
   - Preprint Assigned → Preprint Under Review → Preprint Ready for Publication
   - Review Invitations Sent → (Review Accepted | Review Declined | Review No Response)
   - Review Accepted → Review Completed → Review Under Edit → Review QA Complete

3. Publication:
   - Preprint Ready for Publication → Preprint + Reviews Published

## Test Data Sample

We will create a test dataset that includes:

1. **Preprints** (2-3 samples)
   - One complete preprint with reviews
   - One preprint in progress
   - One preprint with declined reviews

2. **Reviewers** (4-5 samples)
   - Mix of accepted, declined, and no-response reviewers
   - Various affiliations and expertise

3. **Reviews** (2-3 samples)
   - Completed reviews
   - Reviews in different stages (draft, under edit, QA)

## Test Scenarios

### 1. Preprint Workflow
a. Create preprint in "Build Content" stage
b. Move through stages:
   - Unassigned → Assigned → Under Review
   - Test stage constraints and transitions

### 2. Review Process
a. Create reviewer profiles
b. Send review invitations
c. Test different reviewer responses:
   - Acceptance path
   - Decline path
   - No response path

### 3. Publication Process
a. Complete review cycle
b. Move preprint to publication
c. Verify relationships between preprint and reviews

## Expected Results in PubPub

After running the test script, we should see:

1. **In Build Content Stage**:
   - 1 preprint being prepared
   - No reviews or reviewers attached

2. **In Review Process**:
   - 1 preprint under active review
   - 2-3 reviewers with accepted invitations
   - 1 reviewer who declined
   - 1 reviewer who hasn't responded
   - 1-2 completed reviews
   - 1 review under edit

3. **In Published State**:
   - 1 preprint with completed reviews
   - All relationships properly established
   - Full workflow history preserved

## Test Script Structure

1. **Setup Phase**
   ```python
   # Configuration and environment
   # Airtable read-only client setup
   # PubPub API client setup
   ```

2. **Data Sampling**
   ```python
   # Read sample preprints from Airtable
   # Read sample reviewer information
   # Create test dataset in memory
   ```

3. **Test Execution**
   ```python
   # Create publications in correct order
   # Establish relationships
   # Move through workflow stages
   ```

4. **Verification**
   ```python
   # Verify all objects created
   # Verify relationships
   # Verify workflow stages
   # Generate test report
   ```

## Dry Run Mode

The script will include a `--dry-run` flag that will:
1. Read data from Airtable
2. Show exactly what would be created in PubPub
3. Display the sequence of API calls that would be made
4. Generate a preview report of expected results

## Safety Measures

1. **Airtable Protection**:
   - Read-only access
   - No modifications to source data
   - Rate limiting on API calls

2. **PubPub Protection**:
   - Option to delete test data after completion
   - Clear labeling of test content
   - No modification of existing content

## Next Steps

1. Review this plan and confirm the scope
2. Run the script in dry-run mode to verify the planned changes
3. Decide whether to proceed with actual content creation
4. Consider adding more test scenarios if needed

## Questions for Consideration

1. Should we add more publication types beyond the current three?
2. Do we need to test edge cases in the workflow?
3. Should we test error conditions (e.g., invalid data)?
4. How should we handle cleanup of test data? 