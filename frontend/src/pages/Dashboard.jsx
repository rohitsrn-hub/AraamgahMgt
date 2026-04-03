import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { generateCheckoutReceipt } from "@/utils/pdfUtils";
import FeedbackForm from "@/components/FeedbackForm";
import { 
  Bed, 
  CalendarCheck, 
  CurrencyInr, 
  TrendUp,
  Users,
  Warning,
  CheckCircle,
  Clock,
  SignIn,
  SignOut,
  ForkKnife,
  X,
  SpinnerGap,
  CalendarBlank,
  Star,
  ChartBar
} from "@phosphor-icons/react";
import { format, parseISO } from "date-fns";
import { useNavigate } from "react-router-dom";

// Helper to display room numbers from a booking (handles old and new format)
const getRoomDisplay = (booking) => {
  if (booking.room_numbers && booking.room_numbers.length > 0) {
    return booking.room_numbers.join(", ");
  }
  return booking.room_number || "N/A";
};

const getRoomCategories = (booking) => {
  if (booking.room_categories && booking.room_categories.length > 0) {
    const unique = [...new Set(booking.room_categories)];
    return unique.join(", ");
  }
  return booking.room_category || "";
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [occupancy, setOccupancy] = useState(null);
  const [bookings, setBookings] = useState({ today: [], upcoming: [] });
  const [analytics, setAnalytics] = useState(null);
  const [funds, setFunds] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  
  // All bookings for modals
  const [allBookings, setAllBookings] = useState([]);
  const [staff, setStaff] = useState([]);
  const [calendarData, setCalendarData] = useState(null);
  const [showCalendar, setShowCalendar] = useState(false);
  
  // Modal states
  const [showCheckInModal, setShowCheckInModal] = useState(false);
  const [showCheckOutModal, setShowCheckOutModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [pendingCheckoutBooking, setPendingCheckoutBooking] = useState(null);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [refundInfo, setRefundInfo] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedbackAnalysis, setFeedbackAnalysis] = useState(null);
  const [showPendingRefundsModal, setShowPendingRefundsModal] = useState(false);
  const [pendingRefunds, setPendingRefunds] = useState([]);
  const [pendingRefundsLoading, setPendingRefundsLoading] = useState(false);
  
  // Action form
  const [actionForm, setActionForm] = useState({
    staff_id: "",
    notes: "",
    final_payment: 0,
    payment_mode: "",
    reason: "",
    extra_beds: 0
  });

  const fetchDashboardData = async () => {
    try {
      const [occRes, bookRes, analyticsRes, fundsRes, allBookingsRes, staffRes, calRes, fbRes] = await Promise.all([
        axios.get(`${API}/dashboard/occupancy`),
        axios.get(`${API}/dashboard/bookings`),
        axios.get(`${API}/dashboard/analytics?month=${selectedMonth}&year=${selectedYear}`),
        axios.get(`${API}/dashboard/funds?month=${selectedMonth}&year=${selectedYear}`),
        axios.get(`${API}/bookings`),
        axios.get(`${API}/staff`),
        axios.get(`${API}/dashboard/calendar?month=${selectedMonth}&year=${selectedYear}`),
        axios.get(`${API}/feedback/analysis`)
      ]);
      setOccupancy(occRes.data);
      setBookings(bookRes.data);
      setAnalytics(analyticsRes.data);
      setFunds(fundsRes.data);
      setAllBookings(allBookingsRes.data);
      setStaff(staffRes.data);
      setCalendarData(calRes.data);
      setFeedbackAnalysis(fbRes.data);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [selectedMonth, selectedYear]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const months = [
    { value: 1, label: "January" },
    { value: 2, label: "February" },
    { value: 3, label: "March" },
    { value: 4, label: "April" },
    { value: 5, label: "May" },
    { value: 6, label: "June" },
    { value: 7, label: "July" },
    { value: 8, label: "August" },
    { value: 9, label: "September" },
    { value: 10, label: "October" },
    { value: 11, label: "November" },
    { value: 12, label: "December" },
  ];

  // Filter bookings by status
  const confirmedBookings = allBookings.filter(b => b.status === "confirmed");
  const checkedInBookings = allBookings.filter(b => b.status === "checked_in");
  const cancellableBookings = allBookings.filter(b => b.status === "confirmed"); // Only confirmed bookings can be cancelled

  // Handle Check-In
  const handleCheckIn = async () => {
    if (!actionForm.staff_id) {
      toast.error("Please select staff member");
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API}/bookings/check-in`, {
        booking_id: selectedBooking.id,
        staff_id: actionForm.staff_id,
        extra_beds: actionForm.extra_beds,
        notes: actionForm.notes
      });
      toast.success(`${selectedBooking.guest_name} checked in successfully!`);
      setShowCheckInModal(false);
      setSelectedBooking(null);
      setActionForm({ staff_id: "", notes: "", final_payment: 0, payment_mode: "", reason: "", extra_beds: 0 });
      fetchDashboardData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Check-in failed");
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Check-Out: first show feedback, then complete
  const handleProceedToFeedback = () => {
    if (!actionForm.staff_id) { toast.error("Please select staff member"); return; }
    setPendingCheckoutBooking({ ...selectedBooking, _checkoutForm: { ...actionForm } });
    setShowCheckOutModal(false);
    setShowFeedback(true);
  };

  const handleFeedbackSubmitted = async () => {
    setShowFeedback(false);
    const booking = pendingCheckoutBooking;
    const form = booking._checkoutForm;
    setActionLoading(true);
    try {
      await axios.post(`${API}/bookings/check-out`, {
        booking_id: booking.id,
        staff_id: form.staff_id,
        final_payment: form.final_payment,
        payment_mode: form.payment_mode,
        notes: form.notes
      });
      toast.success(`${booking.guest_name} checked out successfully!`);
      // Generate receipt PDF
      const settingsData = await axios.get(`${API}/settings`).then(r => r.data);
      generateCheckoutReceipt(booking, settingsData);
      setPendingCheckoutBooking(null);
      setSelectedBooking(null);
      setActionForm({ staff_id: "", notes: "", final_payment: 0, payment_mode: "", reason: "", extra_beds: 0 });
      fetchDashboardData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Check-out failed");
    } finally {
      setActionLoading(false);
    }
  };

  // Calculate refund when booking is selected for cancellation
  const calculateRefund = async (booking) => {
    try {
      const res = await axios.get(`${API}/bookings/${booking.id}/calculate-refund`);
      setRefundInfo(res.data);
    } catch (error) {
      console.error("Error calculating refund:", error);
      setRefundInfo(null);
    }
  };

  // Handle Cancel Booking
  const handleCancelBooking = async () => {
    if (!refundInfo) return;
    setActionLoading(true);
    try {
      await axios.post(`${API}/bookings/cancel`, {
        booking_id: selectedBooking.id,
        reason: actionForm.reason,
        refund_amount: refundInfo.refund_amount
      });
      toast.success(`Booking cancelled. Refund: ${formatCurrency(refundInfo.refund_amount)}`);
      setShowCancelModal(false);
      setSelectedBooking(null);
      setRefundInfo(null);
      setActionForm({ staff_id: "", notes: "", final_payment: 0, payment_mode: "", reason: "", extra_beds: 0 });
      fetchDashboardData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Cancellation failed");
    } finally {
      setActionLoading(false);
    }
  };

  // Open cancel modal with refund calculation
  const openCancelModal = async (booking) => {
    setSelectedBooking(booking);
    setShowCancelModal(true);
    await calculateRefund(booking);
  };

  // Open pending refunds modal
  const openPendingRefundsModal = async () => {
    setShowPendingRefundsModal(true);
    setPendingRefundsLoading(true);
    try {
      const res = await axios.get(`${API}/refunds?status=pending`);
      setPendingRefunds(res.data);
    } catch (error) {
      toast.error("Failed to load pending refunds");
    } finally {
      setPendingRefundsLoading(false);
    }
  };

  const handleMarkRefundPaid = async (refundId) => {
    try {
      await axios.put(`${API}/refunds/${refundId}`, { status: "completed" });
      setPendingRefunds(prev => prev.filter(r => r.id !== refundId));
      toast.success("Refund marked as paid!");
      // Refresh dashboard funds data
      const fundsRes = await axios.get(`${API}/dashboard/funds?month=${selectedMonth}&year=${selectedYear}`);
      setFunds(fundsRes.data);
    } catch (error) {
      toast.error("Failed to mark refund as paid");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="dashboard-loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard">
      {/* Page Title & Action Buttons */}
      <div className="space-y-4">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-800" style={{ fontFamily: 'Outfit, sans-serif' }}>
          Dashboard
        </h1>
        
        {/* Action Buttons Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-3">
          {/* New Booking - Prominent */}
          <Button 
            onClick={() => navigate('/bookings?action=new')}
            className="col-span-2 sm:col-span-1 h-16 px-6 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white font-semibold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-blue-500/30 transform transition-all hover:scale-105"
            data-testid="new-booking-btn"
          >
            <CalendarCheck size={24} weight="fill" />
            <span className="text-base">New Booking</span>
          </Button>
          
          <Button 
            onClick={() => setShowCheckInModal(true)}
            className="h-16 px-5 bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-xl flex items-center justify-center gap-2 shadow-md"
            data-testid="quick-checkin-btn"
          >
            <SignIn size={22} />
            <span>Check In</span>
          </Button>
          
          <Button 
            onClick={() => setShowCheckOutModal(true)}
            className="h-16 px-5 bg-amber-500 hover:bg-amber-600 text-white font-medium rounded-xl flex items-center justify-center gap-2 shadow-md"
            data-testid="quick-checkout-btn"
          >
            <SignOut size={22} />
            <span>Check Out</span>
          </Button>
          
          <Button 
            onClick={() => setShowCancelModal(true)}
            className="h-16 px-5 bg-red-500 hover:bg-red-600 text-white font-medium rounded-xl flex items-center justify-center gap-2 shadow-md"
            data-testid="cancel-booking-btn"
          >
            <X size={22} />
            <span>Cancel</span>
          </Button>
          
          {/* Feedback Button */}
          {(() => {
            const score = feedbackAnalysis?.average_score || 0;
            const count = feedbackAnalysis?.total_count || 0;
            const emoji = count === 0 ? "" : score >= 4 ? " 😊" : score >= 2.5 ? " 😐" : " 😢";
            const btnClass = count === 0
              ? "h-16 px-5 bg-slate-100 text-slate-600 font-medium rounded-xl flex items-center justify-center gap-2 border border-slate-200 shadow-sm"
              : score >= 4
              ? "h-16 px-5 bg-emerald-100 text-emerald-800 border border-emerald-300 font-medium rounded-xl flex items-center justify-center gap-2 shadow-sm"
              : score >= 2.5
              ? "h-16 px-5 bg-orange-100 text-orange-800 border border-orange-300 font-medium rounded-xl flex items-center justify-center gap-2 shadow-sm"
              : "h-16 px-5 bg-red-100 text-red-800 border border-red-300 font-medium rounded-xl flex items-center justify-center gap-2 shadow-sm";
            return (
              <Button
                onClick={() => navigate('/feedback')}
                className={btnClass}
                data-testid="feedback-btn"
              >
                <Star size={22} weight={count > 0 ? "fill" : "regular"} />
                <span>Feedback{emoji}</span>
              </Button>
            );
          })()}
          
          <Button 
            onClick={() => navigate('/reports')} 
            className="h-16 px-5 bg-indigo-100 text-indigo-700 border border-indigo-200 font-medium rounded-xl flex items-center justify-center gap-2 hover:bg-indigo-200 shadow-sm" 
            data-testid="reports-btn"
          >
            <ChartBar size={22} />
            <span>Reports</span>
          </Button>
          
          {/* Meals - Disabled for now */}
          <Button 
            disabled
            className="h-16 px-5 bg-slate-100 text-slate-400 font-medium rounded-xl flex items-center justify-center gap-2 cursor-not-allowed opacity-50"
            data-testid="meals-btn-placeholder"
          >
            <ForkKnife size={22} />
            <span>Meals</span>
          </Button>
        </div>
      </div>

      {/* Overall Occupancy Summary */}
      {occupancy && (
        <Card className="earms-card border-2 border-blue-200 bg-gradient-to-br from-blue-50 via-indigo-50 to-blue-50 shadow-md" data-testid="overall-occupancy-card">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="p-4 bg-blue-500 rounded-2xl">
                  <Bed size={32} className="text-white" weight="fill" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-800" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    Overall Occupancy
                  </h2>
                  <p className="text-slate-500">Real-time room status</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 flex-1 max-w-2xl">
                <div className="occupancy-stat total" data-testid="stat-total-rooms">
                  <span className="text-3xl font-bold">{occupancy.overall.total}</span>
                  <span className="text-sm font-medium mt-1">Total Rooms</span>
                </div>
                <div className="occupancy-stat occupied" data-testid="stat-occupied-rooms">
                  <span className="text-3xl font-bold">{occupancy.overall.occupied}</span>
                  <span className="text-sm font-medium mt-1">Occupied</span>
                </div>
                <div className="occupancy-stat available" data-testid="stat-available-rooms">
                  <span className="text-3xl font-bold">{occupancy.overall.available}</span>
                  <span className="text-sm font-medium mt-1">Available</span>
                </div>
                <div className="occupancy-stat total" data-testid="stat-occupancy-percent">
                  <span className="text-3xl font-bold">{occupancy.overall.occupancy_percent}%</span>
                  <span className="text-sm font-medium mt-1">Occupancy</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category-wise Breakup */}
      {occupancy && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* Cat I */}
          <Card className="earms-card bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200 shadow-md" data-testid="cat-i-occupancy-card">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-blue-800">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                Cat I Rooms
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-3">
                <div className="text-center p-3 bg-white/70 rounded-xl border border-blue-100">
                  <div className="text-2xl font-bold text-blue-800">{occupancy.cat_i.total}</div>
                  <div className="text-xs text-blue-600">Total</div>
                </div>
                <div className="text-center p-3 bg-white/70 rounded-xl border border-red-100">
                  <div className="text-2xl font-bold text-red-800">{occupancy.cat_i.occupied}</div>
                  <div className="text-xs text-red-600">Occupied</div>
                </div>
                <div className="text-center p-3 bg-white/70 rounded-xl border border-emerald-100">
                  <div className="text-2xl font-bold text-emerald-800">{occupancy.cat_i.available}</div>
                  <div className="text-xs text-emerald-600">Available</div>
                </div>
                <div className="text-center p-3 bg-white/70 rounded-xl border border-slate-200">
                  <div className="text-2xl font-bold text-slate-800">{occupancy.cat_i.occupancy_percent}%</div>
                  <div className="text-xs text-slate-600">Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Cat II */}
          <Card className="earms-card bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200 shadow-md" data-testid="cat-ii-occupancy-card">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-purple-800">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                Cat II Rooms
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-3">
                <div className="text-center p-3 bg-white/70 rounded-xl border border-purple-100">
                  <div className="text-2xl font-bold text-purple-800">{occupancy.cat_ii.total}</div>
                  <div className="text-xs text-purple-600">Total</div>
                </div>
                <div className="text-center p-3 bg-white/70 rounded-xl border border-red-100">
                  <div className="text-2xl font-bold text-red-800">{occupancy.cat_ii.occupied}</div>
                  <div className="text-xs text-red-600">Occupied</div>
                </div>
                <div className="text-center p-3 bg-white/70 rounded-xl border border-emerald-100">
                  <div className="text-2xl font-bold text-emerald-800">{occupancy.cat_ii.available}</div>
                  <div className="text-xs text-emerald-600">Available</div>
                </div>
                <div className="text-center p-3 bg-white/70 rounded-xl border border-slate-200">
                  <div className="text-2xl font-bold text-slate-800">{occupancy.cat_ii.occupancy_percent}%</div>
                  <div className="text-xs text-slate-600">Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Today's & Upcoming Bookings */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Today's Bookings */}
        <Card className="earms-card bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200 shadow-md" data-testid="today-bookings-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock size={20} className="text-amber-600" weight="fill" />
              Today's Bookings
            </CardTitle>
          </CardHeader>
          <CardContent>
            {bookings.today.length === 0 ? (
              <p className="text-slate-400 text-center py-6">No bookings for today</p>
            ) : (
              <div className="space-y-3">
                {bookings.today.slice(0, 5).map((booking) => (
                  <div 
                    key={booking.id} 
                    className="flex items-center justify-between p-3 bg-white/70 rounded-xl border border-amber-100"
                    data-testid={`today-booking-${booking.id}`}
                  >
                    <div>
                      <p className="font-medium text-slate-800">{booking.guest_name}</p>
                      <p className="text-sm text-slate-500">Room {getRoomDisplay(booking)}</p>
                    </div>
                    <Badge className={booking.status === "checked_in" ? "badge-success" : "badge-info"}>
                      {booking.status === "checked_in" ? "Checked In" : "Confirmed"}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Upcoming Bookings */}
        <Card className="earms-card bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200 shadow-md" data-testid="upcoming-bookings-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarCheck size={20} className="text-blue-500" weight="fill" />
              Upcoming Bookings (7 days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {bookings.upcoming.length === 0 ? (
              <p className="text-slate-400 text-center py-6">No upcoming bookings</p>
            ) : (
              <div className="space-y-3">
                {bookings.upcoming.slice(0, 5).map((booking) => (
                  <div 
                    key={booking.id} 
                    className="flex items-center justify-between p-3 bg-white/70 rounded-xl border border-emerald-100"
                    data-testid={`upcoming-booking-${booking.id}`}
                  >
                    <div>
                      <p className="font-medium text-slate-800">{booking.guest_name}</p>
                      <p className="text-sm text-slate-500">
                        Room {getRoomDisplay(booking)} • {format(parseISO(booking.check_in_date), "dd MMM")}
                      </p>
                    </div>
                    <Badge className="badge-info">Confirmed</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Period Selector */}
      <Card className="earms-card" data-testid="period-selector-card">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <span className="font-medium text-slate-700">Analytics Period:</span>
            <Select value={selectedMonth.toString()} onValueChange={(v) => setSelectedMonth(parseInt(v))}>
              <SelectTrigger className="w-40" data-testid="month-selector">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {months.map((m) => (
                  <SelectItem key={m.value} value={m.value.toString()}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v))}>
              <SelectTrigger className="w-28" data-testid="year-selector">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[2024, 2025, 2026].map((y) => (
                  <SelectItem key={y} value={y.toString()}>
                    {y}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Monthly Calendar Planner Toggle */}
      <Card className="earms-card" data-testid="calendar-planner-card">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <CalendarBlank size={22} className="text-indigo-500" weight="fill" />
              Room Planner - {months.find(m => m.value === selectedMonth)?.label} {selectedYear}
            </CardTitle>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setShowCalendar(!showCalendar)}
              className="text-indigo-600 border-indigo-200 hover:bg-indigo-50"
              data-testid="toggle-calendar-btn"
            >
              {showCalendar ? "Hide Planner" : "Show Planner"}
            </Button>
          </div>
        </CardHeader>
        {showCalendar && calendarData && (
          <CardContent className="p-4 overflow-x-auto">
            {/* Legend */}
            <div className="flex flex-wrap gap-4 mb-4 text-xs">
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 rounded bg-emerald-100 border border-emerald-300"></div>
                <span className="text-slate-600">Available</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 rounded bg-blue-400"></div>
                <span className="text-slate-600">Confirmed</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 rounded bg-amber-400"></div>
                <span className="text-slate-600">Checked In</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 rounded bg-slate-300"></div>
                <span className="text-slate-600">Checked Out</span>
              </div>
            </div>

            {/* Planner Grid */}
            <div className="min-w-[900px]">
              {/* Header row: dates */}
              <div className="flex">
                <div className="w-20 min-w-[80px] shrink-0 p-1.5 text-xs font-bold text-slate-600 border-b border-r border-slate-200 bg-slate-50 sticky left-0 z-10">
                  Room
                </div>
                {Array.from({ length: calendarData.days_in_month }, (_, i) => {
                  const day = i + 1;
                  const dateStr = `${selectedYear}-${String(selectedMonth).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
                  const dateObj = new Date(selectedYear, selectedMonth - 1, day);
                  const dayName = format(dateObj, "EEE");
                  const isWeekend = dateObj.getDay() === 0 || dateObj.getDay() === 6;
                  const isToday = format(new Date(), "yyyy-MM-dd") === dateStr;
                  return (
                    <div 
                      key={day} 
                      className={`flex-1 min-w-[34px] p-1 text-center text-[10px] border-b border-r border-slate-200 ${isWeekend ? 'bg-red-50' : 'bg-slate-50'} ${isToday ? 'ring-2 ring-inset ring-indigo-500' : ''}`}
                    >
                      <div className={`font-bold ${isToday ? 'text-indigo-600' : 'text-slate-700'}`}>{day}</div>
                      <div className={`${isWeekend ? 'text-red-400' : 'text-slate-400'}`}>{dayName.charAt(0)}</div>
                    </div>
                  );
                })}
              </div>

              {/* Room rows */}
              {calendarData.rooms.map((room) => (
                <div key={room.room_id} className="flex" data-testid={`calendar-room-${room.room_number}`}>
                  <div className={`w-20 min-w-[80px] shrink-0 p-1.5 text-xs font-semibold border-b border-r border-slate-200 sticky left-0 z-10 ${room.category === 'Cat I' ? 'bg-blue-50 text-blue-800' : 'bg-purple-50 text-purple-800'}`}>
                    {room.room_number}
                  </div>
                  {Array.from({ length: calendarData.days_in_month }, (_, i) => {
                    const day = i + 1;
                    const dateStr = `${selectedYear}-${String(selectedMonth).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
                    const dayData = room.days[dateStr];
                    const status = dayData?.status || "available";
                    const booking = dayData?.booking;

                    let cellClass = "bg-emerald-50";
                    let dotClass = "";
                    if (status === "confirmed") {
                      cellClass = "bg-blue-400";
                      dotClass = "text-white";
                    } else if (status === "checked_in") {
                      cellClass = "bg-amber-400";
                      dotClass = "text-white";
                    } else if (status === "checked_out") {
                      cellClass = "bg-slate-300";
                      dotClass = "text-slate-600";
                    }

                    return (
                      <div
                        key={day}
                        className={`flex-1 min-w-[34px] h-7 border-b border-r border-slate-200 ${cellClass} relative group cursor-default`}
                        title={booking ? `${booking.guest_name} (${status})` : "Available"}
                        data-testid={`cal-${room.room_number}-${dateStr}`}
                      >
                        {booking && (
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className={`text-[8px] font-bold truncate px-0.5 ${dotClass}`}>
                              {booking.guest_name.split(" ")[0].substring(0, 4)}
                            </span>
                          </div>
                        )}
                        {/* Tooltip on hover */}
                        {booking && (
                          <div className="hidden group-hover:block absolute z-20 bottom-full left-1/2 -translate-x-1/2 mb-1 bg-slate-900 text-white text-[10px] rounded-lg px-2.5 py-1.5 whitespace-nowrap shadow-lg">
                            <div className="font-semibold">{booking.guest_name}</div>
                            <div className="text-slate-300">#{booking.booking_number}</div>
                            <div className="text-slate-300 capitalize">{status.replace("_", " ")}</div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Analytics */}
      {analytics && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="analytics-section">
          <Card className="earms-card bg-gradient-to-br from-sky-50 to-blue-50 border-sky-200 shadow-md">
            <CardContent className="p-6 text-center">
              <div className="p-3 bg-blue-100 rounded-full w-14 h-14 mx-auto mb-3 flex items-center justify-center">
                <CalendarCheck size={28} className="text-blue-600" weight="fill" />
              </div>
              <div className="text-3xl font-bold text-slate-800" data-testid="stat-total-bookings">
                {analytics.total_bookings}
              </div>
              <div className="text-sm text-slate-500 mt-1">Total Bookings</div>
            </CardContent>
          </Card>

          <Card className="earms-card bg-gradient-to-br from-emerald-50 to-green-50 border-emerald-200 shadow-md">
            <CardContent className="p-6 text-center">
              <div className="p-3 bg-emerald-100 rounded-full w-14 h-14 mx-auto mb-3 flex items-center justify-center">
                <CheckCircle size={28} className="text-emerald-600" weight="fill" />
              </div>
              <div className="text-3xl font-bold text-slate-800" data-testid="stat-completed-stays">
                {analytics.completed_stays}
              </div>
              <div className="text-sm text-slate-500 mt-1">Completed Stays</div>
            </CardContent>
          </Card>

          <Card className="earms-card bg-gradient-to-br from-violet-50 to-purple-50 border-violet-200 shadow-md">
            <CardContent className="p-6 text-center">
              <div className="p-3 bg-purple-100 rounded-full w-14 h-14 mx-auto mb-3 flex items-center justify-center">
                <Users size={28} className="text-purple-600" weight="fill" />
              </div>
              <div className="text-3xl font-bold text-slate-800" data-testid="stat-total-guests">
                {analytics.total_guests}
              </div>
              <div className="text-sm text-slate-500 mt-1">Total Guests</div>
            </CardContent>
          </Card>

          <Card className="earms-card bg-gradient-to-br from-amber-50 to-yellow-50 border-amber-200 shadow-md">
            <CardContent className="p-6 text-center">
              <div className="p-3 bg-amber-100 rounded-full w-14 h-14 mx-auto mb-3 flex items-center justify-center">
                <TrendUp size={28} className="text-amber-600" weight="fill" />
              </div>
              <div className="text-3xl font-bold text-slate-800" data-testid="stat-avg-occupancy">
                {analytics.average_occupancy}%
              </div>
              <div className="text-sm text-slate-500 mt-1">Avg Occupancy</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Fund Generation Dashboard */}
      {funds && (
        <Card className="earms-card bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-emerald-200 shadow-md" data-testid="fund-dashboard-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CurrencyInr size={24} className="text-emerald-500" weight="fill" />
              Fund Generation - {months.find(m => m.value === selectedMonth)?.label} {selectedYear}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="fund-card earnings" data-testid="fund-completed-stays">
                <CurrencyInr size={24} className="text-emerald-700 mx-auto mb-2" />
                <div className="text-2xl font-bold text-emerald-800">
                  {formatCurrency(funds.completed_stays_amount)}
                </div>
                <div className="text-sm text-emerald-600 mt-1">Completed Stays</div>
              </div>

              <div className="fund-card advance" data-testid="fund-advance">
                <CurrencyInr size={24} className="text-amber-700 mx-auto mb-2" />
                <div className="text-2xl font-bold text-amber-800">
                  {formatCurrency(funds.advance_booking_amount)}
                </div>
                <div className="text-sm text-amber-600 mt-1">Advance Received</div>
              </div>

              <div className="fund-card refund" data-testid="fund-refunds">
                <Warning size={24} className="text-red-700 mx-auto mb-2" />
                <div className="text-2xl font-bold text-red-800">
                  {formatCurrency(funds.refunds_issued)}
                </div>
                <div className="text-sm text-red-600 mt-1">Refunds Issued</div>
              </div>

              <div className="fund-card net" data-testid="fund-net-revenue">
                <TrendUp size={24} className="text-blue-700 mx-auto mb-2" />
                <div className="text-2xl font-bold text-blue-800">
                  {formatCurrency(funds.net_revenue)}
                </div>
                <div className="text-sm text-blue-600 mt-1">Net Revenue</div>
              </div>
            </div>

            {/* Cancellation & Refund Summary */}
            <div className="p-4 bg-slate-50 rounded-xl">
              <h4 className="font-semibold text-slate-700 mb-3">Cancellation & Refund Tracking</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-xl font-bold text-slate-800" data-testid="cancellation-total">
                    {funds.cancellations.total}
                  </div>
                  <div className="text-sm text-slate-500">Total Cancellations</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-amber-600" data-testid="refund-pending-count">
                    {funds.cancellations.pending_refunds}
                  </div>
                  <div className="text-sm text-slate-500">Pending Refunds</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-emerald-600" data-testid="refund-completed-count">
                    {funds.cancellations.completed_refunds}
                  </div>
                  <div className="text-sm text-slate-500">Completed Refunds</div>
                </div>
              </div>
              {funds.cancellations.pending_refunds > 0 && (
                <button
                  className="mt-3 w-full p-3 bg-amber-100 hover:bg-amber-200 rounded-lg text-center transition-colors cursor-pointer border border-amber-300 group"
                  onClick={openPendingRefundsModal}
                  data-testid="pending-refunds-amount-btn"
                >
                  <span className="text-amber-800 font-medium">
                    Pending Refund Amount: {formatCurrency(funds.cancellations.pending_refunds_amount)}
                  </span>
                  <span className="block text-xs text-amber-600 mt-0.5 group-hover:underline">
                    Click to view guest & account details
                  </span>
                </button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Check-In Modal */}
      <Dialog open={showCheckInModal} onOpenChange={setShowCheckInModal}>
        <DialogContent className="max-w-lg" data-testid="checkin-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-emerald-600">
              <SignIn size={24} />
              Check In Guest
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Booking Selection */}
            <div>
              <Label>Select Booked Guest *</Label>
              {confirmedBookings.length === 0 ? (
                <div className="p-4 bg-slate-50 rounded-xl text-center text-slate-500 mt-2">
                  No confirmed bookings available for check-in
                </div>
              ) : (
                <Select 
                  value={selectedBooking?.id || ""} 
                  onValueChange={(v) => setSelectedBooking(confirmedBookings.find(b => b.id === v))}
                >
                  <SelectTrigger className="earms-input mt-1" data-testid="select-checkin-booking">
                    <SelectValue placeholder="Select a booking" />
                  </SelectTrigger>
                  <SelectContent>
                    {confirmedBookings.map((b) => (
                      <SelectItem key={b.id} value={b.id}>
                        {b.guest_name} - Room {getRoomDisplay(b)} ({format(parseISO(b.check_in_date), "dd MMM")})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {selectedBooking && (
              <div className="p-4 bg-emerald-50 rounded-xl">
                <p className="font-medium text-emerald-800">{selectedBooking.guest_name}</p>
                <p className="text-sm text-emerald-600">Room {getRoomDisplay(selectedBooking)} • {getRoomCategories(selectedBooking)}</p>
                <p className="text-sm text-emerald-600">
                  {format(parseISO(selectedBooking.check_in_date), "dd MMM")} - {format(parseISO(selectedBooking.check_out_date), "dd MMM yyyy")}
                </p>
              </div>
            )}

            <div>
              <Label>Staff Member *</Label>
              <Select value={actionForm.staff_id} onValueChange={(v) => setActionForm({...actionForm, staff_id: v})}>
                <SelectTrigger className="earms-input mt-1" data-testid="select-staff-checkin">
                  <SelectValue placeholder="Select staff" />
                </SelectTrigger>
                <SelectContent>
                  {staff.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.name} ({s.staff_type})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Notes</Label>
              <Textarea
                value={actionForm.notes}
                onChange={(e) => setActionForm({...actionForm, notes: e.target.value})}
                placeholder="Check-in notes..."
                className="mt-1"
              />
            </div>
            {/* Extra Beds */}
            <div className="p-3 bg-amber-50 rounded-xl border border-amber-200">
              <Label className="font-semibold text-amber-800">Extra Beds Required</Label>
              <p className="text-xs text-amber-600 mb-2">₹75 per extra bed per night — added to final bill</p>
              <div className="flex items-center gap-3">
                <Input
                  type="number"
                  min="0"
                  max="5"
                  value={actionForm.extra_beds}
                  onChange={(e) => setActionForm({...actionForm, extra_beds: parseInt(e.target.value) || 0})}
                  onFocus={(e) => e.target.select()}
                  className="earms-input w-24"
                  data-testid="input-extra-beds"
                />
                {actionForm.extra_beds > 0 && (
                  <span className="text-sm font-medium text-amber-700">
                    Extra charge: ₹{actionForm.extra_beds * 75}/night
                  </span>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowCheckInModal(false); setSelectedBooking(null); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleCheckIn} 
              disabled={!selectedBooking || !actionForm.staff_id || actionLoading}
              className="bg-emerald-500 hover:bg-emerald-600"
            >
              {actionLoading ? <SpinnerGap size={20} className="animate-spin" /> : "Confirm Check-In"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Check-Out Modal */}
      <Dialog open={showCheckOutModal} onOpenChange={setShowCheckOutModal}>
        <DialogContent className="max-w-lg" data-testid="checkout-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-600">
              <SignOut size={24} />
              Check Out Guest
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Booking Selection */}
            <div>
              <Label>Select Checked-In Guest *</Label>
              {checkedInBookings.length === 0 ? (
                <div className="p-4 bg-slate-50 rounded-xl text-center text-slate-500 mt-2">
                  No checked-in guests available for check-out
                </div>
              ) : (
                <Select 
                  value={selectedBooking?.id || ""} 
                  onValueChange={(v) => setSelectedBooking(checkedInBookings.find(b => b.id === v))}
                >
                  <SelectTrigger className="earms-input mt-1" data-testid="select-checkout-booking">
                    <SelectValue placeholder="Select a guest" />
                  </SelectTrigger>
                  <SelectContent>
                    {checkedInBookings.map((b) => (
                      <SelectItem key={b.id} value={b.id}>
                        {b.guest_name} - Room {getRoomDisplay(b)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {selectedBooking && (
              <div className="p-4 bg-amber-50 rounded-xl">
                <p className="font-medium text-amber-800">{selectedBooking.guest_name}</p>
                <p className="text-sm text-amber-600">Room {getRoomDisplay(selectedBooking)}</p>
                {selectedBooking.extra_beds > 0 && (
                  <p className="text-xs text-amber-600">Extra Beds: {selectedBooking.extra_beds} × ₹75 = ₹{selectedBooking.extra_bed_charge}</p>
                )}
                <p className="text-sm font-medium text-amber-800 mt-1">
                  Balance Due: {formatCurrency(selectedBooking.balance_amount)}
                </p>
              </div>
            )}

            <div>
              <Label>Staff Member *</Label>
              <Select value={actionForm.staff_id} onValueChange={(v) => setActionForm({...actionForm, staff_id: v})}>
                <SelectTrigger className="earms-input mt-1" data-testid="select-staff-checkout">
                  <SelectValue placeholder="Select staff" />
                </SelectTrigger>
                <SelectContent>
                  {staff.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.name} ({s.staff_type})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Final Payment</Label>
                <Input
                  type="number"
                  value={actionForm.final_payment}
                  onChange={(e) => setActionForm({...actionForm, final_payment: parseFloat(e.target.value) || 0})}
                  className="earms-input mt-1"
                />
              </div>
              <div>
                <Label>Payment Mode</Label>
                <Select value={actionForm.payment_mode} onValueChange={(v) => setActionForm({...actionForm, payment_mode: v})}>
                  <SelectTrigger className="earms-input mt-1">
                    <SelectValue placeholder="Mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cash">Cash</SelectItem>
                    <SelectItem value="upi">UPI</SelectItem>
                    <SelectItem value="card">Card</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label>Notes</Label>
              <Textarea
                value={actionForm.notes}
                onChange={(e) => setActionForm({...actionForm, notes: e.target.value})}
                placeholder="Check-out notes..."
                className="mt-1"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowCheckOutModal(false); setSelectedBooking(null); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleProceedToFeedback} 
              disabled={!selectedBooking || !actionForm.staff_id || actionLoading}
              className="bg-amber-500 hover:bg-amber-600"
              data-testid="proceed-to-feedback-btn"
            >
              {actionLoading ? <SpinnerGap size={20} className="animate-spin" /> : "Proceed to Feedback"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Feedback Form (shown before completing checkout) */}
      {showFeedback && pendingCheckoutBooking && (
        <FeedbackForm
          booking={pendingCheckoutBooking}
          open={showFeedback}
          onClose={() => { setShowFeedback(false); setPendingCheckoutBooking(null); }}
          onSubmitted={handleFeedbackSubmitted}
        />
      )}

      {/* Cancel Booking Modal */}
      <Dialog open={showCancelModal} onOpenChange={(open) => { setShowCancelModal(open); if (!open) { setSelectedBooking(null); setRefundInfo(null); } }}>
        <DialogContent className="max-w-lg" data-testid="cancel-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <X size={24} />
              Cancel Booking
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Booking Selection */}
            <div>
              <Label>Select Booking to Cancel *</Label>
              {cancellableBookings.length === 0 ? (
                <div className="p-4 bg-slate-50 rounded-xl text-center text-slate-500 mt-2">
                  No confirmed bookings available to cancel
                </div>
              ) : (
                <Select 
                  value={selectedBooking?.id || ""} 
                  onValueChange={(v) => {
                    const booking = cancellableBookings.find(b => b.id === v);
                    setSelectedBooking(booking);
                    if (booking) calculateRefund(booking);
                  }}
                >
                  <SelectTrigger className="earms-input mt-1" data-testid="select-cancel-booking">
                    <SelectValue placeholder="Select a booking" />
                  </SelectTrigger>
                  <SelectContent>
                    {cancellableBookings.map((b) => (
                      <SelectItem key={b.id} value={b.id}>
                        {b.booking_number} - {b.guest_name} (Room {getRoomDisplay(b)})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {selectedBooking && (
              <div className="p-4 bg-red-50 rounded-xl">
                <p className="font-medium text-red-800">{selectedBooking.guest_name}</p>
                <p className="text-sm text-red-600">Booking #{selectedBooking.booking_number}</p>
                <p className="text-sm text-red-600">Room {getRoomDisplay(selectedBooking)} • {getRoomCategories(selectedBooking)}</p>
                <p className="text-sm text-red-600">
                  {format(parseISO(selectedBooking.check_in_date), "dd MMM")} - {format(parseISO(selectedBooking.check_out_date), "dd MMM yyyy")}
                </p>
              </div>
            )}

            {/* Refund Calculation */}
            {refundInfo && (
              <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
                <h4 className="font-semibold text-amber-800 mb-2">Refund Calculation</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Days until check-in:</span>
                    <span className="font-medium">{refundInfo.days_until_checkin} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Advance Paid:</span>
                    <span>{formatCurrency(refundInfo.advance_paid)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Cancellation Charge ({refundInfo.charge_percent}%):</span>
                    <span className="text-red-600">- {formatCurrency(refundInfo.cancellation_charge)}</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-amber-200 mt-2">
                    <span className="font-semibold text-amber-800">Refund Amount:</span>
                    <span className="font-bold text-lg text-emerald-700">{formatCurrency(refundInfo.refund_amount)}</span>
                  </div>
                </div>
              </div>
            )}

            <div>
              <Label>Cancellation Reason</Label>
              <Textarea
                value={actionForm.reason}
                onChange={(e) => setActionForm({...actionForm, reason: e.target.value})}
                placeholder="Reason for cancellation..."
                className="mt-1"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowCancelModal(false); setSelectedBooking(null); setRefundInfo(null); }}>
              Go Back
            </Button>
            <Button 
              onClick={handleCancelBooking} 
              disabled={!selectedBooking || !refundInfo || actionLoading}
              variant="destructive"
            >
              {actionLoading ? <SpinnerGap size={20} className="animate-spin" /> : "Confirm Cancellation"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Pending Refunds Details Modal */}
      <Dialog open={showPendingRefundsModal} onOpenChange={setShowPendingRefundsModal}>
        <DialogContent className="max-w-2xl" data-testid="pending-refunds-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-700">
              <Warning size={24} weight="fill" />
              Pending Refunds
            </DialogTitle>
          </DialogHeader>
          <div className="py-4 max-h-[60vh] overflow-y-auto pr-1">
            {pendingRefundsLoading ? (
              <div className="flex items-center justify-center h-32">
                <SpinnerGap size={32} className="animate-spin text-amber-500" />
              </div>
            ) : pendingRefunds.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <CheckCircle size={40} className="mx-auto mb-3 text-emerald-400" weight="fill" />
                <p>No pending refunds at this time</p>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-slate-500">{pendingRefunds.length} refund(s) pending payment</p>
                {pendingRefunds.map((refund) => (
                  <div key={refund.id} className="p-4 bg-amber-50 border border-amber-200 rounded-xl" data-testid={`pending-refund-${refund.id}`}>
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <p className="font-semibold text-slate-800 text-lg">{refund.guest_name}</p>
                        <p className="text-sm text-slate-500">Booking #{refund.booking_number}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xl font-bold text-amber-700">{formatCurrency(refund.amount)}</p>
                        <p className="text-xs text-amber-600">Refund Due</p>
                      </div>
                    </div>

                    {/* Bank / UPI Details */}
                    <div className="p-3 bg-white rounded-lg border border-amber-100 text-sm space-y-1.5">
                      <p className="font-medium text-slate-700 mb-2">Payment Details</p>
                      {refund.bank_name && (
                        <div className="flex gap-2">
                          <span className="text-slate-500 w-32 shrink-0">Bank Name:</span>
                          <span className="font-medium text-slate-800">{refund.bank_name}</span>
                        </div>
                      )}
                      {refund.bank_ifsc && (
                        <div className="flex gap-2">
                          <span className="text-slate-500 w-32 shrink-0">IFSC Code:</span>
                          <span className="font-medium text-slate-800">{refund.bank_ifsc}</span>
                        </div>
                      )}
                      {refund.bank_account && (
                        <div className="flex gap-2">
                          <span className="text-slate-500 w-32 shrink-0">Account No:</span>
                          <span className="font-medium text-slate-800">{refund.bank_account}</span>
                        </div>
                      )}
                      {refund.upi_id && (
                        <div className="flex gap-2">
                          <span className="text-slate-500 w-32 shrink-0">UPI ID:</span>
                          <span className="font-medium text-slate-800">{refund.upi_id}</span>
                        </div>
                      )}
                      {refund.upi_phone && (
                        <div className="flex gap-2">
                          <span className="text-slate-500 w-32 shrink-0">UPI Phone:</span>
                          <span className="font-medium text-slate-800">{refund.upi_phone}</span>
                        </div>
                      )}
                      {!refund.bank_name && !refund.bank_ifsc && !refund.bank_account && !refund.upi_id && !refund.upi_phone && (
                        <p className="text-slate-400 italic">No bank/UPI details provided at booking time</p>
                      )}
                    </div>
                    {/* Mark as Paid button */}
                    <div className="mt-3 flex justify-end">
                      <Button
                        size="sm"
                        className="bg-emerald-500 hover:bg-emerald-600 text-white"
                        onClick={() => handleMarkRefundPaid(refund.id)}
                        data-testid={`mark-refund-paid-${refund.id}`}
                      >
                        <CheckCircle size={16} className="mr-1" weight="fill" />
                        Mark as Paid
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPendingRefundsModal(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
