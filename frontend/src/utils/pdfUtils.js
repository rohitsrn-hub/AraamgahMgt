import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import { format } from "date-fns";

// Indian number system formatter: 1,23,45,678.00
export function fmtINR(amount, decimals = 2) {
  const num = typeof amount === "number" ? amount : parseFloat(amount) || 0;
  return "₹" + new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

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
  doc.text("SARAI — Shillong Aramgah Room Automation Interface", pageW / 2, pageH - 7, { align: "center" });
  doc.text(`Page ${doc.internal.getCurrentPageInfo().pageNumber}`, pageW - 10, pageH - 7, { align: "right" });
  doc.setTextColor(0, 0, 0);
}

// ===== CHECKOUT RECEIPT (Half A4 = A5 landscape) =====
export function generateCheckoutReceipt(booking, settings) {
  const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a5" });
  const W = doc.internal.pageSize.width;
  let y = addHeader(doc, "CHECKOUT RECEIPT", `Booking # ${booking.booking_number}`);
  y += 3;

  const isNonOrg = !(booking.is_org);
  const cats = booking.room_categories || [];
  const catLabel = [...new Set(cats)].join(", ") || "N/A";
  const roomNums = (booking.room_numbers || []).join(", ") || booking.room_number || "N/A";
  
  // Use actual check-in/check-out dates if available, otherwise fall back to booking dates
  const checkInDateRaw = booking.actual_check_in || booking.check_in_date;
  const checkOutDateRaw = booking.actual_check_out || booking.check_out_date;
  
  // Format dates to very short format to avoid overflow (dd MMM)
  const checkInDate = format(new Date(checkInDateRaw), "dd MMM");
  const checkOutDate = format(new Date(checkOutDateRaw), "dd MMM");
  
  const nights = Math.ceil(
    (new Date(checkOutDateRaw) - new Date(checkInDateRaw)) / 86400000
  );

  // Guest info
  doc.setFillColor(...LIGHT_GRAY);
  doc.rect(10, y, W - 20, 18, "F");
  doc.setFontSize(9);
  doc.setFont("helvetica", "bold");
  doc.text("GUEST DETAILS", 13, y + 5);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  const g = booking;
  doc.text(`Name: ${g.guest_name || "—"}`, 13, y + 11);
  doc.text(`Type: ${g.is_org ? "Organization" : "Non-Organization"}${g.org_color ? "  |  Color: " + g.org_color : ""}`, 13, y + 16);
  doc.text(`Mobile: ${g.guest_contact || "—"}`, W / 2 + 5, y + 11);
  y += 22;

  // Stay details
  doc.setFillColor(...LIGHT_GRAY);
  doc.rect(10, y, W - 20, 16, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("STAY DETAILS", 13, y + 5);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.text(`Room: ${roomNums}  (${catLabel})`, 13, y + 11);
  doc.text(`Check-in: ${checkInDate}  →  Check-out: ${checkOutDate}  |  Nights: ${nights}`, W / 2 - 10, y + 11);
  y += 20;

  // Charges table - use same calculation as checkout form
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("CHARGES", 13, y + 5);
  y += 7;

  // Calculate based on actual stay (same as checkout form)
  const roomCategories = booking.room_categories || [];
  const numRooms = booking.num_rooms || (booking.room_ids || []).length || 1;
  
  let totalRoomCharges = 0;
  
  // Calculate room charges based on room_guest_mapping if available (accurate per-room rates)
  const roomGuestMapping = booking.room_guest_mapping || [];
  
  if (roomGuestMapping.length > 0) {
    // Use room-guest mapping for accurate calculation (considers org cards per room)
    roomGuestMapping.forEach(room => {
      const category = room.room_category || "Cat I";
      const chargeCategory = room.charge_category || category;
      
      let ratePerNight;
      if (chargeCategory === "Non-Org") {
        // Non-Org rate (same for all categories)
        ratePerNight = (settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30);
      } else {
        // Organization rate
        if (category === "Cat I") {
          ratePerNight = (settings?.cat_i_room_rent || 470) + (settings?.cat_i_license_fee || 30);
        } else {
          ratePerNight = (settings?.cat_ii_room_rent || 385) + (settings?.cat_ii_license_fee || 15);
        }
      }
      
      totalRoomCharges += ratePerNight * nights;
    });
  } else if (roomCategories.length > 0) {
    // Fallback: Use room categories (less accurate - assumes all same guest type)
    roomCategories.forEach(category => {
      let ratePerNight;
      
      if (isNonOrg) {
        // Non-Org rate
        ratePerNight = (settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30);
      } else {
        // Organization rate
        if (category === "Cat I") {
          ratePerNight = (settings?.cat_i_room_rent || 470) + (settings?.cat_i_license_fee || 30);
        } else {
          ratePerNight = (settings?.cat_ii_room_rent || 385) + (settings?.cat_ii_license_fee || 15);
        }
      }
      
      totalRoomCharges += ratePerNight * nights;
    });
  } else {
    // Last resort fallback
    const ratePerNight = isNonOrg 
      ? ((settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30))
      : ((settings?.cat_i_room_rent || 470) + (settings?.cat_i_license_fee || 30));
    totalRoomCharges = ratePerNight * nights * numRooms;
  }
  
  // Advance paid
  const advancePaid = booking.advance_paid || 0;
  
  // Extra bed charges - ONLY use checkout values (actual usage)
  const extraBedActual = booking.extra_bed_charge_checkout || 0;
  
  // Calculate subtotal before advance
  const subtotal = totalRoomCharges + extraBedActual;
  
  // Final payment (from checkout form)
  const finalPayment = booking.final_payment || (subtotal - advancePaid);
  
  // Additional charges (if staff amended the amount)
  const expectedAmount = subtotal - advancePaid;
  const additionalCharges = finalPayment > expectedAmount ? (finalPayment - expectedAmount) : 0;
  
  // Build table rows
  const tableRows = [
    ["Room Charges", `${fmtINR(totalRoomCharges / nights, 0)} × ${nights} night(s) × ${numRooms} room(s)`, fmtINR(totalRoomCharges, 2)]
  ];
  
  // Add extra beds if any (actual usage at checkout)
  if (extraBedActual > 0) {
    const numBedsCheckout = booking.extra_beds_checkout || 0;
    const daysCheckout = booking.extra_bed_days || 0;
    tableRows.push(["Extra Beds (actual usage)", `${numBedsCheckout} bed(s) × ${daysCheckout} day(s) × ₹75`, fmtINR(extraBedActual, 2)]);
  }

  // Add advance deduction
  if (advancePaid > 0) {
    tableRows.push(["Less: Advance Paid", "", `(${fmtINR(advancePaid, 2)})`]);
  }

  // Add additional charges if any
  if (additionalCharges > 0) {
    tableRows.push(["Additional Charges at Checkout", "", fmtINR(additionalCharges, 2)]);
  }
  
  // Add final total
  tableRows.push(["Amount Collected at Checkout", "", fmtINR(finalPayment, 2)]);

  autoTable(doc, {
    startY: y,
    head: [["Description", "Calculation", "Amount (₹)"]],
    body: tableRows,
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: PRIMARY_COLOR, textColor: 255, fontSize: 8 },
    columnStyles: { 0: { cellWidth: 45 }, 1: { cellWidth: 80 }, 2: { cellWidth: 30, halign: "right", fontStyle: "bold" } },
    rowStyles: (row) => {
      const lastRowIndex = tableRows.length - 1;
      const advanceRowIndex = tableRows.findIndex(r => r[0] === "Less: Advance Paid");
      
      // Highlight advance paid row in orange
      if (row.index === advanceRowIndex && advanceRowIndex !== -1) {
        return { textColor: [200, 100, 0] };
      }
      
      // Highlight final amount row
      if (row.index === lastRowIndex) {
        return { fillColor: [170, 210, 170], fontStyle: "bold" };
      }
    },
    margin: { left: 10, right: 10 }
  });

  y = doc.lastAutoTable.finalY + 8;

  // Signature lines - positioned below table
  doc.setFontSize(8);
  doc.line(13, y, 65, y);
  doc.line(W - 65, y, W - 13, y);
  doc.text("(Guest Signature / Atithi ka hastakshar)", 13, y + 5);
  doc.text("(Duty Staff Signature)", W - 65, y + 5);

  addFooter(doc);
  
  // Save and return blob URL
  const filename = `receipt_${booking.booking_number}.pdf`;
  const pdfBlob = doc.output('blob');
  const blobUrl = URL.createObjectURL(pdfBlob);
  return { blobUrl, filename };
}

