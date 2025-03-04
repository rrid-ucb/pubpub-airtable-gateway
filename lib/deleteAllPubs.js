import { baseHeaders } from "./utils.js";
import deletePub from "./deletePub.js";

const communitySlug = process.env.COMMUNITY_SLUG;

export default async function deleteAllPubs(type = null) {
  return new Promise(async function (resolve, reject) {
    await fetch(
      `https://app.pubpub.org/api/v0/c/${communitySlug}/site/pubs?limit=10000&type=${type}`,
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
        if (!response.ok) {
          console.warn(response.status, response);
        }
        await response.json().then(async (pubs) => {
          for (let i = 0; i < pubs.length; i++) {
            await deletePub(pubs[i].id);
          }
          resolve(pubs);
        });
      });
  });
}
