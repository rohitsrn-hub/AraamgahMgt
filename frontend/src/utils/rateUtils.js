// Mirrors backend/utils/report_calc.py's effective_category_rate() /
// effective_non_org_rate() / rate_components(). A booking bills at whichever
// rate was in effect on its own check-in date — never "today's" rate, and
// never a hardcoded Cat I/Cat II assumption. Every rate preview shown to the
// user (booking form, check-in bill summary, amend cost) must resolve
// through this so the number on screen matches what the backend actually
// charges, for any number of configured categories.
//
// settings.room_categories is the base rate — [{name, room_rent,
// license_fee, ...}]. settings.rate_history is a list of {effective_date,
// category_rates: {categoryName: {room_rent?, license_fee?}},
// non_org_room_rent?, non_org_license_fee?} entries; the latest one whose
// effective_date is on/before the check-in date wins, per field.

function parseDate(d) {
  const dt = d instanceof Date ? d : new Date(d);
  return d && !isNaN(dt.getTime()) ? dt : null;
}

function sortedHistory(settings) {
  return (settings?.rate_history || [])
    .filter((h) => h?.effective_date)
    .slice()
    .sort((a, b) => a.effective_date.localeCompare(b.effective_date));
}

/** The room_categories[] entry matching this name, or undefined. */
export function getCategoryConfig(settings, categoryName) {
  return (settings?.room_categories || []).find((c) => c.name === categoryName);
}

/** { rent, licenseFee } for ONE category, resolved for checkInDate. */
export function resolveCategoryRate(settings, categoryName, checkInDate) {
  const base = getCategoryConfig(settings, categoryName);
  let rent = base?.room_rent ?? 470;
  let licenseFee = base?.license_fee ?? 30;

  const ci = parseDate(checkInDate);
  if (!ci) return { rent, licenseFee };
  ci.setHours(0, 0, 0, 0);

  for (const h of sortedHistory(settings)) {
    const eff = parseDate(h.effective_date);
    if (!eff) continue;
    eff.setHours(0, 0, 0, 0);
    if (eff > ci) continue;
    const override = h.category_rates?.[categoryName];
    if (override?.room_rent != null) rent = override.room_rent;
    if (override?.license_fee != null) licenseFee = override.license_fee;
  }
  return { rent, licenseFee };
}

/** { rent, licenseFee } for the flat Non-Org rate, resolved for checkInDate. */
export function resolveNonOrgRate(settings, checkInDate) {
  let rent = settings?.non_org_room_rent ?? 570;
  let licenseFee = settings?.non_org_license_fee ?? 30;

  const ci = parseDate(checkInDate);
  if (!ci) return { rent, licenseFee };
  ci.setHours(0, 0, 0, 0);

  for (const h of sortedHistory(settings)) {
    const eff = parseDate(h.effective_date);
    if (!eff) continue;
    eff.setHours(0, 0, 0, 0);
    if (eff > ci) continue;
    if (h.non_org_room_rent != null) rent = h.non_org_room_rent;
    if (h.non_org_license_fee != null) licenseFee = h.non_org_license_fee;
  }
  return { rent, licenseFee };
}

/** { rent, licenseFee } for one room, resolved for checkInDate. `category`
 * is any configured category name, not just "Cat I"/"Cat II". */
export function getRoomRate(settings, checkInDate, isOrg, category) {
  if (!isOrg) return resolveNonOrgRate(settings, checkInDate);
  return resolveCategoryRate(settings, category, checkInDate);
}
