import { jsonHeaders } from "./utils.js";

const communitySlug = process.env.COMMUNITY_SLUG;

export default async function createPub(
  pubTypeId,
  stageId = null,
  fieldValues,
  callback = async () => {}
) {
  return new Promise(async function (resolve, reject) {
    await fetch(`https://app.pubpub.org/api/v0/c/${communitySlug}/site/pubs`, {
      headers: jsonHeaders,
      method: "POST",
      body: JSON.stringify({
        pubTypeId: pubTypeId,
        stageId: stageId,
        values: fieldValues,
      }),
    })
      .catch((error) => {
        console.error(error);
        reject(error);
      })
      .then(async (response) => {
        await response.json().then(async (res) => {
          if (!response.ok) {
            console.warn(response.status, res);
          }
          await callback(res);
          resolve(res);
        });
      });
  });
}
