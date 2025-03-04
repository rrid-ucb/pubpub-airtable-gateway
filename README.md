# Airtable Gateway Template

This package contains a series of scripts and convenience functions used to sync content from [Airtable](https://airtable.com) bases to [PubPub Platform](https://knowledgefutures.org/platform) using the two system's APIs.
The code has been tested in production, but is somewhat rough and error-prone.
Use at your own risk.
In the future, we plan to build some of this functionality into Platform as an Action or Integration,
but we anticipate more custom applications will need to use this package or its successors for the forseeable future.

## Setup

1. Fork the repo
1. Install the node version specified in nvmrc (likely using a node version manager like [NVM](https://github.com/nvm-sh/nvm)).
1. Run `npm install`
1. Make a copy of .env_template (.env.production at minimum, .env if you have a demo community/airtable)
1. Modify/fill out the required environment variables for your community.
1. Customize import.js (see detailed instructions below)

## Running

The package exposes a few scripts to test and run the code.
You can run the code locally, or use any code runner that supports Node (e.g. GitHub actions) to run it programatically or via webhooks.
To run the code on a code runner, make sure to fill out all of the required environment variables on that service.
There are a few scripts mostly for testing or specific use cases.
These are the ones you're likely going to be running:

- `npm run upsert-dev`: Runs the import.js script, injecting environment variables from `.env` if available.
- `npm run upsert`: Runs the import.js script, injecting environment variables from `.env.production` if available.
- `npm run delete-dev`: Runs the delete.js script, which deletes all Pubs from a community, injecting environment variables from `.env` if available.
- `npm run delete`: Runs the delete.js script, which deletes all Pubs from a community, injecting environment variables from `.env.production` if available.

### Using GitHub Action Workflows

The package exposes two workflows (one for dev, one for prod) that can be used to run the code with GitHub Actions, in the `.github/workflows` directory.
They include dispatches that can be used to run the workflow either in the repository or via webhook, as described in [GitHub's API documentation](https://docs.github.com/en/rest/actions/workflows?apiVersion=2022-11-28).
To set these up, simply enter the required environment variables for your customization in your GitHub repo's "Secrets and Variables" setting.

## Customizing

You'll mostly want to customize the `import.js` script, which contains the logic for mapping from Airtable to PubPub.
The basic logic is to convert one Airtable "Table" to a "Type" of Pub in PubPub Platform, mapping fields along the way.
We recommend creating a "View" for every Airtable Table you want to sync that's specific to this script and contains every field you need for it.
That way, if you change underlying data, you won't break the gateway.

The main function, `airtableToPubPub`, takes as arguments:

- the Airtable base from the configured SDK (you could theoretically use multiple bases if you wanted),
- the name of the Airtable table to source from
- the stage to place the new pub in, an object contain a mapping of fields (more on this later)
- the PubPub field to use to store the airtable ID (used to do upserting)
- an optional array of Airtable field names that, if they are truthy, will cause the record to be excluded from the import
- the name of the Airtable view it will pull from (defaults to "PubPub Platform Import")

The function creates a new pub based on this information, or if it already exists (again, based on the airtable ID stored in PubPub), updates it with the any information provided, and returns an array of the created or updated pub's data from the PubPub Platform API.

### Field Mapping

`airtableToPubPub` takes as an argument an object, where each attribute that specifies mapping logic for each field for each Airtable row.
Each attribute's key is the name of the field in PubPub (without the communitySlug, which is read from environment variables).
Each attribute's value is a synchronous callback function that will be called, and should return the value of the PubPub field.
The callback function will be provided with the Airtable row's "record" function, allowing you to lookup data from Airtable for each field.
For example, to create a PubPub "title" field from an Airtable table's "name" field:

```
"title" => record.get("Name")
```

You can, of course, do more complicated (synchronous) processing of Airtable data here, such as combining fields from a row, performing regex, appending values, etc.

### Pub Relationships

A complication arises when you want to create a related pub field in PubPub (the equivalent of Airtable's "linked records").
To do this, the Pub you are adding as related pub field needs to already have been created.
This means you need to create Pub Types from Airtable in order, such that a Pub that contains a relationship field to another type of Pub is created _after_ the related type is created.

> E.g., if you have a "Review" pub with a relation field that contains "Article" pubs, the "Article" pubs need to be fetched first.

To facilitate creating relationships, the package contains `getRelatedPubsArray`, a convenience function for adding PubPub related fields.
The function takes as arguments:

- The Airtable linked record field
- The corresponding array of already-created Pubs, returned by a previous `airtableToPubPub` call
- The PubPub field that contains the airtable ID of the record (used for upserting values)

If there are circular PubPub relationship dependencies, you can call `airtableToPubPub` on the same Airtable table/Pub Type pair twice.
You just need to make sure that any Pubs you need to add as a relationship already exist before you attempt to create them.

Note that the `getRelatedPubsArray` function, when used with `airtableToPubPub`, is fairly greedy due to limitations with the PubPub API.
If there are any updates to any relationship field, it will delete and recreate all relationships in that field.
Thus, you should not rely on the PubPub relationship field value ID in your app (this is fairly rare).
