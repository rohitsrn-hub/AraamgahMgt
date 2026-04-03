import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import { format } from "date-fns";

const REST_HOUSE_NAME = "ARAAMGAH MANAGEMENT SYSTEM";
const PRIMARY_COLOR = [31, 78, 121];   // dark blue
const ACCENT_COLOR = [70, 130, 180];   // steel blue
const LIGHT_GRAY = [245, 245, 245];
const BORDER_COLOR = [200, 200, 200];

function addHeader(doc, title, subtitle = "") {
  doc.setFillColor(...PRIMARY_COLOR);
  doc.rect(0, 0, doc.internal.pageSize.width, 18, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(11);
  doc.setFont("helvetica", "bold");
  doc.text(REST_HOUSE_NAME, doc.internal.pageSize.width / 2, 8, { align: "center" });
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.text(title, doc.internal.pageSize.width / 2, 13, { align: "center" });
  if (subtitle) {
    doc.text(subtitle, doc.internal.pageSize.width / 2, 17, { align: "center" });
  }
  doc.setTextColor(0, 0, 0);
  return 22;
}

function addFooter(doc) {
  const pageW = doc.internal.pageSize.width;
  const pageH = doc.internal.pageSize.height;
  doc.setDrawColor(...BORDER_COLOR);
  doc.line(10, pageH - 12, pageW - 10, pageH - 12);
  doc.setFontSize(7);
  doc.setTextColor(120, 120, 120);
  doc.text(`Generated: ${format(new Date(), "dd MMM yyyy HH:mm")}`, 10, pageH - 7);
  doc.text("E-ARMS — Araamgah Management System", pageW / 2, pageH - 7, { align: "center" });
  doc.text(`Page ${doc.internal.getCurrentPageInfo().pageNumber}`, pageW - 10, pageH - 7, { align: "right" });
  doc.setTextColor(0, 0, 0);
}

// ===== CHECKOUT RECEIPT (Half A4 = A5 landscape) =====
export function generateCheckoutReceipt(booking, settings) {
  const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a5" });
  const W = doc.internal.pageSize.width;
  let y = addHeader(doc, "CHECKOUT RECEIPT", `Booking # ${booking.booking_number}`);
  y += 3;

  const isDefCiv = (booking.guest_rank || "").toLowerCase() === "def civ";
  const cats = booking.room_categories || [];
  const catLabel = [...new Set(cats)].join(", ") || "N/A";
  const roomNums = (booking.room_numbers || []).join(", ") || booking.room_number || "N/A";
  const nights = Math.ceil(
    (new Date(booking.check_out_date) - new Date(booking.check_in_date)) / 86400000
  );

  // Guest info
  doc.setFillColor(...LIGHT_GRAY);
  doc.rect(10, y, W - 20, 22, "F");
  doc.setFontSize(9);
  doc.setFont("helvetica", "bold");
  doc.text("GUEST DETAILS", 13, y + 5);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  const g = booking;
  doc.text(`Name: ${g.guest_name || "—"}`, 13, y + 11);
  doc.text(`Rank: ${g.guest_rank || "—"}  |  Unit: ${g.guest_unit || "—"}`, 13, y + 16);
  doc.text(`Service: ${g.service_type || "—"}${g.command_hq ? "  Cmd: " + g.command_hq : ""}`, W / 2 + 5, y + 11);
  doc.text(`Army No: ${g.army_number || "—"}  |  Mob: ${g.guest_contact || "—"}`, W / 2 + 5, y + 16);
  doc.text(`Service Status: ${g.guest_service_status || "—"}`, 13, y + 21);
  y += 26;

  // Stay details
  doc.setFillColor(...LIGHT_GRAY);
  doc.rect(10, y, W - 20, 16, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("STAY DETAILS", 13, y + 5);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.text(`Room: ${roomNums}  (${catLabel})`, 13, y + 11);
  doc.text(`Check-in: ${g.check_in_date}  →  Check-out: ${g.check_out_date}  |  Nights: ${nights}`, W / 2 - 10, y + 11);
  y += 20;

  // Charges table
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("CHARGES", 13, y + 5);
  y += 7;

  const numRooms = (booking.room_numbers || [1]).length;
  let roomRent, licFee;
  if (isDefCiv) {
    roomRent = (settings?.def_civ_room_rent || 570);
    licFee = (settings?.def_civ_license_fee || 30);
  } else if (catLabel.includes("Cat I") && !catLabel.includes("Cat II")) {
    roomRent = (settings?.cat_i_room_rent || 470);
    licFee = (settings?.cat_i_license_fee || 30);
  } else {
    roomRent = (settings?.cat_ii_room_rent || 385);
    licFee = (settings?.cat_ii_license_fee || 15);
  }

  const rr = roomRent * nights * numRooms;
  const lf = licFee * nights * numRooms;
  const eb = (booking.extra_beds || 0) * 75;
  const total = rr + lf + eb;
  const balance = booking.balance_amount || (total - (booking.advance_paid || 0));

  autoTable(doc, {
    startY: y,
    head: [["Description", "Calculation", "Amount (₹)"]],
    body: [
      ["Room Rent", `₹${roomRent} × ${nights} nights × ${numRooms} room(s)`, rr.toFixed(2)],
      ["License Fee", `₹${licFee} × ${nights} nights × ${numRooms} room(s)`, lf.toFixed(2)],
      ...(eb > 0 ? [["Extra Beds", `${booking.extra_beds} bed(s) × ₹75`, eb.toFixed(2)]] : []),
      ["Total Amount", "", total.toFixed(2)],
      ["Advance Paid", "", `(${(booking.advance_paid || 0).toFixed(2)})`],
      ["Balance Collected", "", balance.toFixed(2)],
    ],
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: PRIMARY_COLOR, textColor: 255, fontSize: 8 },
    columnStyles: { 0: { cellWidth: 45 }, 1: { cellWidth: 80 }, 2: { cellWidth: 30, halign: "right", fontStyle: "bold" } },
    rowStyles: (row) => {
      if (row.index === 3) return { fillColor: [200, 230, 200] };
      if (row.index === row.table.body.length - 1) return { fillColor: [170, 210, 170], fontStyle: "bold" };
    },
    margin: { left: 10, right: 10 }
  });

  y = doc.lastAutoTable.finalY + 10;

  // Signature lines
  doc.setFontSize(8);
  doc.line(13, y + 8, 65, y + 8);
  doc.line(W - 65, y + 8, W - 13, y + 8);
  doc.text("(Guest Signature / Atithi ka hastakshar)", 13, y + 13);
  doc.text("(Duty Staff Signature)", W - 65, y + 13);

  addFooter(doc);
  doc.save(`receipt_${booking.booking_number}.pdf`);
}

// ===== PENDING REFUNDS PDF =====
export function generateRefundsPDF(refunds) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const W = doc.internal.pageSize.width;
  let y = addHeader(doc, "PENDING REFUNDS REPORT", `Generated: ${format(new Date(), "dd MMM yyyy")}`);
  y += 5;

  if (refunds.length === 0) {
    doc.setFontSize(12);
    doc.text("No pending refunds at this time.", W / 2, y + 20, { align: "center" });
    addFooter(doc);
    doc.save("pending_refunds.pdf");
    return;
  }

  autoTable(doc, {
    startY: y,
    head: [["#", "Booking No", "Guest Name", "Amount (₹)", "Bank Name", "Account No", "IFSC / UPI"]],
    body: refunds.map((r, i) => [
      i + 1,
      r.booking_number,
      r.guest_name,
      `₹${r.amount}`,
      r.bank_name || "—",
      r.bank_account || "—",
      r.bank_ifsc || r.upi_id || r.upi_phone || r.upi_number || "—"
    ]),
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: PRIMARY_COLOR, textColor: 255, fontSize: 8 },
    alternateRowStyles: { fillColor: LIGHT_GRAY },
    columnStyles: { 0: { cellWidth: 8 }, 3: { halign: "right" } },
    margin: { left: 10, right: 10 }
  });

  // Total
  const total = refunds.reduce((sum, r) => sum + (r.amount || 0), 0);
  const finalY = doc.lastAutoTable.finalY + 5;
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text(`Total Pending Refunds: ₹${total.toFixed(2)}  (${refunds.length} guest(s))`, W - 10, finalY, { align: "right" });

  addFooter(doc);
  doc.save("pending_refunds.pdf");
}