// ===== PENDING REFUNDS PDF =====
export function generateRefundsPDF(refunds) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const W = doc.internal.pageSize.width;
  const currentDate = format(new Date(), "dd MMM yyyy");
  let y = addHeader(doc, `REFUNDS DUE AS ON ${currentDate.toUpperCase()}`, "SARAI - Shillong Aramgah Room Automation Interface");
  y += 5;

  if (refunds.length === 0) {
    doc.setFontSize(12);
    doc.text("No pending refunds at this time.", W / 2, y + 20, { align: "center" });
    addFooter(doc);
    
    const filename = `SARAI_Refunds_Due_${format(new Date(), "ddMMMyyy")}.pdf`;
    const pdfBlob = doc.output('blob');
    const blobUrl = URL.createObjectURL(pdfBlob);
    
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    link.click();
    
    return { blobUrl, filename, count: 0 };
  }

  // Main refunds table with detailed columns
  autoTable(doc, {
    startY: y,
    head: [["#", "Booking ID", "Guest Name", "Amount (₹)", "Payment Mode", "Transaction ID", "Bank Details / UPI Details"]],
    body: refunds.map((r, i) => {
      // Build bank/UPI details string
      let paymentDetails = "";
      if (r.bank_name && r.bank_account) {
        paymentDetails = `Bank: ${r.bank_name}\nAcc: ${r.bank_account}`;
        if (r.bank_ifsc) paymentDetails += `\nIFSC: ${r.bank_ifsc}`;
      } else if (r.upi_id) {
        paymentDetails = `UPI ID: ${r.upi_id}`;
      } else if (r.upi_phone) {
        paymentDetails = `UPI Phone: ${r.upi_phone}`;
      } else if (r.upi_number) {
        paymentDetails = `UPI: ${r.upi_number}`;
      } else {
        paymentDetails = "—";
      }

      return [
        i + 1,
        r.booking_number || r.id || "—",
        r.guest_name || "—",
        r.amount ? fmtINR(r.amount, 0) : "₹0",
        r.payment_mode || "—",
        r.payment_id || r.transaction_id || "—",
        paymentDetails
      ];
    }),
    styles: { fontSize: 8, cellPadding: 2, overflow: 'linebreak' },
    headStyles: { fillColor: PRIMARY_COLOR, textColor: 255, fontSize: 8, fontStyle: 'bold' },
    alternateRowStyles: { fillColor: LIGHT_GRAY },
    columnStyles: { 
      0: { cellWidth: 8, halign: 'center' }, 
      1: { cellWidth: 20 },
      2: { cellWidth: 28 },
      3: { cellWidth: 18, halign: 'right' },
      4: { cellWidth: 20 },
      5: { cellWidth: 22 },
      6: { cellWidth: 40 }
    },
    margin: { left: 10, right: 10 }
  });

  // Summary table
  const totalAmount = refunds.reduce((sum, r) => sum + (r.amount || 0), 0);
  const totalBookings = refunds.length;
  let finalY = doc.lastAutoTable.finalY + 10;

  // Add summary heading
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10);
  doc.text("SUMMARY", 10, finalY);
  finalY += 5;

  // Summary table
  autoTable(doc, {
    startY: finalY,
    head: [["Description", "Value"]],
    body: [
      ["Total Bookings Cancelled", totalBookings.toString()],
      ["Total Amount to be Refunded", fmtINR(totalAmount, 2)]
    ],
    styles: { fontSize: 8, cellPadding: 3, overflow: 'linebreak', cellWidth: 'wrap' },
    headStyles: { fillColor: [51, 51, 51], textColor: 255, fontSize: 8, fontStyle: 'bold' },
    columnStyles: { 
      0: { cellWidth: 82, fontStyle: 'bold' },
      1: { cellWidth: 74, halign: 'right', fontStyle: 'bold', textColor: [200, 0, 0], overflow: 'linebreak' }
    },
    margin: { left: 10, right: 10 },
    theme: 'grid'
  });

  addFooter(doc);
  
  // Save and return blob URL
  const filename = `SARAI_Refunds_Due_${format(new Date(), "ddMMMyyy")}.pdf`;
  const pdfBlob = doc.output('blob');
  const blobUrl = URL.createObjectURL(pdfBlob);
  
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  link.click();
  
  return { blobUrl, filename, count: refunds.length };
}

