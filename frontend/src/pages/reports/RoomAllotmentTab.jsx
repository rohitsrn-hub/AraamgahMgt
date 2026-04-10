import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { FilePdf, FileText } from "@phosphor-icons/react";
import { generateRoomAllotmentPDF } from "@/utils/pdfUtils";

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

export default function RoomAllotmentTab({ settings }) {
  const [filterType, setFilterType] = useState("monthly");
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  const years = [];
  for (let y = 2024; y <= new Date().getFullYear() + 1; y++) years.push(y);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const params = { filter_type: filterType };
      
      if (filterType === "daily") {
        const today = new Date().toISOString().split('T')[0];
        params.start_date = today;
        params.end_date = today;
      } else if (filterType === "monthly") {
        params.month = month;
        params.year = year;
      } else if (filterType === "quarterly") {
        params.year = year;
        params.quarter = Math.ceil(month / 3);
      } else if (filterType === "annual") {
        params.year = year;
      } else if (filterType === "custom") {
        if (!customStart || !customEnd) {
          toast.error("Please select both start and end dates");
          setLoading(false);
          return;
        }
        params.start_date = customStart;
        params.end_date = customEnd;
      }
      
      const res = await axios.get(`${API}/reports/room-allotment`, { params });
      setReport(res.data);
    } catch (err) {
      toast.error("Failed to load report");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { 
    fetchReport(); 
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterType, month, year]);

  const handlePrint = () => {
    if (!report) return;
    generateRoomAllotmentPDF(report, settings);
    toast.success("PDF generated!");
  };

  return (
    <div className="space-y-6">
      {/* Header & Filters */}
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Room Allotment Report</h2>
          <p className="text-sm text-slate-500 mt-1">Detailed room allotment and booking history</p>
        </div>
        
        {/* Filter Controls */}
        <Card className="bg-purple-50/50 border-purple-200">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label>Filter Type</Label>
                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                    <SelectItem value="quarterly">Quarterly</SelectItem>
                    <SelectItem value="annual">Annual</SelectItem>
                    <SelectItem value="custom">Custom Range</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {(filterType === "monthly" || filterType === "quarterly") && (
                <div>
                  <Label>Month</Label>
                  <Select value={String(month)} onValueChange={(v) => setMonth(Number(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {MONTHS.map((m, i) => <SelectItem key={i} value={String(i + 1)}>{m}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              )}
              
              {(filterType === "monthly" || filterType === "quarterly" || filterType === "annual") && (
                <div>
                  <Label>Year</Label>
                  <Select value={String(year)} onValueChange={(v) => setYear(Number(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {years.map(y => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              )}
              
              {filterType === "custom" && (
                <>
                  <div>
                    <Label>Start Date</Label>
                    <Input type="date" value={customStart} onChange={(e) => setCustomStart(e.target.value)} />
                  </div>
                  <div>
                    <Label>End Date</Label>
                    <Input type="date" value={customEnd} onChange={(e) => setCustomEnd(e.target.value)} />
                  </div>
                </>
              )}
              
              <div className="flex items-end gap-2">
                <Button onClick={fetchReport} disabled={loading} className="w-full">
                  {loading ? "Loading..." : "Apply"}
                </Button>
                <Button 
                  onClick={handlePrint} 
                  disabled={!report || loading}
                  className="bg-red-600 hover:bg-red-700"
                >
                  <FilePdf size={20} />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Report Data */}
      {loading ? (
        <div className="flex justify-center py-12"><div className="spinner" /></div>
      ) : !report ? null : (
        <Card className="earms-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText size={22} className="text-purple-500" weight="fill" />
              Room Allotments — {report.period_label}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>S.No</th>
                    <th>Booking No</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Color</th>
                    <th className="text-center">Self</th>
                    <th className="text-center">Wife</th>
                    <th className="text-center">Child</th>
                    <th>Check-in</th>
                    <th>Check-out</th>
                    <th className="text-center">Nights</th>
                    <th className="text-center">Org Dep</th>
                    <th className="text-center">Non-Org Dep</th>
                    <th>Room(s)</th>
                    <th>Aadhaar No</th>
                    <th>Mobile No</th>
                    <th className="text-right">Amount (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  {(report.allotments || []).map((allot, idx) => (
                    <tr key={allot.booking_id}>
                      <td className="text-center">{idx + 1}</td>
                      <td className="font-medium">{allot.booking_number}</td>
                      <td>{allot.guest_name}</td>
                      <td>
                        {allot.is_org ? (
                          <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700">Org</span>
                        ) : (
                          <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">Non-Org</span>
                        )}
                      </td>
                      <td>
                        {allot.org_color ? (
                          <span className="text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-700">{allot.org_color}</span>
                        ) : "—"}
                      </td>
                      <td className="text-center font-semibold">{allot.self_count}</td>
                      <td className="text-center font-semibold">{allot.wife_count}</td>
                      <td className="text-center font-semibold">{allot.child_count}</td>
                      <td>{allot.check_in_date}</td>
                      <td>{allot.check_out_date}</td>
                      <td className="text-center">{allot.nights}</td>
                      <td className="text-center text-blue-700 font-semibold">{allot.dependents}</td>
                      <td className="text-center text-orange-700 font-semibold">{allot.non_dependents}</td>
                      <td>{allot.room_numbers?.join(", ") || "N/A"}</td>
                      <td className="text-sm">{allot.aadhaar_no || "—"}</td>
                      <td className="text-sm">{allot.mobile_no}</td>
                      <td className="text-right font-semibold">₹{allot.total_amount?.toFixed(2) || '0.00'}</td>
                    </tr>
                  ))}
                  {report.allotments?.length === 0 && (
                    <tr>
                      <td colSpan="16" className="text-center text-slate-500 py-8">
                        No allotments found for the selected period
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
