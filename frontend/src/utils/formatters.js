// Indian number system: 1,23,45,678.00
export function fmtINR(amount, decimals = 2) {
  const num = typeof amount === "number" ? amount : parseFloat(amount) || 0;
  return "₹" + new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

// Today's calendar date (YYYY-MM-DD) in IST — the guesthouse's timezone. new Date().toISOString()
// is UTC, a day behind between 00:00 and 05:30 IST, which put yesterday's date on the
// check-out screen in the early hours.
export function istTodayStr() {
  return new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });
}
