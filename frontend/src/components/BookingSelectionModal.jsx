import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { SignIn, SignOut, SpinnerGap } from "@phosphor-icons/react";
import { format, parseISO } from "date-fns";

/**
 * BookingSelectionModal - Lightweight modal for selecting a booking
 * Used before redirecting to the full Check-In / Check-Out form in Bookings page
 * 
 * Props:
 * - open: boolean
 * - onOpenChange: (open: boolean) => void
 * - action: "checkin" | "checkout"
 */
export default function BookingSelectionModal({ open, onOpenChange, action }) {
  const navigate = useNavigate();
  const [eligibleBookings, setEligibleBookings] = useState([]);
  const [selectedBookingId, setSelectedBookingId] = useState("");
  const [loading, setLoading] = useState(false);

  const isCheckIn = action === "checkin";
  const title = isCheckIn ? "Select Booking for Check-In" : "Select Booking for Check-Out";
  const Icon = isCheckIn ? SignIn : SignOut;
  const iconColor = isCheckIn ? "text-emerald-500" : "text-amber-500";

  // Fetch eligible bookings when modal opens
  useEffect(() => {
    if (!open) return;
    
    const fetchEligibleBookings = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API}/bookings`);
        const allBookings = response.data;
        
        // Filter based on action type
        const filtered = allBookings.filter(booking => {
          if (isCheckIn) {
            return booking.status === "confirmed";
          } else {
            return booking.status === "checked_in";
          }
        });
        
        setEligibleBookings(filtered);
        
        if (filtered.length === 0) {
          const message = isCheckIn 
            ? "No confirmed bookings available for check-in" 
            : "No checked-in bookings available for check-out";
          toast.info(message);
        }
      } catch (error) {
        console.error("Error fetching bookings:", error);
        toast.error("Failed to load bookings");
      } finally {
        setLoading(false);
      }
    };

    fetchEligibleBookings();
  }, [open, isCheckIn]);

  // Helper to display room numbers
  const getRoomDisplay = (booking) => {
    if (booking.room_numbers && booking.room_numbers.length > 0) {
      return booking.room_numbers.join(", ");
    }
    return booking.room_number || "N/A";
  };

  const handleProceed = () => {
    if (!selectedBookingId) {
      toast.error("Please select a booking");
      return;
    }
    
    // Navigate to Bookings page with query params
    navigate(`/app/bookings?action=${action}&bookingId=${selectedBookingId}`);
    
    // Close modal and reset
    onOpenChange(false);
    setSelectedBookingId("");
  };

  const handleCancel = () => {
    onOpenChange(false);
    setSelectedBookingId("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md" data-testid={`booking-selection-${action}`}>
        <DialogHeader>
          <DialogTitle className={`flex items-center gap-2 ${iconColor}`}>
            <Icon size={24} weight="fill" />
            {title}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <SpinnerGap size={32} className="animate-spin text-slate-400" />
            </div>
          ) : eligibleBookings.length === 0 ? (
            <div className="p-4 bg-slate-50 rounded-xl text-center text-slate-500">
              {isCheckIn 
                ? "No confirmed bookings available for check-in" 
                : "No checked-in guests available for check-out"}
            </div>
          ) : (
            <>
              <div>
                <Label className="text-slate-700 font-medium">Select Booking *</Label>
                <Select 
                  value={selectedBookingId} 
                  onValueChange={setSelectedBookingId}
                >
                  <SelectTrigger className="mt-2" data-testid="select-booking-dropdown">
                    <SelectValue placeholder="Choose a booking..." />
                  </SelectTrigger>
                  <SelectContent>
                    {eligibleBookings.map((booking) => (
                      <SelectItem key={booking.id} value={booking.id}>
                        <div className="flex flex-col">
                          <span className="font-medium">{booking.guest_name}</span>
                          <span className="text-xs text-slate-500">
                            #{booking.booking_number} • Room {getRoomDisplay(booking)}
                            {booking.check_in_date && ` • ${format(parseISO(booking.check_in_date), "dd MMM yyyy")}`}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedBookingId && (
                <div className={`p-3 rounded-lg ${isCheckIn ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'}`}>
                  {(() => {
                    const selected = eligibleBookings.find(b => b.id === selectedBookingId);
                    if (!selected) return null;
                    return (
                      <>
                        <p className={`font-semibold ${isCheckIn ? 'text-emerald-800' : 'text-amber-800'}`}>
                          {selected.guest_name}
                        </p>
                        <p className={`text-sm ${isCheckIn ? 'text-emerald-600' : 'text-amber-600'}`}>
                          Booking #{selected.booking_number}
                        </p>
                        <p className={`text-sm ${isCheckIn ? 'text-emerald-600' : 'text-amber-600'}`}>
                          Room {getRoomDisplay(selected)}
                        </p>
                        {selected.check_in_date && (
                          <p className={`text-sm ${isCheckIn ? 'text-emerald-600' : 'text-amber-600'}`}>
                            {format(parseISO(selected.check_in_date), "dd MMM yyyy")} → {format(parseISO(selected.check_out_date), "dd MMM yyyy")}
                          </p>
                        )}
                      </>
                    );
                  })()}
                </div>
              )}
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button 
            onClick={handleProceed} 
            disabled={!selectedBookingId || loading}
            className={isCheckIn ? "bg-emerald-500 hover:bg-emerald-600" : "bg-amber-500 hover:bg-amber-600"}
            data-testid="proceed-to-form-btn"
          >
            Proceed to {isCheckIn ? "Check-In" : "Check-Out"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
