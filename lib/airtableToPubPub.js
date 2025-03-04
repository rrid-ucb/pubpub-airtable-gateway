import upsertPubByField from "./upsertPubByField.js";
import getPubs from "./getPubs.js";
import updatePubRelations from "./updatePubRelations.js";
import deletePubRelations from "./deletePubRelations.js";

const communitySlug = process.env.COMMUNITY_SLUG;

export default async function airtableToPubPub(
  airtableClient,
  airtableTable,
  pubTypeId,
  stageId,
  pubFieldMap,
  airtableIdPubField,
  excludedFields = [],
  viewName = "PubPub Platform Import",
  returnFields = []
) {
  return new Promise(async function (resolve, reject) {
    const existingPubs = await getPubs(pubTypeId, undefined);
    const pubs = [];
    airtableClient
      .table(airtableTable)
      .select({
        view: viewName,
      })
      .eachPage(
        async function page(records, fetchNextPage) {
          // This function (`page`) will get called for each page of records.
          for (const record of records) {
            let exclude = false;
            excludedFields.forEach((excludedField) => {
              record.get(excludedField) && (exclude = true);
            });
            if (exclude) {
              continue;
            }
            const pub = {};
            const relations = {};
            pub[`${communitySlug}:${airtableIdPubField}`] = record.id;
            for (const field in pubFieldMap) {
              const recordFieldValue = pubFieldMap[field](record);
              if (
                recordFieldValue instanceof Array &&
                typeof recordFieldValue[0] !== "string"
              ) {
                relations[`${communitySlug}:${field}`] = recordFieldValue;
              } else {
                // console.log("NOT A REL", field, recordFieldValue);
                pub[`${communitySlug}:${field}`] = recordFieldValue;
              }
            }
            const pubPub = await upsertPubByField(
              pubTypeId,
              stageId,
              `${communitySlug}:${airtableIdPubField}`,
              record.id,
              pub,
              existingPubs
            );
            // format the relations from the existing pub in PubPub
            const relationsToUpdateOrDelete = [];
            const pubpubRelations = {};
            const matchedExistingPubs = existingPubs.filter(
              (existingPub) => existingPub.id === pubPub.id
            )[0];
            if (matchedExistingPubs && matchedExistingPubs.values) {
              matchedExistingPubs.values
                .filter((value) => value.relatedPubId)
                .forEach((value) => {
                  const pubRelation = {
                    value: value.value,
                    relatedPubId: value.relatedPubId,
                  };
                  pubpubRelations[value.fieldSlug]
                    ? pubpubRelations[value.fieldSlug].push(pubRelation)
                    : (pubpubRelations[value.fieldSlug] = [pubRelation]);
                });
            }
            if (Object.keys(relations).length > 0) {
              const sortbyPubId = (a, b) =>
                a.relatedPubId > b.relatedPubId ? 1 : -1;
              for (const fieldSlug in relations) {
                const airtableString = JSON.stringify(
                  relations[fieldSlug].sort(sortbyPubId)
                );
                const pubpubString = pubpubRelations[fieldSlug]
                  ? JSON.stringify(pubpubRelations[fieldSlug].sort(sortbyPubId))
                  : JSON.stringify([]);
                if (airtableString !== pubpubString) {
                  relationsToUpdateOrDelete.push({
                    airtable: relations[fieldSlug],
                    pubpub: pubpubRelations[fieldSlug],
                  });
                }
              }
            }
            if (relationsToUpdateOrDelete.length > 0) {
              for (const relationKey in pubpubRelations) {
                pubpubRelations[relationKey] = "*";
              }
              await deletePubRelations(pubPub.id, pubpubRelations);
              await updatePubRelations(pubPub.id, relations);
            }
            pubs.push(pubPub);
          }
          // To fetch the next page of records, call `fetchNextPage`.
          // If there are more records, `page` will get called again.
          // If there are no more records, `done` will get called.
          fetchNextPage();
        },
        function done(err) {
          if (err) {
            console.error(err);
            return;
          }
          resolve(pubs);
        }
      );
  });
}
