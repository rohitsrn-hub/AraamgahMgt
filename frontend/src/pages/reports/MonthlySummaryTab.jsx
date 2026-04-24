import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { FilePdf, ChartBar, CurrencyInr, Buildings } from "@phosphor-icons/react";
import { generateMonthlyReportPDF } from "@/utils/pdfUtils";
import { fmtINR } from "@/utils/formatters";

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

export default function MonthlySummaryTab({ settings }) {
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  const years = [];
  for (let y = 2024; y <= new Date().getFullYear() + 1; y++) years.push(y);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/reports/monthly`, { params: { month, year } });
      setReport(res.data);
    } catch (err) {
      toast.error("Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { 
    fetchReport(); 
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [month, year]);

  const handlePrint = () => {
    if (!report) return;
    generateMonthlyReportPDF(report, settings);
    toast.success("PDF generated!");
  };

  return (
    <div className="space-y-6" data-testid="monthly-summary-tab">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Monthly Summary Report</h2>
          <p className="text-sm text-slate-500 mt-1">Occupancy, revenue & license fee summary</p>
        </div>
        <div className="flex gap-2 items-center">
          <Select value={String(month)} onValueChange={(v) => setMonth(Number(v))}>
            <SelectTrigger className="w-36" data-testid="select-month">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MONTHS.map((m, i) => <SelectItem key={i} value={String(i + 1)}>{m}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={String(year)} onValueChange={(v) => setYear(Number(v))}>
            <SelectTrigger className="w-24" data-testid="select-year">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {years.map(y => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button
            onClick={handlePrint}
            disabled={!report || loading}
            className="flex items-center gap-2 bg-red-600 hover:bg-red-700"
            data-testid="print-report-btn"
          >
            <FilePdf size={20} />
            Print PDF
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="spinner" /></div>
      ) : !report ? null : (
        <>
          {/* Colour breakdown */}
          <Card className="earms-card" data-testid="colour-breakdown">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Buildings size={22} className="text-blue-500" weight="fill" />
                Colour-wise Occupancy — {report.month_name} {report.year}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>No</th>
                      <th>Colour</th>
                      <th className="text-center">Total Guests</th>
                      <th className="text-center">No of Days</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(report.command_breakdown || []).map((c, i) => (
                      <tr key={c.command}>
                        <td>{i + 1}</td>
                        <td className="font-medium">{c.command}</td>
                        <td className="text-center">{c.guests}</td>
                        <td className="text-center">{c.days}</td>
                      </tr>
                    ))}
                    <tr className="font-bold bg-slate-100">
                      <td></td>
                      <td>TOTAL</td>
                      <td className="text-center">{report.total_guests}</td>
                      <td className="text-center">{report.total_days}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* License Fee */}
          <Card className="earms-card" data-testid="license-fee-section">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CurrencyInr size={22} className="text-amber-500" weight="fill" />
                License Fee Calculation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { label: "Org (Cat I)", key: "org_cat_i", color: "text-blue-700" },
                  { label: "Org (Cat II)", key: "org_cat_ii", color: "text-purple-700" },
                  { label: "Non-Org", key: "non_org", color: "text-orange-700" }
                ].map(({ label, key, color }) => {
                  const lf = report.license_fees?.[key] || {};
                  return (
                    <div key={key} className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                      <span className={`font-medium ${color}`}>{label}</span>
                      <span className="text-slate-600 text-sm">{lf.days || 0} days × {fmtINR(lf.rate || 0, 0)}</span>
                      <span className="font-bold text-slate-800">{fmtINR((lf.total || 0), 2)}</span>
                    </div>
                  );
                })}
                <div className="flex justify-between items-center p-3 bg-amber-50 border border-amber-200 rounded-lg font-bold">
                  <span>Total License Fee</span>
                  <span>{fmtINR((report.total_license_fee || 0), 2)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Financial Summary */}
          <Card className="earms-card" data-testid="financial-summary">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ChartBar size={22} className="text-emerald-500" weight="fill" />
                Financial Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Row label="Org (Cat I) Room Rent" value={`${report.org_cat_i_days || 0} × ₹${report.rates?.cat_i_room_rent || 470} = ${fmtINR((report.org_cat_i_days || 0) * (report.rates?.cat_i_room_rent || 470), 2)}`} />
                  <Row label="Org (Cat II) Room Rent" value={`${report.org_cat_ii_days || 0} × ₹${report.rates?.cat_ii_room_rent || 385} = ${fmtINR((report.org_cat_ii_days || 0) * (report.rates?.cat_ii_room_rent || 385), 2)}`} />
                  <Row label="Non-Org Room Rent" value={`${report.non_org_days || 0} × ₹${report.rates?.non_org_room_rent || 570} = ${fmtINR((report.non_org_days || 0) * (report.rates?.non_org_room_rent || 570), 2)}`} />
                  <Row label="Room Rent Sub-Total" value={fmtINR((report.room_rent_total || 0), 2)} bold />
                  <Row label="License Fee Total" value={fmtINR((report.total_license_fee || 0), 2)} bold />
                  <Row label="Extra Beds" value={`${report.extra_beds_total || 0} × ₹75 = ${fmtINR(report.extra_bed_amount || 0, 2)}`} />
                  <Row label="GRAND TOTAL" value={fmtINR((report.grand_total || 0), 2)} bold highlight />
                </div>
                <div className="space-y-2">
                  <Row label="Total Rooms" value={report.total_rooms} />
                  <Row label="Days in Month" value={report.days_in_month} />
                  <Row label="Total Booked Room-Days" value={report.total_booked_days || 0} />
                  <Row label="Average Occupancy" value={`${report.avg_occupancy || 0}%`} bold />
                  <Row label="Advance Received" value={fmtINR((report.advance_received || 0), 2)} />
                  <Row label="Advance Adjusted" value={fmtINR((report.advance_adjusted || 0), 2)} />
                  <Row label="Balance Advance" value={fmtINR((report.balance_advance || 0), 2)} bold />
                  <Row label="No-shows (after advance)" value={report.no_shows || 0} />
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function Row({ label, value, bold, highlight }) {
  return (
    <div className={`flex justify-between items-center p-2 rounded ${highlight ? "bg-emerald-50 border border-emerald-200" : "bg-slate-50"}`}>
      <span className={`text-sm ${bold ? "font-bold" : ""} text-slate-700`}>{label}</span>
      <span className={`text-sm ${bold ? "font-bold" : ""} ${highlight ? "text-emerald-800" : "text-slate-800"}`}>{value}</span>
    </div>
  );
}
