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


//Is this a template for reviewers?
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
      "google-drive-folder-url": (record) =>
        record.get("Link to folder with assets"),
      "typeform-url": (record) => record.get("Typeform link"),
      "twitter-collection-url": (record) =>
        record.get("Twitter collection link") &&
        record.get("Twitter collection link")[0],
      "icing-hashtags": (record) =>
        record.get("Icing hashtag (from Icing hashtags)"),
      "feedback-status": (record) => record.get("Current feedback status"),
      "author-email": (record) =>
        record.get("Point person email") &&
        record.get("Point person email").toString(),
      "social-count": (record) =>
        record.get("Number of posts") && record.get("Number of posts")[0],
    },
    "airtable-id",
    ["Internal pub for now", "New versions"]
  );

const PREPRINT_PUBS = await airtableToPubPub(
    airtable,
    "Preprint Info ONLY",
    pubTypes.preprint,
    stages.airtable,
    {
      "title": (record) => record.get("Title (from Selected)"),
      "abstract": (record) => record.get("Abstract"),
      "domain": (record) => record.get("Domain"),
      "team": (record) => record.get("Team/Domain"),
     // 'keywords': (record) => record.get("Keywords"),
      "doi-url": (record) => record.get("Link/DOI (from Selected)"),
     
    //NOTE: Sometimes the link is not a doi. may have to have alternative parsing here.
      "doi": (record) =>
        record.get("Link/DOI (from Selected)") && record.get("Link/DOI (from Selected)").split("https://doi.org/")[1],
      

    //NOTE: Two fields with inconsistencies in formatting. Author_corr will have just name, just email, or both. example: 
    //David S Khoury (dkhoury@kirby.unsw.edu.au). Can create a field that regex this in airtable.
    //'Author Email' is a regex of this field, so sometimes has errors when its not in the above format.
     "author-email": (record) =>
        record.get("Author Email") && 
        record.get("Author Email").toString(),
  
      "preprint-id": (record) => record.get("Preprint ID"),
      slug: (record) => 
        record.get("Slug") ?? slugify(record.get("Title (from Selected)"), { lower: true }),
    },
    "airtable-id"
);

const REVIEWER_PUBS = await airtableToPubPub(
    airtable,
    "Student Reviewer Inputs",
    pubTypes.reviewer,
    stages.airtable,
    {
      "reviewer-name": (record) => record.get("First + Last Name"), //NOTE: we have a first and last name field. this is the concatenated version
      "email": (record) => record.get("Reviewer Email"),
      "justification-for-invite": (record) => record.get("Justification for Invite"),
      "affiliation": (record) => record.get("Affiliation"),
      "reviewer-title": (record) => record.get("Reviewer Title"),
      "highest-degree": (record) => record.get("Highest Degree"),
      "subdiscipline": (record) => record.get("Subdiscipline"),
      "link-to-profile": (record) => record.get("Link to Profile"),
      
      "associated-preprint": (record) =>
        getRelatedPubsArray(
          record.get("Preprint ID (pulled)"),
          PREPRINT_PUBS,
          "airtable-id"
        ),
      slug: (record) => 
        record.get("Slug") ?? 
        slugify(`${record.get("First Name (Proposed Reviewer)")}-${record.get("Last Name (Proposed Reviewer)")}`, { lower: true }),
    },
    "airtable-id"
);