// ===== MONTHLY REPORT PDF =====
export function generateMonthlyReportPDF(data, settings) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const W = doc.internal.pageSize.width;
  
  // Add formation signs if available
  const fmn1 = settings?.fmn_sign_1_url;
  const fmn2 = settings?.fmn_sign_2_url;
  
  let y = 5;
  
  // Add formation signs at top corners
  if (fmn1) {
    try {
      doc.addImage(fmn1, 'PNG', 10, y, 15, 15);
    } catch (e) {
      console.warn("Failed to add formation sign 1", e);
    }
  }
  if (fmn2) {
    try {
      doc.addImage(fmn2, 'PNG', W - 25, y, 15, 15);
    } catch (e) {
      console.warn("Failed to add formation sign 2", e);
    }
  }
  
  y = addHeader(
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
    ["Org (Cat I)", `${lf.org_cat_i?.days || 0} days × ₹${lf.org_cat_i?.rate || 30}`, fmtINR((lf.org_cat_i?.total || 0), 2)],
    ["Org (Cat II)", `${lf.org_cat_ii?.days || 0} days × ₹${lf.org_cat_ii?.rate || 15}`, fmtINR((lf.org_cat_ii?.total || 0), 2)],
    ["Non-Org", `${lf.non_org?.days || 0} days × ₹${lf.non_org?.rate || 30}`, fmtINR((lf.non_org?.total || 0), 2)],
    ["TOTAL LICENSE FEE", "", fmtINR((data.total_license_fee || 0), 2)],
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
    ["Org (Cat I)", `${data.org_cat_i_days || 0} days × ₹${r.cat_i_room_rent || 470} (room rent)`, fmtINR(((data.org_cat_i_days || 0) * (r.cat_i_room_rent || 470)), 2)],
    ["Org (Cat II)", `${data.org_cat_ii_days || 0} days × ₹${r.cat_ii_room_rent || 385} (room rent)`, fmtINR(((data.org_cat_ii_days || 0) * (r.cat_ii_room_rent || 385)), 2)],
    ["Non-Org", `${data.non_org_days || 0} days × ₹${r.non_org_room_rent || 570} (room rent)`, fmtINR(((data.non_org_days || 0) * (r.non_org_room_rent || 570)), 2)],
    ["Room Rent Sub-Total", "", fmtINR((data.room_rent_total || 0), 2)],
    ["License Fee Total", "", fmtINR((data.total_license_fee || 0), 2)],
    ["Extra Beds", `${data.extra_beds_total || 0} bed-nights × ₹75`, fmtINR((data.extra_bed_amount || 0), 2)],
    ["GRAND TOTAL", "", fmtINR((data.grand_total || 0), 2)],
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
    ["Advance Received", fmtINR((data.advance_received || 0), 2)],
    ["Advance Adjusted in Bills", fmtINR((data.advance_adjusted || 0), 2)],
    ["Balance Advance", fmtINR((data.balance_advance || 0), 2)],
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
  
  // Save and return blob URL
  const filename = `ECSAG_monthly_report_${data.month_name}_${data.year}.pdf`;
  const pdfBlob = doc.output('blob');
  const blobUrl = URL.createObjectURL(pdfBlob);
  
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  link.click();
  
  return { blobUrl, filename };
}


