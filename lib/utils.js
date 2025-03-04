const communitySlug = process.env.COMMUNITY_SLUG;

export const baseHeaders = {
  Authorization: `Bearer ${process.env.PUBPUB_API_KEY}`,
  Prefer: "return=representation",
  Accept: "*/*",
  "user-agent": "airtable-gateway",
};

export const jsonHeaders = {
  ...baseHeaders,
  "Content-Type": "application/json",
};

export function filterPubByField(pubs, fieldSlug, fieldValue) {
  return pubs.filter((pub) => {
    if (!pub.values) {
      console.warn("EMPTY PUB:", pub);
      return false;
    }
    const matchedValues = pub.values.filter((value) => {
      return value.fieldSlug === fieldSlug && value.value === fieldValue;
    });
    return matchedValues.length > 0 ? matchedValues : false;
  });
}

export function getRelatedPubsArray(
  recordIds = [],
  possiblyRelatedPubs,
  uniqueFieldName
) {
  const relationValues = [];
  recordIds.forEach((recordId) => {
    const matchedPubs = filterPubByField(
      possiblyRelatedPubs,
      `${communitySlug}:${uniqueFieldName}`,
      recordId
    );
    matchedPubs.forEach((matchedPub) => {
      relationValues.push({
        value: null,
        relatedPubId: matchedPub.id,
      });
    });
  });
  return relationValues;
}
