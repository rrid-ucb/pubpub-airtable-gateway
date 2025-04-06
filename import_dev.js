import Airtable from "airtable";
import airtableToPubPub from "./lib/airtableToPubPub.js";
import slugify from "slugify";

import { getRelatedPubsArray } from "./lib/utils.js";

const pubTypes = {
  narrative: process.env.NARRATIVE_TYPE_ID, //pubtype IDs
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

Airtable.configure({
  apiKey: process.env.AIRTABLE_API_KEY,
});

const airtable = Airtable.base(process.env.AIRTABLE_BASE_ID);

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

const ROLE_PUBS = await airtableToPubPub(
  airtable,
  "Contributor roles",
  pubTypes.roles,
  stages.nonPubs,
  {
    title: (record) => record.get("Role"),
    "byline-role": (record) => record.get("Byline"),
  },
  "airtable-id"
);

const INSTITUTION_PUBS = await airtableToPubPub(
  airtable,
  "Institution",
  pubTypes.institutions,
  stages.nonPubs,
  {
    title: (record) => record.get("Name"),
  },
  "airtable-id"
);

const CONTRIBUTOR_PUBS = await airtableToPubPub(
  airtable,
  "Role assignments",
  pubTypes.contributor,
  stages.nonPubs,
  {
    "full-name": (record) => `${record.get("Contributors")}`,
    "contributor-person": (record) =>
      getRelatedPubsArray(
        record.get("Contributor"),
        PEOPLE_PUBS,
        "airtable-id"
      ),
    affiliations: (record) =>
      getRelatedPubsArray(
        record.get("Institution"),
        INSTITUTION_PUBS,
        "airtable-id"
      ),
    roles: (record) =>
      getRelatedPubsArray(record.get("Role"), ROLE_PUBS, "airtable-id"),
  },
  "airtable-id",
  ["Deleted from original contributor list"]
);

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
    narratives: (record) =>
      getRelatedPubsArray(
        record.get("Project narrative"),
        NARRATIVE_PUBS,
        "airtable-id"
      ),
    "doi-url": (record) => record.get("DOI"),
    doi: (record) =>
      record.get("DOI") && record.get("DOI").split("https://doi.org/")[1],
    "pub-url": (record) => record.get("Link to PubPub"),
    slug: (record) =>
      record.get("Slug") ??
      (record.get("Link to PubPub") &&
        record.get("Link to PubPub").split("/pub/")[1]),
    "pub-content-types": (record) =>
      getRelatedPubsArray(record.get("Pub type"), TYPE_PUBS, "airtable-id"),
    "publication-date": (record) =>
      record.get("Publication date") &&
      new Date(record.get("Publication date")).toISOString(),

    //unsure what these fields are for
    "google-drive-folder-url": (record) =>
      record.get("Link to folder with assets"),
    "typeform-url": (record) => record.get("Typeform link"),
    "twitter-collection-url": (record) =>
      record.get("Twitter collection link") &&
      record.get("Twitter collection link")[0],
    "icing-hashtags": (record) =>
      record.get("Icing hashtag (from Icing hashtags)"),


    "feedback-status": (record) => record.get("Current feedback status"),

    //NOTE: currently not just email. example: 
    //David S Khoury (dkhoury@kirby.unsw.edu.au)
    "author-email": (record) =>
      record.get("Author_corr (from Selected)") && 
      record.get("Author_corr (from Selected)").toString(),

      
    "social-count": (record) =>
      record.get("Number of posts") && record.get("Number of posts")[0],
  },
  "airtable-id",
  ["Internal pub for now", "New versions"]
);

const PREPRINT_PUBS = await airtableToPubPub(
    airtable,
    "Preprint Info ONLY",    // Your Airtable table name
    pubTypes.preprint,
    stages.nonPubs,
    {
      title: (record) => record.get("Title (from Selected)"),
      
      "doi-url": (record) => record.get("Link/DOI (from Selected)"),
      authors: (record) => record.get("Authors"),
      "preprint-id": (record) => record.get("PreprintID"),  // Store this for reference
      slug: (record) => 
        record.get("Slug") ?? slugify(record.get("Title"), { lower: true }),
    },
    "airtable-id"
  );

  const REVIEWER_PUBS = await airtableToPubPub(
    airtable,
    "Student Reviewer Inputs",
    pubTypes.reviewer,
    stages.nonPubs,
    {
      "full-name": (record) => 
        `${record.get("First Name (Proposed Reviewer)")} ${record.get("Last Name (Proposed Reviewer)")}`,
      email: (record) => record.get("Reviewer Email"),
      affiliation: (record) => record.get("Affiliation"),
      // Link to the associated preprint
      "associated-preprint": (record) =>
        getRelatedPubsArray(
          record.get("Preprint ID (pulled)"),  // Assuming this is the field name in Airtable
          PREPRINT_PUBS,
          "airtable-id"
        ),
      slug: (record) => 
        record.get("Slug") ?? 
        slugify(`${record.get("First Name")}-${record.get("Last Name")}`, { lower: true }),
    },
    "airtable-id"
  );