// ===== BOOKING SLIP (REQUISITION FOR ACCN IN ECSAG) =====
// Generates requisition form slips - 3 per A4 page
export function generateBookingSlips(bookings) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageWidth = 210; // A4 width in mm
  const slipHeight = 99; // A4 height (297mm) / 3 = 99mm per slip
  
  bookings.forEach((booking, index) => {
    // Add new page if not first slip and index is multiple of 3
    if (index > 0 && index % 3 === 0) {
      doc.addPage();
    }
    
    // Calculate Y position for this slip (0, 99, or 198)
    const startY = (index % 3) * slipHeight;
    
    // Draw border around slip
    doc.setDrawColor(0, 0, 0);
    doc.setLineWidth(0.3);
    doc.rect(5, startY + 3, pageWidth - 10, slipHeight - 6);
    
    // Header
    doc.setFontSize(12);
    doc.setFont("helvetica", "bold");
    doc.text("REQUISITION FOR ACCN IN ECSAG (JCO/OR)", pageWidth / 2, startY + 10, { align: "center" });
    
    // Calculate nights
    const checkIn = new Date(booking.check_in_date);
    const checkOut = new Date(booking.check_out_date);
    const nights = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
    
    // Form fields - Left column
    let y = startY + 18;
    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    
    // Serial Number
    doc.text("SER NO:", 10, y);
    doc.text((index + 1).toString(), 30, y);
    
    // NO (Army Number) - BLANK
    y += 6;
    doc.text("NO:", 10, y);
    doc.line(30, y, 100, y); // Blank line for manual entry
    
    // Rank - BLANK
    y += 6;
    doc.text("RANK:", 10, y);
    doc.line(30, y, 100, y); // Blank line for manual entry
    
    // Name
    y += 6;
    doc.text("NAME:", 10, y);
    doc.setFont("helvetica", "bold");
    doc.text((booking.guest_name || "").toUpperCase(), 30, y);
    doc.setFont("helvetica", "normal");
    
    // Unit - BLANK
    y += 6;
    doc.text("UNIT:", 10, y);
    doc.line(30, y, 100, y); // Blank line for manual entry
    
    // Right column
    y = startY + 18;
    
    // Number of Days
    doc.text("NO OF DAYS:", 110, y);
    doc.text(nights.toString(), 145, y);
    
    // Number of Rooms
    y += 6;
    doc.text("NO OF ROOM:", 110, y);
    doc.text((booking.num_rooms || 1).toString(), 145, y);
    
    // Room Number - Updated to handle segmented bookings
    y += 6;
    doc.text("ROOM NO:", 110, y);
    if (booking.has_room_changes && booking.room_segments) {
      // For segmented bookings, show "See below" and add details later
      doc.setFontSize(8);
      doc.text("(See room schedule below)", 145, y);
      doc.setFontSize(9);
    } else {
      doc.text((booking.room_numbers || []).join(", "), 145, y);
    }
    
    // From Date
    y += 6;
    doc.text("FROM:", 110, y);
    doc.text(format(checkIn, "dd/MM/yyyy"), 145, y);
    
    // To Date
    y += 6;
    doc.text("TO:", 110, y);
    doc.text(format(checkOut, "dd/MM/yyyy"), 145, y);
    
    // Full width fields
    y += 8;
    
    // I-Card Number - BLANK
    doc.text("ICARD NO:", 10, y);
    doc.line(40, y, 100, y); // Blank line for manual entry
    
    // Mobile Number
    doc.text("MOBILE NO:", 110, y);
    doc.text(booking.guest_contact || "N/A", 145, y);
    
    // Date
    y += 6;
    doc.text("DATE:", 10, y);
    doc.text(format(new Date(booking.created_at || new Date()), "dd/MM/yyyy"), 40, y);
    
    // Contact Address
    y += 6;
    doc.text("CONTACT ADDRESS:", 10, y);
    doc.text(booking.guest_address || "N/A", 45, y, { maxWidth: 150 });
    
    // ID Card No / Aadhar Card No - BLANK
    y += 6;
    doc.text("ID CARD NO/AADHAR CARD NO:", 10, y);
    doc.line(70, y, 200, y); // Blank line for manual entry
    
    // ID Card Issued By - BLANK
    y += 6;
    doc.text("ID CARD ISSUED BY:", 10, y);
    doc.line(55, y, 200, y); // Blank line for manual entry
    
    // Room Schedule for segmented bookings
    if (booking.has_room_changes && booking.room_segments && booking.room_segments.length > 0) {
      y += 8;
      doc.setFontSize(8);
      doc.setFont("helvetica", "bold");
      doc.text("ROOM SCHEDULE (Guest changes rooms during stay):", 10, y);
      doc.setFont("helvetica", "normal");
      y += 4;
      
      // Create compact schedule
      booking.room_segments.forEach((segment, idx) => {
        const nightDate = format(new Date(segment.night_date), "dd MMM");
        const roomNums = segment.rooms.map(r => r.room_number).join(", ");
        
        if (idx % 2 === 0) {
          // Left column
          doc.text(`${nightDate}: ${roomNums}`, 10, y);
        } else {
          // Right column
          doc.text(`${nightDate}: ${roomNums}`, 110, y);
          y += 4;
        }
      });
      
      // Add spacing if odd number of segments
      if (booking.room_segments.length % 2 !== 0) {
        y += 4;
      }
      
      doc.setFontSize(9);
    }
    
    // Signature section
    y += 10;
    const sigWidth = 45;
    
    doc.setFontSize(8);
    doc.text("SIG OF INDL", 15, y);
    doc.line(10, y + 2, 10 + sigWidth, y + 2);
    
    doc.text("NCO/IC", 65, y);
    doc.line(60, y + 2, 60 + sigWidth, y + 2);
    
    doc.text("Signature", 115, y);
    doc.line(110, y + 2, 110 + sigWidth, y + 2);
    
    doc.text("OIC", 165, y);
    doc.line(160, y + 2, 160 + sigWidth, y + 2);
    
    // Dotted line separator between slips (except for last slip on page)
    if ((index + 1) % 3 !== 0 && index < bookings.length - 1) {
      doc.setLineDash([2, 2]);
      doc.line(10, startY + slipHeight - 3, pageWidth - 10, startY + slipHeight - 3);
      doc.setLineDash([]);
    }
  });
  
  // Save the PDF and return blob for opening
  const timestamp = format(new Date(), "yyyyMMdd_HHmmss");
  const filename = `ECSAG_booking_slips_${timestamp}.pdf`;
  
  // Get the PDF as a blob
  const pdfBlob = doc.output('blob');
  const blobUrl = URL.createObjectURL(pdfBlob);
  
  // Trigger download
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  link.click();
  
  // Return blob URL for opening in new tab
  return { blobUrl, filename, count: bookings.length };
}

