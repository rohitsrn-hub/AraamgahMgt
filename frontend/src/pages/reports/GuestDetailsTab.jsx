import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { FilePdf, Users } from "@phosphor-icons/react";
import { generateGuestDetailsPDF } from "@/utils/pdfUtils";

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

export default function GuestDetailsTab({ settings }) {
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
      
      const res = await axios.get(`${API}/reports/guest-details`, { params });
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
    generateGuestDetailsPDF(report, settings);
    toast.success("PDF generated!");
  };

  return (
    <div className="space-y-6">
      {/* Header & Filters */}
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Guest Details Report</h2>
          <p className="text-sm text-slate-500 mt-1">Comprehensive guest information and statistics</p>
        </div>
        
        {/* Filter Controls */}
        <Card className="bg-teal-50/50 border-teal-200">
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
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600">Total Party Members</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-teal-600">{report.total_party_members || 0}</div>
                <p className="text-xs text-slate-500 mt-1">Guests + Companions</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600">Total Bookings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">{report.total_bookings || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600">Total Nights</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-purple-600">{report.total_nights || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600">Revenue (₹)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-emerald-600">₹{report.total_revenue?.toFixed(2) || '0.00'}</div>
              </CardContent>
            </Card>
          </div>

          {/* Guest Details Table */}
          <Card className="earms-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users size={22} className="text-teal-500" weight="fill" />
                Guest Party Details — {report.period_label}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Booking No</th>
                      <th>Room(s)</th>
                      <th>Type</th>
                      <th>Color</th>
                      <th>Name</th>
                      <th>Age</th>
                      <th>Sex</th>
                      <th>Relationship</th>
                      <th>Address</th>
                      <th>Aadhaar No</th>
                      <th>Mobile No</th>
                      <th>Check-in</th>
                      <th>Check-out</th>
                      <th className="text-center">Nights</th>
                      <th className="text-right">Amount (₹)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(report.guest_party_members || []).map((guest, idx) => (
                      <tr key={idx} className={guest.relationship === "Self" ? "bg-blue-50 font-semibold" : ""}>
                        <td className="font-medium">{guest.booking_number}</td>
                        <td>{guest.room_numbers}</td>
                        <td>
                          {guest.is_org ? (
                            <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700">Org</span>
                          ) : guest.is_org === "—" ? "—" : (
                            <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">Non-Org</span>
                          )}
                        </td>
                        <td>
                          {guest.org_color && guest.org_color !== "—" ? (
                            <span className="text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-700">{guest.org_color}</span>
                          ) : "—"}
                        </td>
                        <td>{guest.name}</td>
                        <td className="text-center">{guest.age}</td>
                        <td className="text-center">{guest.sex}</td>
                        <td>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            guest.relationship === 'Self' ? 'bg-blue-100 text-blue-700' :
                            guest.relationship.toLowerCase().includes('w/o') || guest.relationship.toLowerCase().includes('wife') ? 'bg-pink-100 text-pink-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                            {guest.relationship}
                          </span>
                        </td>
                        <td className="text-sm">{guest.address}</td>
                        <td className="text-sm">{guest.aadhaar_no}</td>
                        <td className="text-sm">{guest.mobile_no}</td>
                        <td>{guest.check_in_date}</td>
                        <td>{guest.check_out_date}</td>
                        <td className="text-center">{guest.nights}</td>
                        <td className="text-right font-semibold">
                          {typeof guest.total_amount === 'number' ? `₹${guest.total_amount.toFixed(2)}` : guest.total_amount}
                        </td>
                      </tr>
                    ))}
                    {report.guest_party_members?.length === 0 && (
                      <tr>
                        <td colSpan="15" className="text-center text-slate-500 py-8">
                          No guest records found for the selected period
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
