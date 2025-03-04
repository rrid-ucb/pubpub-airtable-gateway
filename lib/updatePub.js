import { jsonHeaders } from "./utils.js";

const communitySlug = process.env.COMMUNITY_SLUG;

export default async function updatePub(
  pubId,
  fieldValues,
  callback = async () => {}
) {
  return new Promise(async function (resolve, reject) {
    await fetch(
      `https://app.pubpub.org/api/v0/c/${communitySlug}/site/pubs/${pubId}`,
      {
        headers: jsonHeaders,
        method: "PATCH",
        body: JSON.stringify({
          ...fieldValues,
        }),
      }
    )
      .catch((error) => {
        console.error(error);
        reject(error);
      })
      .then(async (response) => {
        await response.json().then(async (res) => {
          if (!response.ok) {
            console.error(response.status, res);
          }
          await callback(res);
          resolve(res);
        });
      });
  });
}