// ===== ROOM OCCUPANCY REPORT PDF =====
export function generateRoomOccupancyPDF(data, settings) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const W = doc.internal.pageSize.width;
  
  // Add formation signs if available
  const fmn1 = settings?.fmn_sign_1_url;
  const fmn2 = settings?.fmn_sign_2_url;
  
  let y = 5;
  
  // Add formation signs at top corners
  if (fmn1) {
    try {
      doc.addImage(fmn1, 'PNG', 10, y, 15, 15);
    } catch (e) {
      console.warn("Failed to add formation sign 1", e);
    }
  }
  if (fmn2) {
    try {
      doc.addImage(fmn2, 'PNG', W - 25, y, 15, 15);
    } catch (e) {
      console.warn("Failed to add formation sign 2", e);
    }
  }
  
  y = addHeader(
    doc,
    `ROOM OCCUPANCY REPORT`,
    data.period_label?.toUpperCase()
  );
  y += 5;

  // Summary section
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("SUMMARY", 10, y);
  y += 4;

  const summaryRows = [
    ["Total Rooms", data.total_rooms || 0],
    ["Total Days in Period", data.total_days || 0],
    ["Total Occupied Room-Days", data.total_occupied_days || 0],
    ["Average Occupancy", `${data.avg_occupancy || 0}%`],
    ["Total Bookings", data.total_bookings || 0],
    ["Total Revenue", fmtINR((data.total_revenue || 0), 2)],
  ];

  autoTable(doc, {
    startY: y,
    head: [["Metric", "Value"]],
    body: summaryRows,
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: [70, 100, 180], textColor: 255 },
    alternateRowStyles: { fillColor: LIGHT_GRAY },
    columnStyles: { 1: { halign: "right", fontStyle: "bold" } },
    margin: { left: 10, right: 10 }
  });

  y = doc.lastAutoTable.finalY + 8;

  // Room-wise details with expanded booking information
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("ROOM-WISE OCCUPANCY DETAILS", 10, y);
  y += 4;

  // Iterate through each room and show summary + booking details
  for (const room of (data.room_details || [])) {
    // Check if we need a new page
    if (y > doc.internal.pageSize.height - 40) {
      doc.addPage();
      y = 20;
    }

    // Room summary row
    const roomSummaryRow = [[
      room.room_number,
      room.category,
      room.occupied_days,
      room.available_days,
      `${room.occupancy_percent}%`,
      fmtINR(room.revenue, 2)
    ]];

    autoTable(doc, {
      startY: y,
      head: [["Room No", "Category", "Occupied Days", "Available Days", "Occupancy %", "Revenue (₹)"]],
      body: roomSummaryRow,
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: PRIMARY_COLOR, textColor: 255 },
      bodyStyles: { fillColor: [240, 240, 255], fontStyle: 'bold' },
      columnStyles: { 
        2: { halign: "center" }, 
        3: { halign: "center" }, 
        4: { halign: "center" },
        5: { halign: "right", fontStyle: "bold" }
      },
      margin: { left: 10, right: 10 }
    });

    y = doc.lastAutoTable.finalY + 2;

    // If this room has booking details, show them
    if (room.bookings_detail && room.bookings_detail.length > 0) {
      const bookingRows = room.bookings_detail.map(b => [
        b.booking_number,
        b.army_number,
        b.rank,
        b.name,
        b.unit,
        b.from_date,
        b.to_date,
        b.days,
        b.total_members,
        fmtINR(b.rate_per_day, 0),
        fmtINR(b.total_revenue_due, 2),
        b.bill_no,
        fmtINR(b.advance_paid, 2),
        fmtINR(b.final_amount_paid, 2)
      ]);

      autoTable(doc, {
        startY: y,
        head: [["Booking", "Army No", "Rank", "Name", "Unit", "From", "To", "Days", "Members", "Rate/Day", "Revenue", "Bill", "Advance", "Final"]],
        body: bookingRows,
        styles: { fontSize: 6, cellPadding: 1.5 },
        headStyles: { fillColor: [100, 120, 200], textColor: 255 },
        alternateRowStyles: { fillColor: [245, 247, 255] },
        columnStyles: { 
          7: { halign: "center" },
          8: { halign: "center", fontStyle: "bold", textColor: [0, 0, 255] },
          9: { halign: "right" },
          10: { halign: "right", fontStyle: "bold", textColor: [0, 128, 0] },
          12: { halign: "right" },
          13: { halign: "right" }
        },
        margin: { left: 15, right: 10 }
      });

      y = doc.lastAutoTable.finalY + 6;
    } else {
      y += 3;
    }
  }

  addFooter(doc);
  
  const filename = `ECSAG_room_occupancy_${data.period_label.replace(/\s+/g, '_')}.pdf`;
  const pdfBlob = doc.output('blob');
  const blobUrl = URL.createObjectURL(pdfBlob);
  
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  link.click();
  
  return { blobUrl, filename };
}