// ===== MONTHLY REPORT PDF =====
export function generateMonthlyReportPDF(data, settings) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const W = doc.internal.pageSize.width;
  let y = addHeader(
    doc,
    `MONTHLY REPORT — ${data.month_name?.toUpperCase()} ${data.year}`,
    "REST HOUSE OCCUPANCY & FINANCIAL SUMMARY"
  );
  y += 5;

  // Command breakdown table
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("COMMAND-WISE OCCUPANCY", 10, y);
  y += 4;

  const cmdRows = (data.command_breakdown || []).map((c, i) => [
    i + 1, c.command, c.guests, c.days
  ]);
  cmdRows.push(["", "TOTAL", data.total_guests, data.total_days]);

  autoTable(doc, {
    startY: y,
    head: [["No", "Command / Service", "Total Guests", "No of Days"]],
    body: cmdRows,
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: PRIMARY_COLOR, textColor: 255 },
    alternateRowStyles: { fillColor: LIGHT_GRAY },
    columnStyles: { 0: { cellWidth: 10 }, 2: { halign: "center" }, 3: { halign: "center" } },
    foot: [],
    margin: { left: 10, right: 10 }
  });

  y = doc.lastAutoTable.finalY + 8;

  // License fee section
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("LICENSE FEE CALCULATION", 10, y);
  y += 4;

  const lf = data.license_fees || {};
  const lfRows = [
    ["JCO (Cat I Rooms)", `${lf.jco?.days || 0} days × ₹${lf.jco?.rate || 30}`, `₹${(lf.jco?.total || 0).toFixed(2)}`],
    ["OR (Cat II Rooms)", `${lf.or?.days || 0} days × ₹${lf.or?.rate || 15}`, `₹${(lf.or?.total || 0).toFixed(2)}`],
    ["Def Civ", `${lf.def_civ?.days || 0} days × ₹${lf.def_civ?.rate || 30}`, `₹${(lf.def_civ?.total || 0).toFixed(2)}`],
    ["TOTAL LICENSE FEE", "", `₹${(data.total_license_fee || 0).toFixed(2)}`],
  ];

  autoTable(doc, {
    startY: y,
    head: [["Category", "Calculation", "License Fee (₹)"]],
    body: lfRows,
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: [100, 120, 160], textColor: 255 },
    alternateRowStyles: { fillColor: LIGHT_GRAY },
    columnStyles: { 2: { halign: "right", fontStyle: "bold" } },
    margin: { left: 10, right: 10 }
  });

  y = doc.lastAutoTable.finalY + 8;

  // Financial summary
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text(`FINANCIAL SUMMARY — ${data.month_name?.toUpperCase()} ${data.year}`, 10, y);
  y += 4;

  const r = data.rates || {};
  const summaryRows = [
    ["JCO (Cat I)", `${data.jco_days || 0} days × ₹${r.cat_i_room_rent || 470} (room rent)`, `₹${((data.jco_days || 0) * (r.cat_i_room_rent || 470)).toFixed(2)}`],
    ["OR (Cat II)", `${data.or_days || 0} days × ₹${r.cat_ii_room_rent || 385} (room rent)`, `₹${((data.or_days || 0) * (r.cat_ii_room_rent || 385)).toFixed(2)}`],
    ["Def Civ", `${data.def_civ_days || 0} days × ₹${r.def_civ_room_rent || 570} (room rent)`, `₹${((data.def_civ_days || 0) * (r.def_civ_room_rent || 570)).toFixed(2)}`],
    ["Room Rent Sub-Total", "", `₹${(data.room_rent_total || 0).toFixed(2)}`],
    ["License Fee Total", "", `₹${(data.total_license_fee || 0).toFixed(2)}`],
    ["Extra Beds", `${data.extra_beds_total || 0} bed-nights × ₹75`, `₹${(data.extra_bed_amount || 0).toFixed(2)}`],
    ["GRAND TOTAL", "", `₹${(data.grand_total || 0).toFixed(2)}`],
  ];

  autoTable(doc, {
    startY: y,
    head: [["Description", "Calculation", "Amount (₹)"]],
    body: summaryRows,
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: [70, 150, 80], textColor: 255 },
    alternateRowStyles: { fillColor: LIGHT_GRAY },
    columnStyles: { 2: { halign: "right", fontStyle: "bold" } },
    didParseCell: (data) => {
      if (data.row.index === summaryRows.length - 1) {
        data.cell.styles.fillColor = [180, 220, 180];
        data.cell.styles.fontStyle = "bold";
      }
    },
    margin: { left: 10, right: 10 }
  });

  y = doc.lastAutoTable.finalY + 8;

  // Advance & occupancy summary
  const statsRows = [
    ["Total Rooms", data.total_rooms || 15],
    ["Total Days in Month", data.days_in_month],
    ["Total Booked Room-Days", data.total_booked_days || 0],
    ["Average Occupancy", `${data.avg_occupancy || 0}%`],
    ["Advance Received", `₹${(data.advance_received || 0).toFixed(2)}`],
    ["Advance Adjusted in Bills", `₹${(data.advance_adjusted || 0).toFixed(2)}`],
    ["Balance Advance", `₹${(data.balance_advance || 0).toFixed(2)}`],
    ["No-shows (advance paid, cancelled)", data.no_shows || 0],
  ];

  autoTable(doc, {
    startY: y,
    head: [["Metric", "Value"]],
    body: statsRows,
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: [150, 100, 60], textColor: 255 },
    alternateRowStyles: { fillColor: LIGHT_GRAY },
    columnStyles: { 1: { halign: "right", fontStyle: "bold" } },
    margin: { left: 10, right: 10 }
  });

  // Signature lines
  const sigY = doc.lastAutoTable.finalY + 12;
  if (sigY < 240) {
    doc.setFontSize(8);
    doc.line(15, sigY, 75, sigY);
    doc.line(W / 2 - 30, sigY, W / 2 + 30, sigY);
    doc.line(W - 75, sigY, W - 15, sigY);
    doc.text("Officer In Charge", 15, sigY + 5);
    doc.text("Chairman", W / 2, sigY + 5, { align: "center" });
    doc.text("Commanding Officer", W - 15, sigY + 5, { align: "right" });
  }

  addFooter(doc);
  doc.save(`monthly_report_${data.month_name}_${data.year}.pdf`);
}
