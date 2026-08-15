// Mirrors backend/utils/report_calc.py's effective_rate_settings()/rate_components().
// A booking bills at whichever rate was in effect on its own check-in date —
// never "today's" rate, never the flat base fields alone. Every rate preview
// shown to the user (booking form, check-in bill summary, amend cost) must
// resolve through this so the number on screen matches what the backend
// actually charges. Previously these read settings.cat_i_room_rent etc.
// directly, so a scheduled future rate change never showed up until the
// booking was actually saved.

const RATE_FIELDS = [
  "cat_i_room_rent", "cat_i_license_fee",
  "cat_ii_room_rent", "cat_ii_license_fee",
  "non_org_room_rent", "non_org_license_fee",
];

/** Resolve the rate fields that apply for a given check-in date (YYYY-MM-DD
 * string or Date). Falls back to the base settings fields if check_in_date
 * is missing/invalid or no history entry qualifies yet. */
export function resolveRateFields(settings, checkInDate) {
  const resolved = {};
  for (const key of RATE_FIELDS) {
    if (settings?.[key] != null) resolved[key] = settings[key];
  }

  const ci = checkInDate instanceof Date ? checkInDate : new Date(checkInDate);
  if (!checkInDate || isNaN(ci.getTime())) return resolved;
  ci.setHours(0, 0, 0, 0);

  const history = (settings?.rate_history || [])
    .filter((h) => h?.effective_date)
    .slice()
    .sort((a, b) => a.effective_date.localeCompare(b.effective_date));

  for (const h of history) {
    const eff = new Date(h.effective_date);
    eff.setHours(0, 0, 0, 0);
    if (eff <= ci) {
      for (const key of RATE_FIELDS) {
        if (h[key] != null) resolved[key] = h[key];
      }
    }
  }
  return resolved;
}

const DEFAULTS = {
  cat_i_room_rent: 470, cat_i_license_fee: 30,
  cat_ii_room_rent: 385, cat_ii_license_fee: 15,
  non_org_room_rent: 570, non_org_license_fee: 30,
};

/** { rent, licenseFee } for one room, resolved for checkInDate. */
export function getRoomRate(settings, checkInDate, isOrg, category) {
  const r = resolveRateFields(settings, checkInDate);
  const get = (key) => (r[key] != null ? r[key] : DEFAULTS[key]);
  if (!isOrg) {
    return { rent: get("non_org_room_rent"), licenseFee: get("non_org_license_fee") };
  }
  if (category === "Cat I") {
    return { rent: get("cat_i_room_rent"), licenseFee: get("cat_i_license_fee") };
  }
  return { rent: get("cat_ii_room_rent"), licenseFee: get("cat_ii_license_fee") };
}
