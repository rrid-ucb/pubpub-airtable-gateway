import updatePub from "./updatePub.js";
import createPub from "./createPub.js";
import { filterPubByField } from "./utils.js";

export default async function upsertPubByField(
  pubTypeId = null,
  stageId = null,
  fieldSlug,
  fieldValue,
  values,
  pubs,
  callback = async () => {}
) {
  return new Promise(async function (resolve, reject) {
    // Get all existing pubs of given type
    const matchedPubs = filterPubByField(pubs, fieldSlug, fieldValue);
    // if there are matches, update
    if (matchedPubs.length > 0) {
      await matchedPubs.forEach(async (pub) => {
        const oldValues = {};
        pub.values.forEach((value) => {
          oldValues[value.fieldSlug] = value.value;
        });

        const newValues = {};
        // Find new values that are not null and not undefined and do not exist in old values or have changed from old ones
        for (const newKey in values) {
          if (
            (values[newKey] !== null &&
              values[newKey !== undefined] &&
              !oldValues[newKey]) ||
            oldValues[newKey] !== values[newKey]
          ) {
            newValues[newKey] = values[newKey];
          }
        }

        // Compare via string method since these (should) always be ordered, simple JSON
        // and return either update the pub and return the object or go straight to the existing one
        const updatedPub =
          Object.keys(newValues).length > 0
            ? await updatePub(pub.id, values, callback)
            : pub;
        resolve(updatedPub);
      });
      // otherwise, create new pubs
    } else {
      const createdPub = await createPub(pubTypeId, stageId, values, callback);
      resolve(createdPub);
    }
  });
}