// ===== ROOM ALLOTMENT REPORT PDF =====
export function generateRoomAllotmentPDF(data, settings) {
  const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" });
  const W = doc.internal.pageSize.width;
  
  // Add formation signs if available
  const fmn1 = settings?.fmn_sign_1_url;
  const fmn2 = settings?.fmn_sign_2_url;
  
  let y = 5;
  
  if (fmn1) {
    try {
      doc.addImage(fmn1, 'PNG', 10, y, 15, 15);
    } catch (e) {
      console.warn("Failed to add formation sign 1", e);
    }
  }
  if (fmn2) {
    try {
      doc.addImage(fmn2, 'PNG', W - 25, y, 15, 15);
    } catch (e) {
      console.warn("Failed to add formation sign 2", e);
    }
  }
  
  y = addHeader(
    doc,
    `ROOM ALLOTMENT REPORT`,
    data.period_label?.toUpperCase()
  );
  y += 5;

  const allotRows = (data.allotments || []).map((a, idx) => [
    idx + 1,
    a.booking_number,
    a.army_number,
    a.guest_rank,
    a.guest_name,
    a.guest_unit,
    a.self_count,
    a.wife_count,
    a.child_count,
    a.check_in_date,
    a.check_out_date,
    a.nights,
    a.dependents,
    a.non_dependents,
    (a.room_numbers || []).join(", "),
    a.mobile_no,
    fmtINR(a.total_amount, 2)
  ]);

  autoTable(doc, {
    startY: y,
    head: [["S.No", "Booking", "Army No", "Rank", "Name", "Unit", "Self", "Wife", "Child", "In", "Out", "Nights", "Dep", "Non-Dep", "Room", "Mobile", "Amount"]],
    body: allotRows,
    styles: { fontSize: 6, cellPadding: 1.5 },
    headStyles: { fillColor: [120, 80, 160], textColor: 255 },
    alternateRowStyles: { fillColor: LIGHT_GRAY },
    columnStyles: { 
      0: { halign: "center" },
      6: { halign: "center", fontStyle: "bold" },
      7: { halign: "center", fontStyle: "bold" },
      8: { halign: "center", fontStyle: "bold" },
      11: { halign: "center" },
      12: { halign: "center", textColor: [34, 139, 34], fontStyle: "bold" },
      13: { halign: "center", textColor: [255, 140, 0], fontStyle: "bold" },
      16: { halign: "right", fontStyle: "bold" }
    },
    margin: { left: 10, right: 10 }
  });

  addFooter(doc);
  
  const filename = `ECSAG_room_allotment_${data.period_label.replace(/\s+/g, '_')}.pdf`;
  const pdfBlob = doc.output('blob');
  const blobUrl = URL.createObjectURL(pdfBlob);
  
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  link.click();
  
  return { blobUrl, filename };
}

// ===== GUEST DETAILS REPORT PDF =====
export function generateGuestDetailsPDF(data, settings) {
  const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" });
  const W = doc.internal.pageSize.width;
  
  // Add formation signs if available
  const fmn1 = settings?.fmn_sign_1_url;
  const fmn2 = settings?.fmn_sign_2_url;
  
  let y = 5;
  
  if (fmn1) {
    try {
      doc.addImage(fmn1, 'PNG', 10, y, 15, 15);
    } catch (e) {
      console.warn("Failed to add formation sign 1", e);
    }
  }
  if (fmn2) {
    try {
      doc.addImage(fmn2, 'PNG', W - 25, y, 15, 15);
    } catch (e) {
      console.warn("Failed to add formation sign 2", e);
    }
  }
  
  y = addHeader(
    doc,
    `GUEST DETAILS REPORT`,
    data.period_label?.toUpperCase()
  );
  y += 5;

  // Summary
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text(`Total Party Members: ${data.total_party_members || 0}  |  Total Bookings: ${data.total_bookings || 0}  |  Total Nights: ${data.total_nights || 0}  |  Revenue: ${fmtINR(data.total_revenue || 0, 2)}`, 10, y);
  y += 6;

  const guestRows = (data.guest_party_members || []).map(g => [
    g.booking_number,
    g.room_numbers,
    g.rank,
    g.name,
    g.age,
    g.sex,
    g.relationship,
    g.mobile_no,
    typeof g.total_amount === 'number' ? fmtINR(g.total_amount, 2) : g.total_amount
  ]);

  autoTable(doc, {
    startY: y,
    head: [["Booking", "Room", "Rank", "Name", "Age", "Sex", "Relation", "Mobile", "Amount (₹)"]],
    body: guestRows,
    styles: { fontSize: 6, cellPadding: 1.5 },
    headStyles: { fillColor: [60, 140, 130], textColor: 255 },
    alternateRowStyles: { fillColor: LIGHT_GRAY },
    columnStyles: { 
      4: { halign: "center" },
      5: { halign: "center" },
      8: { halign: "right", fontStyle: "bold" }
    },
    margin: { left: 10, right: 10 },
    didParseCell: function (data) {
      // Highlight main guest rows (Self)
      if (data.section === 'body' && guestRows[data.row.index] && guestRows[data.row.index][6] === 'Self') {
        data.cell.styles.fillColor = [219, 234, 254]; // Light blue for main guests
        data.cell.styles.fontStyle = 'bold';
      }
    }
  });

  addFooter(doc);
  
  const filename = `ECSAG_guest_details_${data.period_label.replace(/\s+/g, '_')}.pdf`;
  const pdfBlob = doc.output('blob');
  const blobUrl = URL.createObjectURL(pdfBlob);
  
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  link.click();
  
  return { blobUrl, filename };
}




/**
 * Generate Org Data Form - Blank form for manual pen-filling of sensitive data
 * This form is generated at check-in for Organization guests
 * Contains fields: Rank, Service Number, Unit, Command
 * To be filled manually with pen and kept as physical record only
 */
