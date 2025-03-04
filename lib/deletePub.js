import { baseHeaders } from "./utils.js";

const communitySlug = process.env.COMMUNITY_SLUG;

export default async function deletePub(pubId, callback = async () => {}) {
  return new Promise(async function (resolve, reject) {
    const pubURL = `https://app.pubpub.org/api/v0/c/${communitySlug}/site/pubs/${pubId}`;
    await fetch(pubURL, {
      headers: baseHeaders,
      method: "DELETE",
    })
      .catch((error) => {
        console.error(error);
        reject(error);
      })
      .then(async (response) => {
        await response.text().then(async (res) => {
          if (!response.ok) {
            console.warn(response.status, res);
          }
          await callback(res);
          resolve(res);
        });
      });
  });
}
