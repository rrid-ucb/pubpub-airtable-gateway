import { baseHeaders } from "./utils.js";

const communitySlug = process.env.COMMUNITY_SLUG;

export default async function getPubs(
  pubTypeId,
  limit = 10000,
  callback = async () => {}
) {
  return new Promise(async function (resolve, reject) {
    await fetch(
      `https://app.pubpub.org/api/v0/c/${communitySlug}/site/pubs?pubTypeId=${pubTypeId}&limit=${limit}&withRelatedPubs=true`,
      {
        headers: baseHeaders,
        method: "GET",
      }
    )
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