export function generateOrgDataForm(booking) {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.width;
  const pageHeight = doc.internal.pageSize.height;
  let y = 15;

  // Header
  doc.setFillColor(31, 78, 121);
  doc.rect(0, 0, pageWidth, 20, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text("SARAI", pageWidth / 2, 10, { align: "center" });
  doc.setFontSize(8);
  doc.setFont("helvetica", "normal");
  doc.text("Shillong Aramgah Room Automation Interface", pageWidth / 2, 15, { align: "center" });
  doc.setTextColor(0, 0, 0);
  
  y = 28;

  // Title
  doc.setFillColor(220, 230, 241);
  doc.rect(10, y, pageWidth - 20, 10, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.text("ORGANIZATION GUEST DATA FORM", pageWidth / 2, y + 7, { align: "center" });

  y += 14;

  // Warning - Compact
  doc.setFontSize(8);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(200, 0, 0);
  doc.text("⚠️ CONFIDENTIAL - FOR MANUAL RECORD KEEPING ONLY", pageWidth / 2, y, { align: "center" });
  doc.setFontSize(7);
  doc.setFont("helvetica", "normal");
  y += 4;
  doc.text("Please fill with pen. This form will be kept in physical records. Do not digitize.", pageWidth / 2, y, { align: "center" });
  doc.setTextColor(0, 0, 0);

  y += 8;

  // Booking Information - Compact
  doc.setFillColor(245, 245, 245);
  doc.rect(10, y, pageWidth - 20, 24, "F");
  doc.setDrawColor(200, 200, 200);
  doc.rect(10, y, pageWidth - 20, 24);
  
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("BOOKING INFORMATION", 15, y + 5);
  
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.text(`Booking: ${booking.booking_number}`, 15, y + 10);
  doc.text(`Guest: ${booking.guest_name}`, 15, y + 15);
  doc.text(`Mobile: ${booking.guest_contact || "—"}`, 15, y + 20);
  
  // Room display - handle both traditional and segmented bookings
  if (booking.has_room_changes && booking.room_segments) {
    const uniqueRooms = [...new Set(booking.room_segments.flatMap(s => s.rooms.map(r => r.room_number)))];
    doc.text(`Room(s): ${uniqueRooms.join(", ")} (varies)`, pageWidth / 2 + 5, y + 10);
  } else {
    doc.text(`Room(s): ${(booking.room_numbers || []).join(", ")}`, pageWidth / 2 + 5, y + 10);
  }
  doc.text(`Check-in: ${format(new Date(booking.check_in_date), "dd MMM yyyy")}`, pageWidth / 2 + 5, y + 15);
  doc.text(`Color: ${booking.org_color || "Not assigned"}`, pageWidth / 2 + 5, y + 20);

  y += 30;

  // Main Guest Sensitive Data
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10);
  doc.text("MAIN GUEST SENSITIVE DATA (Fill with pen)", 15, y);
  
  y += 6;

  const fieldHeight = 12;
  const fieldWidth = pageWidth - 20;

  // Compact fields with smaller spacing
  const sensitiveFields = [
    { label: "Identity Card No:", hint: "(Aadhaar / Voter ID / Driving License)" },
    { label: "Rank:", hint: "(e.g., Sep, Nk, Hav, Sub, WO)" },
    { label: "Service Number:", hint: "(e.g., IC-12345, 15814432-F)" },
    { label: "Unit:", hint: "(e.g., 2 PARA, 14 Rajput)" },
    { label: "Command HQ:", hint: "(e.g., Eastern Command, Northern)" }
  ];

  sensitiveFields.forEach(field => {
    doc.setFillColor(255, 255, 255);
    doc.rect(10, y, fieldWidth, fieldHeight);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8);
    doc.text(field.label, 13, y + 5);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7);
    doc.setTextColor(120, 120, 120);
    doc.text(field.hint, 13, y + 9);
    doc.setTextColor(0, 0, 0);
    y += fieldHeight + 2;
  });

  y += 4;

  // Family Members with Org Cards Section - REDESIGNED for 4+ members
  const familyWithOrgCards = (booking.family_members || []).filter(fm => fm.has_org_card);
  
  if (familyWithOrgCards.length > 0) {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10);
    doc.text("FAMILY MEMBERS WITH ORG DEPENDENT CARD", 15, y);
    y += 6;

    // Compact grid layout - 2 columns for space efficiency
    const memberBoxWidth = (pageWidth - 25) / 2;
    const memberBoxHeight = 32;
    let col = 0;

    familyWithOrgCards.forEach((member, idx) => {
      // Check if we need a new page
      if (y > pageHeight - 50) {
        doc.addPage();
        y = 20;
        col = 0;
      }

      const xOffset = col === 0 ? 10 : 10 + memberBoxWidth + 5;

      // Member box
      doc.setFillColor(250, 250, 250);
      doc.rect(xOffset, y, memberBoxWidth, memberBoxHeight, "F");
      doc.setDrawColor(150, 150, 150);
      doc.rect(xOffset, y, memberBoxWidth, memberBoxHeight);

      doc.setFont("helvetica", "bold");
      doc.setFontSize(8);
      doc.text(`Member ${idx + 1}:`, xOffset + 3, y + 5);
      
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7);
      doc.text(`Name: ${member.name || "—"}`, xOffset + 3, y + 10);
      doc.text(`Rel: ${member.relation || "—"}`, xOffset + 3, y + 14);
      doc.text(`Age: ${member.age || "—"} | ${member.sex || "—"}`, xOffset + 3, y + 18);

      // Blank field for Org Dep ID
      doc.setFont("helvetica", "bold");
      doc.setFontSize(7);
      doc.text("Org Dep ID:", xOffset + 3, y + 24);
      doc.setFont("helvetica", "normal");
      doc.line(xOffset + 3, y + 28, xOffset + memberBoxWidth - 3, y + 28);

      // Move to next column or row
      if (col === 0) {
        col = 1;
      } else {
        col = 0;
        y += memberBoxHeight + 3;
      }
    });

    // Move to next row if we ended on column 1
    if (col === 1) {
      y += memberBoxHeight + 3;
    }

    y += 4;
  }

  // Signature section - compact
  doc.setDrawColor(0, 0, 0);
  doc.line(15, y + 10, 80, y + 10);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(7);
  doc.text("Guest Signature", 15, y + 14);
  doc.text("Date: ___________", 15, y + 18);

  doc.line(pageWidth - 80, y + 10, pageWidth - 15, y + 10);
  doc.text("Staff Signature", pageWidth - 80, y + 14);
  doc.text("Date: ___________", pageWidth - 80, y + 18);

  // Footer warning - FIXED positioning
  const footerY = pageHeight - 15;
  doc.setFillColor(255, 240, 240);
  doc.rect(10, footerY, pageWidth - 20, 10, "F");
  doc.setDrawColor(200, 0, 0);
  doc.rect(10, footerY, pageWidth - 20, 10);
  doc.setTextColor(200, 0, 0);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(7);
  doc.text("⚠️ IMPORTANT: Store in physical records only. Do not digitize or scan.", pageWidth / 2, footerY + 4, { align: "center" });
  doc.text("This information is confidential and must not be entered into any digital system.", pageWidth / 2, footerY + 8, { align: "center" });

  // Save
  const filename = `ORG_DATA_${booking.booking_number}_${format(new Date(), "yyyyMMdd")}.pdf`;
  doc.save(filename);
  
  return filename;
}

