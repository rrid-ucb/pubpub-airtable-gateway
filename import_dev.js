import Airtable from "airtable";
import airtableToPubPub from "./lib/airtableToPubPub.js";
import slugify from "slugify";
import getPubs from "./lib/getPubs.js";

import { getRelatedPubsArray, baseHeaders } from "./lib/utils.js";

// Debug information
console.log("Starting import process...");
console.log(`Community slug: ${process.env.COMMUNITY_SLUG}`);
console.log(`Airtable Base ID: ${process.env.AIRTABLE_BASE_ID}`);
console.log(`PubPub API Key (masked): ${process.env.PUBPUB_API_KEY.slice(0, 5)}...`);

const pubTypes = {
  preprint: process.env.PREPRINT_TYPE_ID,
  reviewer: process.env.REVIEWER_TYPE_ID,
  review: process.env.REVIEW_TYPE_ID
};

const stages = {
  airtable: process.env.AIRTABLE_STAGE_ID,  // Preprint Unassigned 
  nonPubs: process.env.NONPUBS_STAGE_ID     // Build Content stage
};

console.log("Pub Types:", pubTypes);
console.log("Stages:", stages);

// Quick test of the API access
console.log("Testing PubPub API connection...");
const testUrl = `https://app.pubpub.org/api/v0/c/${process.env.COMMUNITY_SLUG}/site/pub-types`;
fetch(testUrl, { headers: baseHeaders })
  .then(response => {
    if (!response.ok) {
      console.error(`API Test failed: ${response.status} ${response.statusText}`);
      console.error("Please check your API key and community slug.");
      process.exit(1);
    }
    console.log("API connection successful! Continuing with import...");
  })
  .catch(error => {
    console.error("API Test failed:", error);
    process.exit(1);
  });

Airtable.configure({
  apiKey: process.env.AIRTABLE_API_KEY,
});

const airtable = Airtable.base(process.env.AIRTABLE_BASE_ID);

// Test Airtable connection
console.log("Testing Airtable connection...");
airtable.table("Preprint Info ONLY").select({ maxRecords: 1 }).firstPage((err, records) => {
  if (err) {
    console.error("Airtable connection failed:", err);
    process.exit(1);
  }
  
  if (!records || records.length === 0) {
    console.warn("No records found in 'Preprint Info ONLY' table. Please check your Airtable base.");
  } else {
    console.log(`Airtable connection successful! Found ${records.length} records.`);
  }
});

// Helper to safely slugify strings
const safeSlugify = (str) => {
  if (!str || typeof str !== 'string') return slugify('untitled', { lower: true });
  return slugify(str, { lower: true });
};

// Import Preprints first
const PREPRINT_PUBS = await airtableToPubPub(
  airtable,
  "Preprint Info ONLY",  // Airtable table name
  pubTypes.preprint,
  stages.airtable,
  {
    // Based on the Airtable schema analysis
    "title": (record) => record.get("Title (from Selected)") || "Untitled Preprint",
    "abstract": (record) => record.get("Abstract") || "",
    "domain": (record) => {
      const domain = record.get("Domain");
      return domain && Array.isArray(domain) ? domain.join(", ") : "";
    },
    "team": (record) => record.get("Team/Domain") || "",
    // Add preprint ID as a field for reference
    "preprint-id": (record) => record.get("Preprint ID") || "",
    // Generate slug from title
    "slug": (record) => {
      const customSlug = record.get("Slug");
      if (customSlug && typeof customSlug === 'string') return customSlug;
      
      const title = record.get("Title (from Selected)");
      return safeSlugify(title || "preprint");
    }
  },
  "airtable-id",
  [],  // Empty array instead of null
  "Grid view"  // Use Grid view instead of PubPub Platform Import view
);

console.log(`Created/updated ${PREPRINT_PUBS.length} preprint publications`);

// Then import Reviewers with references to Preprints
const REVIEWER_PUBS = await airtableToPubPub(
  airtable,
  "Student Reviewer Inputs",  // Airtable table name
  pubTypes.reviewer,
  stages.nonPubs,
  {
    // Based on the expected fields for Reviewers
    "reviewer-name": (record) => {
      const fullName = record.get("First + Last Name");
      if (fullName && typeof fullName === 'string') return fullName;
      
      const firstName = record.get("First Name (Proposed Reviewer)") || "";
      const lastName = record.get("Last Name (Proposed Reviewer)") || "";
      return (firstName + " " + lastName).trim() || "Unnamed Reviewer";
    },
    "email": (record) => record.get("Reviewer Email") || "",
    "justification-for-invite": (record) => record.get("Justification for Invite") || "",
    "affiliation": (record) => record.get("Affiliation") || "",
    "reviewer-title": (record) => record.get("Reviewer Title") || "",
    "highest-degree": (record) => record.get("Highest Degree") || "",
    "subdiscipline": (record) => record.get("Subdiscipline") || "",
    "link-to-profile": (record) => record.get("Link to Profile") || "",
    
    // Reference to associated preprint - using the preprint ID to match
    "associated-preprint": (record) => {
      const preprintId = record.get("Preprint ID (pulled)");
      if (!preprintId) return [];
      
      return getRelatedPubsArray(
        preprintId,
        PREPRINT_PUBS,
        "airtable-id"
      );
    },
      
    // Generate slug from name
    "slug": (record) => {
      const customSlug = record.get("Slug");
      if (customSlug && typeof customSlug === 'string') return customSlug;
      
      const firstName = record.get("First Name (Proposed Reviewer)") || "";
      const lastName = record.get("Last Name (Proposed Reviewer)") || "";
      const fullName = record.get("First + Last Name") || "";
      
      if (firstName && lastName) {
        return safeSlugify(`${firstName}-${lastName}`);
      } else if (fullName) {
        return safeSlugify(fullName);
      } else {
        return safeSlugify("reviewer-" + Date.now());
      }
    }
  },
  "airtable-id",
  [],  // Empty array instead of null
  "Grid view"  // Use Grid view instead of PubPub Platform Import view
);

console.log(`Created/updated ${REVIEWER_PUBS.length} reviewer publications`);