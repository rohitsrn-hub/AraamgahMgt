import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { FilePdf, Bed, CaretDown, CaretRight } from "@phosphor-icons/react";
import { generateRoomOccupancyPDF } from "@/utils/pdfUtils";
import { fmtINR } from "@/utils/formatters";

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

export default function RoomOccupancyTab({ settings }) {
  const [filterType, setFilterType] = useState("monthly");
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedRooms, setExpandedRooms] = useState({}); // Track expanded rooms

  const years = [];
  for (let y = 2024; y <= new Date().getFullYear() + 1; y++) years.push(y);

  const toggleRoomExpand = (roomNumber) => {
    setExpandedRooms(prev => ({
      ...prev,
      [roomNumber]: !prev[roomNumber]
    }));
  };

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
      
      const res = await axios.get(`${API}/reports/room-occupancy`, { params });
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
    generateRoomOccupancyPDF(report, settings);
    toast.success("PDF generated!");
  };

  return (
    <div className="space-y-6">
      {/* Header & Filters */}
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Room Occupancy Report</h2>
          <p className="text-sm text-slate-500 mt-1">Detailed room-wise occupancy analysis</p>
        </div>
        
        {/* Filter Controls */}
        <Card className="bg-indigo-50/50 border-indigo-200">
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600">Total Rooms</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-indigo-600">{report.total_rooms || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600">Average Occupancy</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-emerald-600">{report.avg_occupancy || 0}%</div>
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
          </div>

          {/* Room-wise Occupancy Table */}
          <Card className="earms-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bed size={22} className="text-indigo-500" weight="fill" />
                Room-wise Occupancy Details — {report.period_label}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th className="w-12"></th>
                      <th>Room No</th>
                      <th>Category</th>
                      <th className="text-center">Occupied Days</th>
                      <th className="text-center">Available Days</th>
                      <th className="text-center">Occupancy %</th>
                      <th className="text-right">Revenue (₹)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(report.room_details || []).map((room) => (
                      <>
                        <tr key={room.room_number} className={expandedRooms[room.room_number] ? "bg-indigo-50" : ""}>
                          <td className="text-center">
                            {room.bookings_detail && room.bookings_detail.length > 0 && (
                              <button
                                onClick={() => toggleRoomExpand(room.room_number)}
                                className="p-1 hover:bg-indigo-100 rounded"
                                title={expandedRooms[room.room_number] ? "Collapse" : "Expand bookings"}
                              >
                                {expandedRooms[room.room_number] ? (
                                  <CaretDown size={18} weight="bold" className="text-indigo-600" />
                                ) : (
                                  <CaretRight size={18} weight="bold" className="text-slate-500" />
                                )}
                              </button>
                            )}
                          </td>
                          <td className="font-medium">{room.room_number}</td>
                          <td>{room.category}</td>
                          <td className="text-center">{room.occupied_days}</td>
                          <td className="text-center">{room.available_days}</td>
                          <td className="text-center">
                            <span className={`font-semibold ${
                              room.occupancy_percent >= 75 ? 'text-emerald-600' :
                              room.occupancy_percent >= 50 ? 'text-amber-600' :
                              'text-slate-600'
                            }`}>
                              {room.occupancy_percent}%
                            </span>
                          </td>
                          <td className="text-right font-semibold">{fmtINR(room.revenue || 0, 2)}</td>
                        </tr>
                        
                        {/* Expandable Booking Details */}
                        {expandedRooms[room.room_number] && room.bookings_detail && room.bookings_detail.length > 0 && (
                          <tr key={`${room.room_number}-details`}>
                            <td colSpan="7" className="p-0 bg-indigo-50/50">
                              <div className="px-6 py-4">
                                <h4 className="text-sm font-bold text-indigo-900 mb-3">Booking Details for {room.room_number}</h4>
                                <div className="bg-white rounded-lg border border-indigo-200 overflow-hidden">
                                  <table className="w-full text-sm">
                                    <thead className="bg-indigo-100">
                                      <tr>
                                        <th className="text-left p-2 font-semibold">Booking No</th>
                                        <th className="text-left p-2 font-semibold">Name</th>
                                        <th className="text-left p-2 font-semibold">Type</th>
                                        <th className="text-left p-2 font-semibold">Color</th>
                                        <th className="text-center p-2 font-semibold">From</th>
                                        <th className="text-center p-2 font-semibold">To</th>
                                        <th className="text-center p-2 font-semibold">Days</th>
                                        <th className="text-center p-2 font-semibold">Members</th>
                                        <th className="text-right p-2 font-semibold">Rate/Day</th>
                                        <th className="text-right p-2 font-semibold">Revenue</th>
                                        <th className="text-left p-2 font-semibold">Bill No</th>
                                        <th className="text-right p-2 font-semibold">Advance</th>
                                        <th className="text-right p-2 font-semibold">Final Paid</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {room.bookings_detail.map((booking, idx) => (
                                        <tr key={idx} className="border-t border-indigo-100 hover:bg-indigo-50">
                                          <td className="p-2 font-medium">{booking.booking_number}</td>
                                          <td className="p-2">{booking.name}</td>
                                          <td className="p-2">
                                            <span className={`text-xs px-2 py-0.5 rounded ${booking.is_org ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'}`}>
                                              {booking.is_org ? "Org" : "Non-Org"}
                                            </span>
                                          </td>
                                          <td className="p-2">
                                            {booking.org_color ? (
                                              <span className="text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-700">{booking.org_color}</span>
                                            ) : "—"}
                                          </td>
                                          <td className="p-2 text-center">{booking.from_date}</td>
                                          <td className="p-2 text-center">{booking.to_date}</td>
                                          <td className="p-2 text-center font-semibold">{booking.days}</td>
                                          <td className="p-2 text-center font-semibold text-blue-600">{booking.total_members}</td>
                                          <td className="p-2 text-right">{fmtINR(booking.rate_per_day, 0)}</td>
                                          <td className="p-2 text-right font-bold text-emerald-700">{fmtINR(booking.total_revenue_due, 2)}</td>
                                          <td className="p-2">{booking.bill_no}</td>
                                          <td className="p-2 text-right">{fmtINR(booking.advance_paid, 2)}</td>
                                          <td className="p-2 text-right">{fmtINR(booking.final_amount_paid, 2)}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                    <tr className="font-bold bg-slate-100">
                      <td></td>
                      <td colSpan="2">TOTAL</td>
                      <td className="text-center">{report.total_occupied_days || 0}</td>
                      <td className="text-center">{report.total_available_days || 0}</td>
                      <td className="text-center">{report.avg_occupancy || 0}%</td>
                      <td className="text-right">{fmtINR(report.total_revenue || 0, 2)}</td>
                    </tr>
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
