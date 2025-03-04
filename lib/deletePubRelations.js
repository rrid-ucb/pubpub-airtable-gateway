import { jsonHeaders } from "./utils.js";

const communitySlug = process.env.COMMUNITY_SLUG;

export default async function deletePubRelations(
  pubId,
  fieldValues,
  callback = async () => {}
) {
  return new Promise(async function (resolve, reject) {
    await fetch(
      `https://app.pubpub.org/api/v0/c/${communitySlug}/site/pubs/${pubId}/relations`,
      {
        headers: jsonHeaders,
        method: "DELETE",
        body: JSON.stringify(fieldValues),
      }
    )
      .catch((error) => {
        console.error(error);
        reject(error);
      })
      .then(async (response) => {
        await response.text().then(async (res) => {
          if (!response.ok) {
            console.warn("relation", pubId, fieldValues);
            console.error(response.status, res);
          }
          await callback(res);
          resolve(res);
        });
      });
  });
}
