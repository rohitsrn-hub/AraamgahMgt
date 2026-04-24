// Indian number system: 1,23,45,678.00
export function fmtINR(amount, decimals = 2) {
  const num = typeof amount === "number" ? amount : parseFloat(amount) || 0;
  return "₹" + new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}