// ===== TOILETRY TRANSACTIONS REPORT PDF =====
export function generateToiletryReportPDF(transactions, items, fromDate, toDate, summaryOnly = false) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const W = doc.internal.pageSize.width;

  const dateRange = fromDate && toDate
    ? `${format(new Date(fromDate), "dd MMM yyyy")} – ${format(new Date(toDate), "dd MMM yyyy")}`
    : fromDate ? `From ${format(new Date(fromDate), "dd MMM yyyy")}`
    : toDate ? `Up to ${format(new Date(toDate), "dd MMM yyyy")}`
    : "All Transactions";

  let y = addHeader(doc, "TOILETRY STOCK REPORT", dateRange);
  y += 4;

  // Per-item summary (same logic as computeItemSummary in Toiletry.jsx)
  const itemSummaries = (items || []).map(item => {
    const itemTxns = transactions.filter(t => t.item_id === item.id);
    const stockIn = itemTxns.filter(t => t.transaction_type === "stock_in").reduce((s, t) => s + t.quantity, 0);
    const consumed = itemTxns.filter(t => t.transaction_type === "consumption").reduce((s, t) => s + t.quantity, 0);
    const netChange = stockIn - consumed;
    const initialStock = item.quantity - netChange;
    return {
      name: item.name,
      initialStock,
      stockIn,
      consumed,
      finalBalance: item.quantity,
    };
  });

  // Totals strip
  const totalStockIn = itemSummaries.reduce((s, i) => s + i.stockIn, 0);
  const totalConsumed = itemSummaries.reduce((s, i) => s + i.consumed, 0);
  const totalBalance = itemSummaries.reduce((s, i) => s + i.finalBalance, 0);

  doc.setFontSize(9);
  doc.setFont("helvetica", "bold");
  doc.setFillColor(240, 248, 255);
  doc.rect(10, y, W - 20, 12, "F");
  doc.text(`Stock Added: ${totalStockIn}`, 14, y + 5);
  doc.text(`Kits Issued: ${totalConsumed}`, 80, y + 5);
  doc.text(`Current Balance: ${totalBalance}`, 148, y + 5);
  doc.setFont("helvetica", "normal");
  y += 16;

  // Per-item summary table
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("ITEM-WISE SUMMARY", 10, y);
  y += 4;

  autoTable(doc, {
    startY: y,
    head: [["Item", "Opening Stock", "Stock Added", "Kits Issued", "Closing Balance"]],
    body: itemSummaries.map(i => [
      i.name,
      i.initialStock,
      i.stockIn,
      i.consumed,
      i.finalBalance,
    ]),
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: PRIMARY_COLOR, textColor: 255, fontStyle: "bold" },
    alternateRowStyles: { fillColor: [248, 249, 250] },
    columnStyles: {
      0: { cellWidth: "auto" },
      1: { cellWidth: 30, halign: "center" },
      2: { cellWidth: 30, halign: "center" },
      3: { cellWidth: 28, halign: "center" },
      4: { cellWidth: 35, halign: "center", fontStyle: "bold" },
    },
    margin: { left: 10, right: 10 },
  });

  y = doc.lastAutoTable.finalY + 6;

  // Note about opening stock calculation
  doc.setFontSize(7);
  doc.setTextColor(120, 120, 120);
  doc.text("* Opening Stock = Current Stock − (Stock Added − Kits Issued) within the selected date range.", 10, y);
  doc.setTextColor(0, 0, 0);
  y += 6;

  if (!summaryOnly && transactions.length > 0) {
    // Transaction detail table
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.text("TRANSACTION DETAILS", 10, y);
    y += 4;

    autoTable(doc, {
      startY: y,
      head: [["Date", "Item", "Type", "Qty", "Room / Booking", "Notes"]],
      body: transactions.map(t => [
        format(new Date(t.created_at), "dd/MM/yyyy HH:mm"),
        t.item_name,
        t.transaction_type === "stock_in" ? "Stock In" : "Consumed",
        t.quantity,
        [t.room_number, t.booking_id ? `BK#${t.booking_id.slice(0, 8)}` : ""].filter(Boolean).join(" / ") || "—",
        t.notes || "—",
      ]),
      styles: { fontSize: 7, cellPadding: 2 },
      headStyles: { fillColor: [80, 120, 160], textColor: 255, fontStyle: "bold" },
      alternateRowStyles: { fillColor: [248, 249, 250] },
      columnStyles: {
        0: { cellWidth: 32 },
        1: { cellWidth: 32 },
        2: { cellWidth: 22 },
        3: { cellWidth: 12, halign: "center" },
        4: { cellWidth: 38 },
        5: { cellWidth: "auto" },
      },
      margin: { left: 10, right: 10 },
    });
  }

  addFooter(doc);

  const filename = `toiletry_report_${format(new Date(), "yyyyMMdd_HHmm")}.pdf`;
  const pdfBlob = doc.output("blob");
  const blobUrl = URL.createObjectURL(pdfBlob);
  return { blobUrl, filename };
}
