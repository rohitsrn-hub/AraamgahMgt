import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { generateCheckoutReceipt, generateRefundsPDF, generateBookingSlips } from "@/utils/pdfUtils";
import FeedbackForm from "@/components/FeedbackForm";
import { 
  Plus, 
  CalendarCheck, 
  SignIn, 
  SignOut, 
  X,
  MagnifyingGlass,
  CalendarBlank,
  User,
  Phone,
  Bed,
  CurrencyInr,
  SpinnerGap,
  CheckSquare,
  Bank,
  ArrowCounterClockwise,
  ArrowsClockwise,
  FilePdf,
  UserPlus,
  Trash,
  WarningCircle
} from "@phosphor-icons/react";
import { format, parseISO } from "date-fns";
import { useLocation } from "react-router-dom";

// Indian mobile phone validation
const validateIndianPhone = (phone) => {
  const cleaned = phone.replace(/\s+/g, "").replace(/^\+91/, "");
  return /^[6-9]\d{9}$/.test(cleaned);
};

const formatIndianPhone = (value) => {
  let digits = value.replace(/[^\d]/g, "");
  if (digits.startsWith("91") && digits.length > 10) digits = digits.slice(2);
  digits = digits.slice(0, 10);
  if (digits.length <= 5) return digits;
  return digits.slice(0, 5) + " " + digits.slice(5);
};

// IFSC Code validation (11 characters: 4 letters + 0 + 6 alphanumeric)
const validateIFSC = (ifsc) => {
  return /^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifsc);
};

// Force uppercase for ID fields
const toUpperCase = (value) => {
  return value.toUpperCase();
};

export default function Bookings() {
  const [bookings, setBookings] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [availableRooms, setAvailableRooms] = useState([]);
  const [staff, setStaff] = useState([]);
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loadingRooms, setLoadingRooms] = useState(false);

  // Controlled popover open states for date pickers
  const [checkInOpen, setCheckInOpen] = useState(false);
  const [checkOutOpen, setCheckOutOpen] = useState(false);

  // Dialog states
  const [showNewBooking, setShowNewBooking] = useState(false);
  const [showCheckIn, setShowCheckIn] = useState(false);
  const [showCheckOut, setShowCheckOut] = useState(false);
  const [showCancel, setShowCancel] = useState(false);
  const [refundInfo, setRefundInfo] = useState(null);
  const [showPendingRefunds, setShowPendingRefunds] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [pendingCheckoutBooking, setPendingCheckoutBooking] = useState(null);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [showWhatsAppModal, setShowWhatsAppModal] = useState(false);
  const [createdBookingData, setCreatedBookingData] = useState(null);

  // Guest History
  const [showGuestHistory, setShowGuestHistory] = useState(false);
  const [guestHistorySearch, setGuestHistorySearch] = useState({ phone: "", army_number: "" });
  const [guestHistoryData, setGuestHistoryData] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // 4-night booking confirmation
  const [showNightConfirmation, setShowNightConfirmation] = useState(false);
  const [pendingBookingData, setPendingBookingData] = useState(null);

  // Bulk booking slip generation
  const [selectedBookingIds, setSelectedBookingIds] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);

  // Pending refunds
  const [pendingRefunds, setPendingRefunds] = useState([]);
  const [refundAction, setRefundAction] = useState(null);
  const [refundForm, setRefundForm] = useState({ transaction_ref: "", refund_date: "", notes: "" });

  // Form state
  const [bookingForm, setBookingForm] = useState({
    guest_name: "",
    guest_contact: "",
    guest_rank: "",
    army_number: "",
    guest_unit: "",
    num_rooms: 1,
    room_ids: [],
    check_in_date: null,
    check_out_date: null,
    advance_paid: 0,
    payment_mode: "",
    payment_id: "",
    bank_name: "",
    bank_ifsc: "",
    bank_account: "",
    upi_id: "",        // NEW: UPI ID for refunds
    upi_phone: ""      // NEW: UPI Phone for refunds
  });

  const [actionForm, setActionForm] = useState({
    staff_id: "",
    notes: "",
    final_payment: 0,
    payment_mode: "",
    reason: "",
    refund_amount: 0,
    extra_beds: 0,
    extra_beds_checkout: 0,  // Extra beds used at checkout
    extra_bed_days: 0,        // Days extra beds were used
    // Check-in personal details
    guest_contact: "",
    guest_age: "",
    guest_sex: "",
    guest_address: "",
    identity_card_number: "",
    guest_service_status: "",
    service_type: "",
    command_hq: "",
    bank_name: "",
    bank_ifsc: "",
    bank_account: "",
    upi_id: "",
    upi_phone: "",
    family_members: []
  });

  const [phoneError, setPhoneError] = useState("");
  const [bookingPhoneError, setBookingPhoneError] = useState("");
  const [bookingIfscError, setBookingIfscError] = useState("");
  const [checkinIfscError, setCheckinIfscError] = useState("");
  const [upiPhoneError, setUpiPhoneError] = useState("");
  const [checkinUpiPhoneError, setCheckinUpiPhoneError] = useState("");
  
  // Room-Guest Mapping for new pricing logic
  const [roomGuestMapping, setRoomGuestMapping] = useState([]);
  
  // P2: Room modification during check-in
  const [showRoomModification, setShowRoomModification] = useState(false);
  const [availableRoomsForCheckIn, setAvailableRoomsForCheckIn] = useState([]);
  const [modifiedRoomIds, setModifiedRoomIds] = useState([]);

  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const action = params.get('action');
    const bookingId = params.get('bookingId');
    
    if (!action) return;
    
    if (action === 'new') {
      setShowNewBooking(true);
    } else if (action === 'checkin') {
      // Only process if bookings are loaded
      if (bookings.length === 0) return;
      
      // If bookingId is provided, find and open that specific booking
      if (bookingId) {
        const targetBooking = bookings.find(b => b.id === bookingId);
        if (targetBooking) {
          if (targetBooking.status === 'confirmed') {
            openCheckInDialog(targetBooking);
          } else {
            toast.error(`Booking cannot be checked in (status: ${targetBooking.status})`);
          }
        } else {
          toast.error("Booking not found");
        }
      } else {
        // Fallback: Find first confirmed booking
        const confirmedBooking = bookings.find(b => b.status === 'confirmed');
        if (confirmedBooking) {
          openCheckInDialog(confirmedBooking);
        } else {
          toast.info("No confirmed bookings available for check-in");
        }
      }
    } else if (action === 'checkout') {
      // Only process if bookings are loaded
      if (bookings.length === 0) return;
      
      // If bookingId is provided, find and open that specific booking
      if (bookingId) {
        const targetBooking = bookings.find(b => b.id === bookingId);
        if (targetBooking) {
          if (targetBooking.status === 'checked_in') {
            openCheckOutDialog(targetBooking);
          } else {
            toast.error(`Booking cannot be checked out (status: ${targetBooking.status})`);
          }
        } else {
          toast.error("Booking not found");
        }
      } else {
        // Fallback: Find first checked-in booking
        const checkedInBooking = bookings.find(b => b.status === 'checked_in');
        if (checkedInBooking) {
          openCheckOutDialog(checkedInBooking);
        } else {
          toast.info("No checked-in bookings available for check-out");
        }
      }
    } else if (action === 'cancel') {
      // Only process if bookings are loaded
      if (bookings.length === 0) return;
      
      // If bookingId is provided, find and open that specific booking
      if (bookingId) {
        const targetBooking = bookings.find(b => b.id === bookingId);
        if (targetBooking) {
          if (targetBooking.status === 'confirmed' || targetBooking.status === 'checked_in') {
            openCancelDialog(targetBooking);
          } else {
            toast.error(`Booking cannot be cancelled (status: ${targetBooking.status})`);
          }
        } else {
          toast.error("Booking not found");
        }
      } else {
        // Fallback: Find first cancelable booking
        const cancelableBooking = bookings.find(b => b.status === 'confirmed' || b.status === 'checked_in');
        if (cancelableBooking) {
          openCancelDialog(cancelableBooking);
        } else {
          toast.info("No bookings available for cancellation");
        }
      }
    }
  }, [location, bookings]);

  const fetchData = async () => {
    try {
      const [bookingsRes, roomsRes, staffRes, settingsRes] = await Promise.all([
        axios.get(`${API}/bookings`),
        axios.get(`${API}/rooms`),
        axios.get(`${API}/staff`),
        axios.get(`${API}/settings`)
      ]);
      setBookings(bookingsRes.data);
      setRooms(roomsRes.data);
      setStaff(staffRes.data);
      setSettings(settingsRes.data);
      if (settingsRes.data?.default_advance_amount) {
        setBookingForm(prev => ({
          ...prev,
          advance_paid: settingsRes.data.default_advance_amount
        }));
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const fetchPendingRefunds = async () => {
    try {
      const res = await axios.get(`${API}/refunds`, { params: { status: "pending" } });
      setPendingRefunds(res.data);
    } catch (error) {
      toast.error("Failed to load pending refunds");
    }
  };

  useEffect(() => {
    if (settings?.default_advance_amount) {
      setBookingForm(prev => ({
        ...prev,
        advance_paid: settings.default_advance_amount * prev.num_rooms
      }));
    }
  }, [bookingForm.num_rooms, settings]);

  useEffect(() => {
    setBookingForm(prev => ({ ...prev, room_ids: [] }));
  }, [bookingForm.num_rooms]);

  const fetchAvailableRooms = async (checkIn, checkOut) => {
    if (!checkIn || !checkOut) { setAvailableRooms([]); return; }
    setLoadingRooms(true);
    try {
      const response = await axios.get(`${API}/dashboard/room-availability`, {
        params: {
          check_in_date: format(checkIn, "yyyy-MM-dd"),
          check_out_date: format(checkOut, "yyyy-MM-dd")
        }
      });
      setAvailableRooms(response.data.available_rooms || []);
    } catch (error) {
      toast.error("Failed to check room availability");
      setAvailableRooms([]);
    } finally {
      setLoadingRooms(false);
    }
  };

  useEffect(() => {
    if (bookingForm.check_in_date && bookingForm.check_out_date) {
      fetchAvailableRooms(bookingForm.check_in_date, bookingForm.check_out_date);
      setBookingForm(prev => ({ ...prev, room_ids: [] }));
    }
  }, [bookingForm.check_in_date, bookingForm.check_out_date]);

  useEffect(() => { fetchData(); }, []);

  const filteredBookings = bookings.filter(booking => {
    const roomNums = (booking.room_numbers || [booking.room_number || ""]).join(", ");
    const matchesSearch =
      booking.guest_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.booking_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      roomNums.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || booking.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getRoomDisplay = (booking) => {
    if (booking.room_numbers?.length > 0) return booking.room_numbers.join(", ");
    return booking.room_number || "N/A";
  };

  const getRoomCategories = (booking) => {
    if (booking.room_categories?.length > 0) {
      return [...new Set(booking.room_categories)].join(", ");
    }
    return booking.room_category || "";
  };

  const resetBookingForm = () => {
    setBookingForm({
      guest_name: "",
      guest_contact: "",
      guest_rank: "",
      army_number: "",
      guest_unit: "",
      num_rooms: 1,
      room_ids: [],
      check_in_date: null,
      check_out_date: null,
      advance_paid: settings?.default_advance_amount || 400,
      payment_mode: "",
      payment_id: "",
      bank_name: "",
      bank_ifsc: "",
      bank_account: ""
    });
    setAvailableRooms([]);
    setBookingPhoneError("");
  };

  const toggleRoomSelection = (roomId) => {
    setBookingForm(prev => {
      const currentIds = prev.room_ids || [];
      if (currentIds.includes(roomId)) {
        return { ...prev, room_ids: currentIds.filter(id => id !== roomId) };
      } else {
        if (currentIds.length < prev.num_rooms) {
          return { ...prev, room_ids: [...currentIds, roomId] };
        } else {
          toast.error(`You can only select ${prev.num_rooms} room(s)`);
          return prev;
        }
      }
    });
  };

  // Check if required payment details are filled based on mode
  const isPaymentDetailsFilled = () => {
    const m = bookingForm.payment_mode;
    if (m === "cash") return !!bookingForm.payment_id;
    if (m === "upi") return !!(bookingForm.upi_id || bookingForm.payment_id);
    if (m === "bank_transfer") return !!(bookingForm.bank_name && bookingForm.bank_account);
    if (m === "card") return !!bookingForm.payment_id;
    return false;
  };

  const handleCreateBooking = async () => {
    // Guest Name validation
    if (!bookingForm.guest_name || bookingForm.guest_name.trim().length < 2) {
      toast.error("Guest name is required (minimum 2 characters)");
      return;
    }
    if (bookingForm.guest_name.length > 100) {
      toast.error("Guest name cannot exceed 100 characters");
      return;
    }
    
    // Phone number validation (if provided)
    if (bookingForm.guest_contact) {
      const cleanPhone = bookingForm.guest_contact.replace(/\s/g, "");
      if (!validateIndianPhone(cleanPhone)) {
        toast.error("Enter valid 10-digit Indian mobile number");
        return;
      }
    }
    
    // Date and room validation
    if (!bookingForm.check_in_date || !bookingForm.check_out_date) {
      toast.error("Please select check-in and check-out dates");
      return;
    }
    
    // P3: Check-in date must be today or future (unless migration mode enabled)
    const migrationMode = localStorage.getItem("migration_mode") === "true";
    if (!migrationMode) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const checkInDate = new Date(bookingForm.check_in_date);
      checkInDate.setHours(0, 0, 0, 0);
      if (checkInDate < today) {
        toast.error("Check-in date must be today or a future date");
        return;
      }
    }
    
    // Check-out must be after check-in
    if (bookingForm.check_out_date <= bookingForm.check_in_date) {
      toast.error("Check-out date must be after check-in date");
      return;
    }
    
    if (bookingForm.room_ids.length === 0) {
      toast.error("Please select at least one room");
      return;
    }
    if (bookingForm.room_ids.length !== bookingForm.num_rooms) {
      toast.error(`Please select exactly ${bookingForm.num_rooms} room(s)`);
      return;
    }
    
    // Payment validation
    if (!bookingForm.payment_mode) {
      toast.error("Please select payment mode");
      return;
    }
    if (!isPaymentDetailsFilled()) {
      toast.error("Please fill in the required payment details");
      return;
    }
    
    // Advance amount validation
    if (bookingForm.advance_paid < 0) {
      toast.error("Advance amount cannot be negative");
      return;
    }

    // Calculate number of nights
    const checkIn = new Date(bookingForm.check_in_date);
    const checkOut = new Date(bookingForm.check_out_date);
    const nights = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));

    // Check if booking is more than 4 nights
    if (nights > 4) {
      // Store booking data and show confirmation dialog
      setPendingBookingData(bookingForm);
      setShowNightConfirmation(true);
      return;
    }

    // Proceed with booking
    await executeBooking();
  };

  const executeBooking = async () => {
    const formData = pendingBookingData || bookingForm;
    
    try {
      // Format phone number with +91 prefix if provided
      const formattedPhone = formData.guest_contact
        ? "+91 " + formData.guest_contact.replace(/\s/g, "").replace(/^\+91/, "")
        : undefined;

      const payload = {
        guest_name: formData.guest_name,
        guest_contact: formattedPhone,
        guest_rank: formData.guest_rank,
        army_number: formData.army_number,
        aadhaar_number: formData.aadhaar_number,
        guest_unit: formData.guest_unit,
        room_ids: formData.room_ids,
        num_rooms: formData.num_rooms,
        check_in_date: format(formData.check_in_date, "yyyy-MM-dd"),
        check_out_date: format(formData.check_out_date, "yyyy-MM-dd"),
        advance_paid: formData.advance_paid,
        payment_mode: formData.payment_mode,
        payment_id: formData.payment_id,
        bank_name: formData.bank_name,
        bank_ifsc: formData.bank_ifsc,
        bank_account: formData.bank_account,
        upi_id: formData.upi_id,
        upi_phone: formData.upi_phone
      };
      const response = await axios.post(`${API}/bookings`, payload);
      const createdBooking = response.data;
      
      toast.success(`Booking created for ${formData.num_rooms} room(s)!`);
      setShowNewBooking(false);
      setShowNightConfirmation(false);
      setPendingBookingData(null);
      
      // Clear URL parameters to prevent auto-reopen
      window.history.replaceState({}, '', '/app/bookings');
      
      // Show WhatsApp message modal with booking details
      setCreatedBookingData(createdBooking);
      setShowWhatsAppModal(true);
      
      resetBookingForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create booking");
    }
  };

  const resetActionForm = () => setActionForm({
    staff_id: "", notes: "", final_payment: 0, payment_mode: "", reason: "", refund_amount: 0, extra_beds: 0,
    guest_contact: "", guest_age: "", guest_sex: "", guest_address: "", identity_card_number: "",
    guest_service_status: "", service_type: "", command_hq: "",
    bank_name: "", bank_ifsc: "", bank_account: "", upi_id: "", upi_phone: "", family_members: []
  });

  const handleCheckinPhoneChange = (value) => {
    const formatted = formatIndianPhone(value);
    setActionForm(prev => ({ ...prev, guest_contact: formatted }));
    if (formatted.replace(/\s/g, "").length >= 10) {
      setPhoneError(validateIndianPhone(formatted) ? "" : "Enter a valid 10-digit Indian mobile number");
    } else {
      setPhoneError("");
    }
  };

  const handleBookingPhoneChange = (value) => {
    const formatted = formatIndianPhone(value);
    setBookingForm(prev => ({ ...prev, guest_contact: formatted }));
    if (formatted.replace(/\s/g, "").length >= 10) {
      setBookingPhoneError(validateIndianPhone(formatted) ? "" : "Enter a valid 10-digit Indian mobile number");
    } else {
      setBookingPhoneError("");
    }
  };

  const addCheckinFamilyMember = () => setActionForm(prev => ({
    ...prev,
    family_members: [...prev.family_members, { relation: "w/o", name: "", age: "", sex: "F", aadhaar: "", mobile: "", dependent_id: "" }]
  }));

  const removeCheckinFamilyMember = (idx) => setActionForm(prev => ({
    ...prev,
    family_members: prev.family_members.filter((_, i) => i !== idx)
  }));

  const updateCheckinFamilyMember = (idx, field, value) => setActionForm(prev => ({
    ...prev,
    family_members: prev.family_members.map((m, i) => i === idx ? { ...m, [field]: value } : m)
  }));

  // Room-Guest Mapping Functions (REDESIGNED for inline family members)
  const toggleSelfInRoom = (roomIndex) => {
    setRoomGuestMapping(prev => {
      const updated = [...prev];
      
      // If this room already has Self, remove it
      if (updated[roomIndex].has_self) {
        updated[roomIndex].has_self = false;
      } else {
        // Remove Self from all other rooms (Self can only be in one room)
        updated.forEach((room, idx) => {
          if (idx !== roomIndex) {
            room.has_self = false;
          }
        });
        // Add Self to this room
        updated[roomIndex].has_self = true;
      }
      
      // Recalculate charge category for all affected rooms
      return updated.map(room => calculateRoomChargeCategory(room));
    });
  };

  const addFamilyMemberToRoom = (roomIndex) => {
    setRoomGuestMapping(prev => {
      const updated = [...prev];
      updated[roomIndex].family_members.push({
        relation: "w/o",
        name: "",
        age: "",
        sex: "F",
        mobile: "",
        has_dependent_card: false,  // Default: no dependent card
        dependent_id: ""
      });
      // Recalculate charge category
      updated[roomIndex] = calculateRoomChargeCategory(updated[roomIndex]);
      return updated;
    });
  };

  const removeFamilyMemberFromRoom = (roomIndex, memberIndex) => {
    setRoomGuestMapping(prev => {
      const updated = [...prev];
      updated[roomIndex].family_members = updated[roomIndex].family_members.filter((_, idx) => idx !== memberIndex);
      // Recalculate charge category
      updated[roomIndex] = calculateRoomChargeCategory(updated[roomIndex]);
      return updated;
    });
  };

  const updateRoomFamilyMember = (roomIndex, memberIndex, field, value) => {
    setRoomGuestMapping(prev => {
      const updated = [...prev];
      updated[roomIndex].family_members[memberIndex] = {
        ...updated[roomIndex].family_members[memberIndex],
        [field]: value
      };
      // Recalculate charge category
      updated[roomIndex] = calculateRoomChargeCategory(updated[roomIndex]);
      return updated;
    });
  };

  const calculateRoomChargeCategory = (roomMapping) => {
    // Check if any family member lacks dependent card
    const anyMemberWithoutCard = roomMapping.family_members.some(m => !m.has_dependent_card);
    
    // If Self is not in this room and there are no family members, keep original category
    if (!roomMapping.has_self && roomMapping.family_members.length === 0) {
      return {
        ...roomMapping,
        charge_category: roomMapping.room_category
      };
    }
    
    // If any family member lacks dependent card → Def Civ rate
    if (anyMemberWithoutCard) {
      return {
        ...roomMapping,
        charge_category: "Def Civ"
      };
    }
    
    // If Self has valid ID (from identity_card_number field) and all family members have dependent cards
    const selfHasValidId = actionForm.identity_card_number && actionForm.identity_card_number.trim().length > 0;
    
    if (roomMapping.has_self && !selfHasValidId) {
      // Self lacks valid ID
      return {
        ...roomMapping,
        charge_category: "Def Civ"
      };
    }
    
    // All conditions met → Original category (Cat I/II)
    return {
      ...roomMapping,
      charge_category: roomMapping.room_category
    };
  };

  const handleCheckIn = async () => {
    // Date validation - Cannot check in before scheduled check-in date
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Reset time to start of day
    
    const checkInDate = new Date(selectedBooking.check_in_date);
    checkInDate.setHours(0, 0, 0, 0); // Reset time to start of day
    
    if (today < checkInDate) {
      const checkInDateFormatted = new Date(selectedBooking.check_in_date).toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      });
      toast.error(`Cannot check in before scheduled date: ${checkInDateFormatted}`);
      return;
    }
    
    // Staff validation
    if (!actionForm.staff_id) { 
      toast.error("Please select staff member"); 
      return; 
    }
    
    // Phone validation (required for check-in)
    if (!actionForm.guest_contact) {
      toast.error("Phone number is required for check-in");
      return;
    }
    const cleanPhone = actionForm.guest_contact.replace(/\s/g, "");
    if (!validateIndianPhone(cleanPhone)) {
      toast.error("Enter valid 10-digit mobile number");
      return;
    }
    
    // Age validation (required for check-in)
    if (!actionForm.guest_age) {
      toast.error("Age is required");
      return;
    }
    const age = parseInt(actionForm.guest_age);
    if (age < 18 || age > 120) {
      toast.error("Enter valid age (18-120)");
      return;
    }
    
    // Gender validation
    if (!actionForm.guest_sex) {
      toast.error("Please select gender");
      return;
    }
    
    // Address validation (required and min 10 chars)
    if (!actionForm.guest_address || actionForm.guest_address.trim().length < 10) {
      toast.error("Enter complete address (minimum 10 characters)");
      return;
    }
    if (actionForm.guest_address.length > 500) {
      toast.error("Address cannot exceed 500 characters");
      return;
    }
    
    // Identity card validation
    if (!actionForm.identity_card_number || actionForm.identity_card_number.trim().length === 0) {
      toast.error("Enter valid identity card number");
      return;
    }
    
    // Service status validation
    if (!actionForm.guest_service_status) {
      toast.error("Please select service status");
      return;
    }
    
    // Room-guest assignment validation
    const totalGuestsAssigned = roomGuestMapping.reduce((sum, room) => {
      return sum + (room.has_self ? 1 : 0) + room.family_members.length;
    }, 0);
    
    if (totalGuestsAssigned === 0) {
      toast.error("Please assign Self or add family members to at least one room");
      return;
    }
    
    // Collect all family members from all rooms into a single array for backend
    const allFamilyMembers = [];
    roomGuestMapping.forEach(room => {
      room.family_members.forEach(member => {
        allFamilyMembers.push({
          relation: member.relation,
          name: member.name,
          age: member.age,
          sex: member.sex,
          mobile: member.mobile,
          has_dependent_card: member.has_dependent_card,
          dependent_id: member.has_dependent_card ? member.dependent_id : ""  // Only send if card available
        });
      });
    });
    
    try {
      const formattedPhone = "+91 " + cleanPhone.replace(/^\+91/, "");
      await axios.post(`${API}/bookings/check-in`, {
        booking_id: selectedBooking.id,
        staff_id: actionForm.staff_id,
        extra_beds: actionForm.extra_beds,
        notes: actionForm.notes,
        guest_contact: formattedPhone,
        guest_age: actionForm.guest_age ? parseInt(actionForm.guest_age) : undefined,
        guest_sex: actionForm.guest_sex || undefined,
        guest_address: actionForm.guest_address || undefined,
        identity_card_number: actionForm.identity_card_number || undefined,
        guest_service_status: actionForm.guest_service_status || undefined,
        service_type: actionForm.service_type || undefined,
        command_hq: actionForm.command_hq || undefined,
        bank_name: actionForm.bank_name || undefined,
        bank_ifsc: actionForm.bank_ifsc || undefined,
        bank_account: actionForm.bank_account || undefined,
        upi_id: actionForm.upi_id || undefined,
        upi_phone: actionForm.upi_phone || undefined,
        family_members: allFamilyMembers.length > 0 ? allFamilyMembers : undefined,
        room_guest_mapping: roomGuestMapping  // Send room-guest mapping with inline family members
      });
      toast.success("Check-in successful!");
      setShowCheckIn(false);
      setSelectedBooking(null);
      resetActionForm();
      setPhoneError("");
      setRoomGuestMapping([]); // Reset room-guest mapping
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Check-in failed");
    }
  };

  const handleProceedToFeedback = () => {
    if (!actionForm.staff_id) { toast.error("Please select staff member"); return; }
    setPendingCheckoutBooking({ ...selectedBooking, _checkoutForm: { ...actionForm } });
    setShowCheckOut(false);
    setShowFeedback(true);
  };

  const handleFeedbackSubmitted = async () => {
    setShowFeedback(false);
    const booking = pendingCheckoutBooking;
    const form = booking._checkoutForm;
    try {
      await axios.post(`${API}/bookings/check-out`, {
        booking_id: booking.id,
        staff_id: form.staff_id,
        final_payment: form.final_payment,
        payment_mode: form.payment_mode,
        notes: form.notes,
        extra_beds_checkout: form.extra_beds_checkout || 0,
        extra_bed_days: form.extra_bed_days || 0
      });
      toast.success("Check-out successful!");
      // Generate receipt with enhanced notification
      const result = generateCheckoutReceipt(booking, settings);
      showPDFNotification(result, "Checkout Receipt Generated");
      setPendingCheckoutBooking(null);
      setSelectedBooking(null);
      setActionForm({ staff_id: "", notes: "", final_payment: 0, payment_mode: "", reason: "", refund_amount: 0, extra_beds: 0,
        extra_beds_checkout: 0, extra_bed_days: 0,
        guest_contact: "", guest_age: "", guest_sex: "", guest_address: "", identity_card_number: "",
        guest_service_status: "", service_type: "", command_hq: "",
        bank_name: "", bank_ifsc: "", bank_account: "", upi_id: "", upi_phone: "", family_members: [] });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Check-out failed");
    }
  };

  const openCancelDialog = async (booking) => {
    setSelectedBooking(booking);
    setRefundInfo(null);
    setShowCancel(true);
    try {
      const res = await axios.get(`${API}/bookings/${booking.id}/calculate-refund`);
      setRefundInfo(res.data);
      setActionForm(prev => ({ ...prev, refund_amount: res.data.refund_amount }));
    } catch (err) {
      console.error("Failed to calculate refund:", err);
    }
  };

  const openCheckInDialog = (booking) => {
    setSelectedBooking(booking);
    
    // Auto-fill check-in form with booking data (keep fields editable)
    setActionForm(prev => ({
      ...prev,
      // Contact details from booking
      guest_contact: booking.guest_contact || "",
      
      // Bank details from booking (if available)
      bank_name: booking.bank_name || "",
      bank_ifsc: booking.bank_ifsc || "",
      bank_account: booking.bank_account || "",
      
      // UPI details from booking (if available)
      upi_id: booking.upi_id || "",
      upi_phone: booking.upi_phone || "",
      
      // Identity - use Aadhaar from booking if available
      identity_card_number: booking.aadhaar_number || "",
      
      // Reset other fields to empty (will be filled during check-in)
      staff_id: "",
      extra_beds: 0,
      notes: "",
      guest_age: "",
      guest_sex: "",
      guest_address: "",
      guest_service_status: "",
      service_type: "",
      command_hq: "",
      family_members: []
    }));
    
    // Initialize room-guest mapping based on booked rooms (NEW STRUCTURE)
    const roomIds = booking.room_ids || [];
    const roomNumbers = booking.room_numbers || [];
    const roomCategories = booking.room_categories || [];
    
    const initialMapping = roomIds.map((roomId, index) => ({
      room_id: roomId,
      room_number: roomNumbers[index] || `Room ${index + 1}`,
      room_category: roomCategories[index] || "Cat I",
      has_self: false,  // Whether Self is assigned to this room
      family_members: [],  // Family members directly in this room
      charge_category: roomCategories[index] || "Cat I" // Will be recalculated
    }));
    
    setRoomGuestMapping(initialMapping);
    
    // P2: Initialize room modification state
    setModifiedRoomIds(roomIds);
    setShowRoomModification(false);
    
    // Fetch available rooms for potential room change
    fetchAvailableRoomsForCheckIn(booking);
    
    setShowCheckIn(true);
  };

  // P2: Fetch available rooms for check-in (for room modification)
  const fetchAvailableRoomsForCheckIn = async (booking) => {
    try {
      const response = await axios.get(`${API}/rooms/available`, {
        params: {
          check_in: booking.check_in_date,
          check_out: booking.check_out_date,
          exclude_booking_id: booking.id  // Exclude current booking to show currently assigned rooms
        }
      });
      
      // Combine available rooms with currently assigned rooms
      const currentRooms = rooms.filter(r => booking.room_ids.includes(r.id));
      const availableRooms = response.data;
      
      // Merge and deduplicate
      const allAvailableRooms = [...currentRooms, ...availableRooms].reduce((acc, room) => {
        if (!acc.find(r => r.id === room.id)) {
          acc.push(room);
        }
        return acc;
      }, []);
      
      setAvailableRoomsForCheckIn(allAvailableRooms);
    } catch (error) {
      console.error("Failed to fetch available rooms:", error);
      toast.error("Could not load available rooms");
    }
  };

  // P2: Toggle room modification mode
  const toggleRoomModification = () => {
    setShowRoomModification(!showRoomModification);
  };

  // P2: Update modified room selection
  const handleRoomChange = (oldRoomId, newRoomId) => {
    const newRoomIds = modifiedRoomIds.map(id => id === oldRoomId ? newRoomId : id);
    setModifiedRoomIds(newRoomIds);
    
    // Update room-guest mapping to reflect new room
    const newRoom = availableRoomsForCheckIn.find(r => r.id === newRoomId);
    if (newRoom) {
      setRoomGuestMapping(prev => prev.map(room => {
        if (room.room_id === oldRoomId) {
          return {
            ...room,
            room_id: newRoom.id,
            room_number: newRoom.room_number,
            room_category: newRoom.category,
            charge_category: room.charge_category === "Def Civ" ? "Def Civ" : newRoom.category
          };
        }
        return room;
      }));
    }
  };

  // P2: Apply room changes to booking before check-in
  const applyRoomChanges = async () => {
    try {
      // Update booking with new room assignments
      await axios.put(`${API}/bookings/${selectedBooking.id}/update-rooms`, {
        room_ids: modifiedRoomIds
      });
      
      toast.success("Room assignments updated");
      setShowRoomModification(false);
      
      // Refresh booking data
      const updatedBooking = await axios.get(`${API}/bookings/${selectedBooking.id}`);
      setSelectedBooking(updatedBooking.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update room assignments");
    }
  };

  const openCheckOutDialog = (booking) => {
    setSelectedBooking(booking);
    setShowCheckOut(true);
  };

  const canCheckInToday = (booking) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const checkInDate = new Date(booking.check_in_date);
    checkInDate.setHours(0, 0, 0, 0);
    
    return today >= checkInDate;
  };

  const handleCancel = async () => {
    try {
      await axios.post(`${API}/bookings/cancel`, {
        booking_id: selectedBooking.id,
        reason: actionForm.reason,
        refund_amount: refundInfo?.refund_amount ?? 0
      });
      toast.success(`Booking cancelled. Refund: ₹${refundInfo?.refund_amount ?? 0}`);
      setShowCancel(false);
      setSelectedBooking(null);
      setRefundInfo(null);
      setActionForm({ staff_id: "", notes: "", final_payment: 0, payment_mode: "", reason: "", refund_amount: 0, extra_beds: 0,
        extra_beds_checkout: 0, extra_bed_days: 0,
        guest_contact: "", guest_age: "", guest_sex: "", guest_address: "", identity_card_number: "",
        guest_service_status: "", service_type: "", command_hq: "",
        bank_name: "", bank_ifsc: "", bank_account: "", upi_id: "", upi_phone: "", family_members: [] });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Cancellation failed");
    }
  };

  const handleSearchGuestHistory = async () => {
    if (!guestHistorySearch.phone && !guestHistorySearch.army_number) {
      toast.error("Please enter phone number or army number");
      return;
    }

    setLoadingHistory(true);
    try {
      const params = {};
      if (guestHistorySearch.phone) {
        params.phone_number = guestHistorySearch.phone;
      }
      if (guestHistorySearch.army_number) {
        params.army_number = guestHistorySearch.army_number;
      }

      const response = await axios.get(`${API}/bookings/guest-history`, { params });
      
      if (response.data.found) {
        setGuestHistoryData(response.data);
        toast.success(`Found ${response.data.statistics.total_bookings} booking(s)`);
      } else {
        setGuestHistoryData(null);
        toast.info("No booking history found for this guest");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to fetch guest history");
      setGuestHistoryData(null);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handlePrintBookingSlips = () => {
    // Get confirmed or checked-in bookings
    const eligibleBookings = bookings.filter(b => 
      b.status === "confirmed" || b.status === "checked_in"
    );
    
    if (eligibleBookings.length === 0) {
      toast.error("No confirmed or checked-in bookings to print");
      return;
    }
    
    try {
      const result = generateBookingSlips(eligibleBookings);
      showPDFNotification(result, `Generated ${result.count} booking slip(s)`);
    } catch (error) {
      toast.error("Failed to generate booking slips");
      console.error(error);
    }
  };

  const resetGuestHistorySearch = () => {
    setGuestHistorySearch({ phone: "", army_number: "" });
    setGuestHistoryData(null);
  };

  // Helper function for PDF download notification
  const showPDFNotification = (result, title = "PDF Generated") => {
    toast.success(
      <div className="flex flex-col gap-2">
        <div className="font-semibold">
          ✓ {title}
        </div>
        <div className="text-sm text-gray-600">
          Saved to Downloads: {result.filename}
        </div>
        <button
          onClick={() => {
            window.open(result.blobUrl, '_blank');
            toast.dismiss();
          }}
          className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          📄 Open PDF
        </button>
      </div>,
      {
        duration: 10000,
        style: { minWidth: '350px' }
      }
    );
  };


  const handleProcessRefund = async (refund) => {
    setRefundAction(refund);
    setRefundForm({ transaction_ref: "", refund_date: format(new Date(), "yyyy-MM-dd"), notes: "" });
  };

  const handleConfirmRefund = async () => {
    if (!refundForm.transaction_ref) {
      toast.error("Please enter transaction reference");
      return;
    }
    try {
      await axios.put(`${API}/refunds/${refundAction.id}`, {
        status: "completed",
        transaction_ref: refundForm.transaction_ref,
        refund_date: refundForm.refund_date,
        notes: refundForm.notes
      });
      toast.success("Refund marked as completed!");
      setRefundAction(null);
      fetchPendingRefunds();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to process refund");
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      confirmed: "badge-info",
      checked_in: "badge-success",
      checked_out: "badge-warning",
      cancelled: "badge-danger"
    };
    const labels = {
      confirmed: "Confirmed",
      checked_in: "Checked In",
      checked_out: "Checked Out",
      cancelled: "Cancelled"
    };
    return <Badge className={styles[status]}>{labels[status]}</Badge>;
  };

  const selectedRooms = availableRooms.filter(r => bookingForm.room_ids.includes(r.id));
  const calculateTotalRate = () => {
    return selectedRooms.reduce((total, room) => {
      let rate;
      const isDefCiv = bookingForm.guest_rank === "Def Civ";
      if (room.category === "Cat I") {
        rate = isDefCiv ? (settings?.def_civ_cat_i_rate ?? settings?.cat_i_rate) : settings?.cat_i_rate;
      } else {
        rate = isDefCiv ? (settings?.def_civ_cat_ii_rate ?? settings?.cat_ii_rate) : settings?.cat_ii_rate;
      }
      return total + (rate || 0);
    }, 0);
  };
  const totalRoomRate = calculateTotalRate();
  const nights = bookingForm.check_in_date && bookingForm.check_out_date
    ? Math.ceil((bookingForm.check_out_date - bookingForm.check_in_date) / (1000 * 60 * 60 * 24))
    : 0;

  const ranks = settings?.ranks || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="bookings-loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="bookings-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-800" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Bookings
          </h1>
          <p className="text-slate-500 mt-1">Manage reservations, check-ins & check-outs</p>
        </div>
        <div className="flex gap-3 flex-wrap">
          <Button
            variant="outline"
            onClick={() => { fetchPendingRefunds(); setShowPendingRefunds(true); }}
            className="flex items-center gap-2 text-amber-700 border-amber-300 hover:bg-amber-50"
            data-testid="pending-refunds-btn"
          >
            <ArrowCounterClockwise size={20} />
            Pending Refunds
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowGuestHistory(true)}
            className="flex items-center gap-2 text-indigo-700 border-indigo-300 hover:bg-indigo-50"
            data-testid="guest-history-btn"
          >
            <MagnifyingGlass size={20} />
            Guest History
          </Button>
          <Button
            variant="outline"
            onClick={handlePrintBookingSlips}
            className="flex items-center gap-2 text-green-700 border-green-300 hover:bg-green-50"
            data-testid="print-slips-btn"
          >
            <FilePdf size={20} />
            Print Booking Slips
          </Button>
          <Button
            onClick={() => setShowNewBooking(true)}
            className="earms-btn-primary flex items-center gap-2"
            data-testid="new-booking-btn"
          >
            <Plus size={20} />
            New Booking
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="earms-card">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <MagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
              <Input
                placeholder="Search by guest, booking # or room..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 earms-input"
                data-testid="search-bookings"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-48" data-testid="status-filter">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="confirmed">Confirmed</SelectItem>
                <SelectItem value="checked_in">Checked In</SelectItem>
                <SelectItem value="checked_out">Checked Out</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Bookings List */}
      <Card className="earms-card">
        <CardContent className="p-0">
          {filteredBookings.length === 0 ? (
            <div className="text-center py-12" data-testid="no-bookings">
              <CalendarCheck size={48} className="mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No bookings found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table" data-testid="bookings-table">
                <thead>
                  <tr>
                    <th>Booking #</th>
                    <th>Guest</th>
                    <th>Room</th>
                    <th>Check-in</th>
                    <th>Check-out</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBookings.map((booking) => (
                    <tr key={booking.id} data-testid={`booking-row-${booking.id}`}>
                      <td className="font-medium text-slate-800">{booking.booking_number}</td>
                      <td>
                        <div>{booking.guest_name}</div>
                        {booking.guest_rank && <div className="text-xs text-slate-500">{booking.guest_rank}{booking.guest_service_status ? ` (${booking.guest_service_status})` : ""}</div>}
                      </td>
                      <td>
                        <Badge variant="outline">{getRoomDisplay(booking)}</Badge>
                        <span className="text-xs text-slate-500 ml-1">{getRoomCategories(booking)}</span>
                      </td>
                      <td>{format(parseISO(booking.check_in_date), "dd MMM yyyy")}</td>
                      <td>{format(parseISO(booking.check_out_date), "dd MMM yyyy")}</td>
                      <td>
                        <span className="font-medium">₹{booking.total_amount}</span>
                        {booking.balance_amount > 0 && (
                          <span className="text-xs text-amber-600 block">Due: ₹{booking.balance_amount}</span>
                        )}
                      </td>
                      <td>{getStatusBadge(booking.status)}</td>
                      <td>
                        <div className="flex gap-2">
                          {booking.status === "confirmed" && (
                            <>
                              <Button size="sm" variant="outline"
                                onClick={() => openCheckInDialog(booking)}
                                disabled={!canCheckInToday(booking)}
                                className="text-emerald-600 border-emerald-200 hover:bg-emerald-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                title={!canCheckInToday(booking) ? `Check-in available from ${new Date(booking.check_in_date).toLocaleDateString('en-IN')}` : 'Check In'}
                                data-testid={`checkin-btn-${booking.id}`}>
                                <SignIn size={16} className="mr-1" />Check In
                              </Button>
                              <Button size="sm" variant="outline"
                                onClick={() => openCancelDialog(booking)}
                                className="text-red-600 border-red-200 hover:bg-red-50"
                                data-testid={`cancel-btn-${booking.id}`}>
                                <X size={16} />
                              </Button>
                            </>
                          )}
                          {booking.status === "checked_in" && (
                            <>
                              <Button size="sm" variant="outline"
                                onClick={() => { setSelectedBooking(booking); setShowCheckOut(true); }}
                                className="text-blue-600 border-blue-200 hover:bg-blue-50"
                                data-testid={`checkout-btn-${booking.id}`}>
                                <SignOut size={16} className="mr-1" />Check Out
                              </Button>
                              <Button size="sm" variant="outline"
                                onClick={() => {
                                  const result = generateCheckoutReceipt(booking, settings);
                                  showPDFNotification(result, "Receipt Generated");
                                }}
                                className="text-purple-600 border-purple-200 hover:bg-purple-50"
                                title="Print Bill"
                                data-testid={`print-bill-btn-${booking.id}`}>
                                <FilePdf size={16} className="mr-1" />Bill
                              </Button>
                              <Button size="sm" variant="outline"
                                onClick={() => openCancelDialog(booking)}
                                className="text-red-600 border-red-200 hover:bg-red-50"
                                data-testid={`cancel-btn-${booking.id}`}>
                                <X size={16} />
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
      <Dialog open={showNewBooking} onOpenChange={(open) => { setShowNewBooking(open); if (!open) resetBookingForm(); }}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto" data-testid="new-booking-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CalendarCheck size={24} className="text-blue-500" />
              New Booking
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Section 1: Guest Details */}
            <div>
              <h3 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-blue-500 text-white text-sm flex items-center justify-center">1</div>
                <User size={18} /> Guest Details
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Rank</Label>
                  {ranks.length > 0 ? (
                    <Select value={bookingForm.guest_rank} onValueChange={(v) => setBookingForm({...bookingForm, guest_rank: v})}>
                      <SelectTrigger className="earms-input mt-1" data-testid="select-guest-rank">
                        <SelectValue placeholder="Select rank" />
                      </SelectTrigger>
                      <SelectContent>
                        {ranks.map(rank => <SelectItem key={rank} value={rank}>{rank}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  ) : (
                    <Input value={bookingForm.guest_rank} onChange={(e) => setBookingForm({...bookingForm, guest_rank: e.target.value})} onFocus={(e) => e.target.select()} placeholder="e.g., Havildar" className="earms-input mt-1" data-testid="input-guest-rank" />
                  )}
                </div>
                <div>
                  <Label>Guest Name *</Label>
                  <Input value={bookingForm.guest_name} onChange={(e) => setBookingForm({...bookingForm, guest_name: e.target.value})} onFocus={(e) => e.target.select()} placeholder="Full name" className="earms-input mt-1" data-testid="input-guest-name" />
                </div>
                <div>
                  <Label>Mobile Number</Label>
                  <Input 
                    value={bookingForm.guest_contact} 
                    onChange={(e) => handleBookingPhoneChange(e.target.value)} 
                    onFocus={(e) => e.target.select()} 
                    placeholder="10-digit mobile number" 
                    className={`earms-input mt-1 ${bookingPhoneError ? 'border-red-500' : ''}`}
                    data-testid="input-guest-contact" 
                    maxLength={11}
                  />
                  {bookingPhoneError && <p className="text-xs text-red-500 mt-1">{bookingPhoneError}</p>}
                  <p className="text-xs text-slate-500 mt-1">For WhatsApp booking confirmation</p>
                </div>
                <div>
                  <Label>Army / Service Number</Label>
                  <Input value={bookingForm.army_number} onChange={(e) => setBookingForm({...bookingForm, army_number: toUpperCase(e.target.value)})} onFocus={(e) => e.target.select()} placeholder="e.g., 15814432-F" className="earms-input mt-1" data-testid="input-army-number" />
                </div>
                <div>
                  <Label>Unit Name</Label>
                  <Input value={bookingForm.guest_unit} onChange={(e) => setBookingForm({...bookingForm, guest_unit: e.target.value})} onFocus={(e) => e.target.select()} placeholder="e.g., 2 PARA" className="earms-input mt-1" data-testid="input-guest-unit" />
                </div>
                <div>
                  <Label>Number of Rooms *</Label>
                  <Input type="number" min="1" value={bookingForm.num_rooms} onChange={(e) => setBookingForm({...bookingForm, num_rooms: parseInt(e.target.value) || 1})} onFocus={(e) => e.target.select()} className="earms-input mt-1" data-testid="input-num-rooms" />
                </div>
              </div>
            </div>

            {/* Section 2: Stay Dates */}
            <div>
              <h3 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-blue-500 text-white text-sm flex items-center justify-center">2</div>
                <CalendarBlank size={18} /> Stay Dates
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Check-in Date *</Label>
                  <Popover open={checkInOpen} onOpenChange={setCheckInOpen}>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="w-full earms-input justify-start mt-1" data-testid="select-checkin-date">
                        <CalendarBlank className="mr-2" size={18} />
                        {bookingForm.check_in_date ? format(bookingForm.check_in_date, "dd MMM yyyy") : "Select date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={bookingForm.check_in_date}
                        onSelect={(date) => {
                          setBookingForm({...bookingForm, check_in_date: date, check_out_date: null, room_ids: []});
                          setCheckInOpen(false);
                        }}
                        disabled={(date) => {
                          // P3: Allow past dates in migration mode
                          const migrationMode = localStorage.getItem("migration_mode") === "true";
                          if (migrationMode) return false; // No restriction in migration mode
                          return date < new Date(new Date().setHours(0,0,0,0));
                        }}
                      />
                    </PopoverContent>
                  </Popover>
                </div>
                <div>
                  <Label>Check-out Date *</Label>
                  <Popover open={checkOutOpen} onOpenChange={setCheckOutOpen}>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="w-full earms-input justify-start mt-1" data-testid="select-checkout-date" disabled={!bookingForm.check_in_date}>
                        <CalendarBlank className="mr-2" size={18} />
                        {bookingForm.check_out_date ? format(bookingForm.check_out_date, "dd MMM yyyy") : "Select date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={bookingForm.check_out_date}
                        onSelect={(date) => {
                          setBookingForm({...bookingForm, check_out_date: date, room_ids: []});
                          setCheckOutOpen(false);
                        }}
                        disabled={(date) => date <= (bookingForm.check_in_date || new Date())}
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
              {bookingForm.check_in_date && bookingForm.check_out_date && (
                <div className="mt-2 p-2 bg-blue-50 rounded-lg text-sm text-blue-700">
                  Stay Duration: {nights} night(s)
                </div>
              )}
            </div>

            {/* Section 3: Room Selection */}
            <div>
              <h3 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <div className={`w-6 h-6 rounded-full text-white text-sm flex items-center justify-center ${bookingForm.check_in_date && bookingForm.check_out_date ? 'bg-blue-500' : 'bg-slate-300'}`}>3</div>
                <Bed size={18} /> Room Selection
              </h3>
              {!bookingForm.check_in_date || !bookingForm.check_out_date ? (
                <div className="p-4 bg-slate-50 rounded-xl text-center text-slate-500">
                  Please select check-in and check-out dates first
                </div>
              ) : loadingRooms ? (
                <div className="p-4 bg-slate-50 rounded-xl text-center text-slate-500 flex items-center justify-center gap-2">
                  <SpinnerGap size={20} className="animate-spin" />
                  Checking room availability...
                </div>
              ) : availableRooms.length === 0 ? (
                <div className="p-4 bg-red-50 rounded-xl text-center text-red-600">
                  No rooms available for selected dates. Please try different dates.
                </div>
              ) : availableRooms.length < bookingForm.num_rooms ? (
                <div className="p-4 bg-amber-50 rounded-xl text-center text-amber-600">
                  Only {availableRooms.length} room(s) available. You requested {bookingForm.num_rooms} room(s).
                </div>
              ) : (
                <>
                  <div className="p-3 bg-blue-50 rounded-lg mb-3">
                    <p className="text-sm text-blue-700 font-medium">
                      Select {bookingForm.num_rooms} room(s) — {bookingForm.room_ids.length} of {bookingForm.num_rooms} selected
                      {bookingForm.guest_rank === "Def Civ" && <span className="ml-2 text-orange-600 font-semibold">(Def Civ rates apply)</span>}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-56 overflow-y-auto p-1">
                    {availableRooms.map((room) => {
                      const isSelected = bookingForm.room_ids.includes(room.id);
                      const isDefCiv = bookingForm.guest_rank === "Def Civ";
                      const rate = room.category === "Cat I"
                        ? (isDefCiv ? (settings?.def_civ_cat_i_rate ?? settings?.cat_i_rate) : settings?.cat_i_rate)
                        : (isDefCiv ? (settings?.def_civ_cat_ii_rate ?? settings?.cat_ii_rate) : settings?.cat_ii_rate);
                      return (
                        <div
                          key={room.id}
                          onClick={() => toggleRoomSelection(room.id)}
                          className={`p-3 rounded-xl border-2 cursor-pointer transition-all ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-blue-300 bg-white'}`}
                          data-testid={`room-option-${room.id}`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-bold text-slate-800">{room.room_number}</span>
                            {isSelected && <CheckSquare size={20} className="text-blue-500" weight="fill" />}
                          </div>
                          <div className="text-xs text-slate-500">{room.category}</div>
                          <div className="text-sm font-medium text-emerald-600">₹{rate}/night</div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-3">
                    <div className="p-3 bg-blue-50 rounded-lg text-center">
                      <div className="text-sm text-blue-600">Cat I Available</div>
                      <div className="text-xl font-bold text-blue-800">{availableRooms.filter(r => r.category === "Cat I").length}</div>
                    </div>
                    <div className="p-3 bg-purple-50 rounded-lg text-center">
                      <div className="text-sm text-purple-600">Cat II Available</div>
                      <div className="text-xl font-bold text-purple-800">{availableRooms.filter(r => r.category === "Cat II").length}</div>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Section 4: Advance Amount + Payment */}
            {bookingForm.room_ids.length === bookingForm.num_rooms && bookingForm.room_ids.length > 0 && (
              <div>
                <h3 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-blue-500 text-white text-sm flex items-center justify-center">4</div>
                  <CurrencyInr size={18} /> Advance Payment
                </h3>

                {/* Bank / UPI Details - ALWAYS VISIBLE (for refunds if cancelled) */}
                <div className="p-4 bg-blue-50 rounded-xl border border-blue-200 mb-4">
                  <h4 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
                    <Bank size={16} className="text-blue-600" /> Bank / UPI Details (for refund if cancelled)
                  </h4>
                  <p className="text-xs text-blue-700 mb-3">These details will be used for refunds in case of cancellation</p>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>Bank Name</Label>
                      <Input value={bookingForm.bank_name} onChange={(e) => setBookingForm({...bookingForm, bank_name: e.target.value})}
                        onFocus={(e) => e.target.select()} placeholder="e.g., State Bank of India" className="earms-input mt-1 bg-white" data-testid="input-booking-bank-name" />
                    </div>
                    <div>
                      <Label>IFSC Code</Label>
                      <Input 
                        value={bookingForm.bank_ifsc} 
                        onChange={(e) => {
                          const value = toUpperCase(e.target.value);
                          setBookingForm({...bookingForm, bank_ifsc: value});
                          setBookingIfscError(value && !validateIFSC(value) ? "Invalid IFSC format (e.g., SBIN0001234)" : "");
                        }}
                        onFocus={(e) => e.target.select()} 
                        placeholder="e.g., SBIN0001234" 
                        className={`earms-input mt-1 bg-white ${bookingIfscError ? 'border-red-500' : ''}`}
                        data-testid="input-booking-bank-ifsc" 
                        maxLength={11}
                      />
                      {bookingIfscError && <p className="text-xs text-red-500 mt-1">{bookingIfscError}</p>}
                    </div>
                    <div>
                      <Label>Account Number</Label>
                      <Input value={bookingForm.bank_account} onChange={(e) => setBookingForm({...bookingForm, bank_account: e.target.value})}
                        onFocus={(e) => e.target.select()} placeholder="Bank account number" className="earms-input mt-1 bg-white" data-testid="input-booking-bank-account" />
                    </div>
                    <div>
                      <Label>UPI ID</Label>
                      <Input value={bookingForm.upi_id} onChange={(e) => setBookingForm({...bookingForm, upi_id: e.target.value})}
                        onFocus={(e) => e.target.select()} placeholder="e.g., name@upi" className="earms-input mt-1 bg-white" data-testid="input-booking-upi-id" />
                    </div>
                    <div>
                      <Label>UPI Phone</Label>
                      <Input 
                        value={bookingForm.upi_phone} 
                        onChange={(e) => {
                          const formatted = formatIndianPhone(e.target.value);
                          setBookingForm({...bookingForm, upi_phone: formatted});
                          setUpiPhoneError(formatted && !validateIndianPhone(formatted) ? "Enter a valid 10-digit Indian mobile number" : "");
                        }}
                        onFocus={(e) => e.target.select()} 
                        placeholder="10-digit mobile" 
                        className={`earms-input mt-1 bg-white ${upiPhoneError ? 'border-red-500' : ''}`}
                        data-testid="input-booking-upi-phone" 
                        maxLength={11}
                      />
                      {upiPhoneError && <p className="text-xs text-red-500 mt-1">{upiPhoneError}</p>}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Advance Paid (₹)</Label>
                    <Input
                      type="number"
                      value={bookingForm.advance_paid}
                      onChange={(e) => setBookingForm({...bookingForm, advance_paid: parseFloat(e.target.value) || 0})}
                      onFocus={(e) => e.target.select()}
                      className="earms-input mt-1"
                      data-testid="input-advance"
                    />
                    <p className="text-xs text-slate-500 mt-1">Default: ₹{settings?.default_advance_amount || 400} × {bookingForm.num_rooms} room(s)</p>
                  </div>
                  <div>
                    <Label>Payment Mode *</Label>
                    <Select value={bookingForm.payment_mode} onValueChange={(v) => setBookingForm({...bookingForm, payment_mode: v, payment_id: ""})}>
                      <SelectTrigger className="earms-input mt-1" data-testid="select-payment-mode">
                        <SelectValue placeholder="Select mode" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="upi">UPI</SelectItem>
                        <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                        <SelectItem value="card">Card</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Simplified payment detail fields (bank details already captured above) */}
                {bookingForm.payment_mode === "cash" && (
                  <div className="mt-3">
                    <Label>Cash Receipt Number *</Label>
                    <Input value={bookingForm.payment_id} onChange={(e) => setBookingForm({...bookingForm, payment_id: e.target.value})}
                      onFocus={(e) => e.target.select()} placeholder="Receipt / Voucher number" className="earms-input mt-1" data-testid="input-payment-id" />
                  </div>
                )}

                {bookingForm.payment_mode === "card" && (
                  <div className="mt-3">
                    <Label>Card Transaction Reference *</Label>
                    <Input value={bookingForm.payment_id} onChange={(e) => setBookingForm({...bookingForm, payment_id: e.target.value})}
                      onFocus={(e) => e.target.select()} placeholder="Card approval / transaction ID" className="earms-input mt-1" data-testid="input-payment-id" />
                  </div>
                )}

                {bookingForm.payment_mode === "upi" && (
                  <div className="mt-3">
                    <Label>UPI Transaction ID *</Label>
                    <Input value={bookingForm.payment_id} onChange={(e) => setBookingForm({...bookingForm, payment_id: e.target.value})}
                      onFocus={(e) => e.target.select()} placeholder="UPI Transaction/Reference ID" className="earms-input mt-1" data-testid="input-upi-transaction-id" />
                  </div>
                )}

                {bookingForm.payment_mode === "bank_transfer" && (
                  <div className="mt-3">
                    <Label>Bank Transfer Reference *</Label>
                    <Input value={bookingForm.payment_id} onChange={(e) => setBookingForm({...bookingForm, payment_id: e.target.value})}
                      onFocus={(e) => e.target.select()} placeholder="NEFT/IMPS/RTGS reference" className="earms-input mt-1" data-testid="input-payment-id" />
                  </div>
                )}

                {/* Booking amount summary */}
                {selectedRooms.length > 0 && (
                  <div className="mt-4 p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-sm">
                    <div className="flex justify-between mb-1">
                      <span className="text-slate-600">Rooms: {selectedRooms.map(r => r.room_number).join(", ")}</span>
                      <span className="font-medium">₹{totalRoomRate}/night × {nights} nights</span>
                    </div>
                    <div className="flex justify-between font-semibold text-amber-700 border-t border-emerald-200 pt-1 mt-1">
                      <span>Balance at Checkout:</span>
                      <span>₹{(totalRoomRate * nights) - bookingForm.advance_paid}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewBooking(false)} data-testid="cancel-booking-form">Cancel</Button>
            <Button
              onClick={handleCreateBooking}
              className="earms-btn-primary"
              data-testid="submit-booking"
              disabled={!bookingForm.guest_name || bookingForm.room_ids.length !== bookingForm.num_rooms || !bookingForm.check_in_date || !bookingForm.check_out_date || !bookingForm.payment_mode || !isPaymentDetailsFilled()}
            >
              Create Booking{bookingForm.num_rooms > 1 ? ` (${bookingForm.num_rooms} Rooms)` : ''}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== CHECK-IN DIALOG ===== */}
      <Dialog open={showCheckIn} onOpenChange={(open) => { 
        setShowCheckIn(open); 
        if (!open) { 
          setSelectedBooking(null); 
          resetActionForm(); 
          setPhoneError(""); 
        } else if (selectedBooking?.guest_contact) {
          // Pre-populate phone from booking data
          const phoneOnly = selectedBooking.guest_contact.replace(/^\+91\s*/, "").replace(/\s/g, "");
          const formatted = formatIndianPhone(phoneOnly);
          setActionForm(prev => ({ ...prev, guest_contact: formatted }));
        }
      }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="checkin-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <SignIn size={24} className="text-emerald-500" />
              Check-In Guest
            </DialogTitle>
          </DialogHeader>
          {selectedBooking && (
            <div className="space-y-5 py-4">

              {/* Booking Summary */}
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                <p className="font-semibold text-emerald-800 text-lg">{selectedBooking.guest_name}</p>
                {selectedBooking.guest_rank && <p className="text-sm text-emerald-700">{selectedBooking.guest_rank}{selectedBooking.guest_unit ? ` · ${selectedBooking.guest_unit}` : ""}</p>}
                <p className="text-sm text-emerald-600">Room {getRoomDisplay(selectedBooking)} · {getRoomCategories(selectedBooking)}</p>
                <p className="text-sm text-emerald-600">{format(parseISO(selectedBooking.check_in_date), "dd MMM yyyy")} → {format(parseISO(selectedBooking.check_out_date), "dd MMM yyyy")}</p>
              </div>

              {/* Staff Member */}
              <div>
                <Label>Staff Member *</Label>
                <Select value={actionForm.staff_id} onValueChange={(v) => setActionForm({...actionForm, staff_id: v})}>
                  <SelectTrigger className="earms-input mt-1" data-testid="select-staff-checkin">
                    <SelectValue placeholder="Select staff" />
                  </SelectTrigger>
                  <SelectContent>
                    {staff.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name} ({s.staff_type})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Extra Beds */}
              <div className="p-3 bg-amber-50 rounded-xl border border-amber-200">
                <Label className="font-semibold text-amber-800">Extra Beds Required</Label>
                <p className="text-xs text-amber-600 mb-2">₹75 per extra bed — added to final bill</p>
                <div className="flex items-center gap-3">
                  <Input type="number" min="0" max="5" value={actionForm.extra_beds}
                    onChange={(e) => setActionForm({...actionForm, extra_beds: parseInt(e.target.value) || 0})}
                    onFocus={(e) => e.target.select()} className="earms-input w-24" data-testid="input-extra-beds-checkin" />
                  {actionForm.extra_beds > 0 && <span className="text-sm font-medium text-amber-700">Charge: ₹{actionForm.extra_beds * 75}</span>}
                </div>
              </div>

              {/* Personal Details */}
              <div>
                <h4 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <User size={16} className="text-blue-500" /> Personal Details
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Mobile Number</Label>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-sm font-medium text-slate-600 bg-slate-100 border border-slate-200 px-2 py-2 rounded-md">+91</span>
                      <Input value={actionForm.guest_contact} onChange={(e) => handleCheckinPhoneChange(e.target.value)}
                        onFocus={(e) => e.target.select()} placeholder="XXXXX XXXXX"
                        className={`earms-input flex-1 ${phoneError ? "border-red-400" : ""}`} maxLength={11} data-testid="input-checkin-phone" />
                    </div>
                    {phoneError && <p className="text-xs text-red-500 mt-1">{phoneError}</p>}
                  </div>
                  <div>
                    <Label>Identity Card No</Label>
                    <Input value={actionForm.identity_card_number} onChange={(e) => setActionForm({...actionForm, identity_card_number: e.target.value})}
                      onFocus={(e) => e.target.select()} placeholder="e.g., F223529" className="earms-input mt-1" data-testid="input-checkin-identity-card" />
                  </div>
                  <div>
                    <Label>Age</Label>
                    <Input type="number" min="18" max="100" value={actionForm.guest_age}
                      onChange={(e) => setActionForm({...actionForm, guest_age: e.target.value})}
                      onFocus={(e) => e.target.select()} className="earms-input mt-1" data-testid="input-checkin-age" />
                  </div>
                  <div>
                    <Label>Sex</Label>
                    <Select value={actionForm.guest_sex} onValueChange={(v) => setActionForm({...actionForm, guest_sex: v})}>
                      <SelectTrigger className="earms-input mt-1" data-testid="select-checkin-sex"><SelectValue placeholder="Select" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="M">Male</SelectItem>
                        <SelectItem value="F">Female</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Service Status</Label>
                    <Select value={actionForm.guest_service_status} onValueChange={(v) => setActionForm({...actionForm, guest_service_status: v})}>
                      <SelectTrigger className="earms-input mt-1" data-testid="select-checkin-service-status"><SelectValue placeholder="Serving / Retired" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Serving">Serving</SelectItem>
                        <SelectItem value="Retired">Retired</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Address</Label>
                    <Input value={actionForm.guest_address} onChange={(e) => setActionForm({...actionForm, guest_address: e.target.value})}
                      onFocus={(e) => e.target.select()} placeholder="Permanent/Contact address" className="earms-input mt-1" data-testid="input-checkin-address" />
                  </div>
                </div>
              </div>

              {/* Service Details */}
              <div>
                <h4 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <CheckSquare size={16} className="text-blue-500" weight="fill" /> Service Details
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Type of Service</Label>
                    <Select value={actionForm.service_type} onValueChange={(v) => setActionForm({...actionForm, service_type: v, command_hq: ""})}>
                      <SelectTrigger className="earms-input mt-1" data-testid="select-checkin-service-type"><SelectValue placeholder="Select service" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Army">Army</SelectItem>
                        <SelectItem value="Air Force">Air Force</SelectItem>
                        <SelectItem value="Navy">Navy</SelectItem>
                        <SelectItem value="SFC">SFC</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {actionForm.service_type === "Army" && (
                    <div>
                      <Label>Command HQ</Label>
                      <Select value={actionForm.command_hq} onValueChange={(v) => setActionForm({...actionForm, command_hq: v})}>
                        <SelectTrigger className="earms-input mt-1" data-testid="select-checkin-command-hq"><SelectValue placeholder="Select command" /></SelectTrigger>
                        <SelectContent>
                          {["Northern Command","Eastern Command","Western Command","Southern Command","South Western Command","Central Command","ARTRAC","SFC","Army HQ"].map(c => (
                            <SelectItem key={c} value={c}>{c}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
              </div>

              {/* P2: Room Assignment Modification */}
              <div className="p-4 bg-amber-50 rounded-xl border border-amber-300">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-semibold text-amber-800 flex items-center gap-2">
                    <ArrowsClockwise size={18} className="text-amber-600" weight="fill" /> Room Assignments
                  </h4>
                  <Button
                    type="button"
                    variant={showRoomModification ? "default" : "outline"}
                    size="sm"
                    onClick={toggleRoomModification}
                    className="text-xs"
                  >
                    {showRoomModification ? "Cancel Changes" : "Modify Rooms"}
                  </Button>
                </div>

                {!showRoomModification ? (
                  // Show current room assignments
                  <div className="space-y-2">
                    <p className="text-xs text-amber-700 mb-2">Current room assignments for this booking:</p>
                    <div className="grid grid-cols-2 gap-2">
                      {roomGuestMapping.map((room, idx) => (
                        <div key={idx} className="p-2 bg-white rounded border border-amber-200 text-sm">
                          <span className="font-semibold">Room {room.room_number}</span>
                          <span className="text-slate-500 ml-2">({room.room_category})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  // Show room modification interface
                  <div className="space-y-3">
                    <p className="text-xs text-amber-700 mb-2">
                      <WarningCircle size={14} className="inline mr-1" weight="fill" />
                      Select new rooms from available options. Only vacant rooms for the booking dates are shown.
                    </p>
                    
                    {roomGuestMapping.map((room, idx) => {
                      const currentRoomId = modifiedRoomIds[idx] || room.room_id;
                      const isChanged = currentRoomId !== selectedBooking.room_ids[idx];
                      
                      return (
                        <div key={idx} className={`p-3 rounded-lg border ${isChanged ? 'bg-emerald-50 border-emerald-300' : 'bg-white border-slate-200'}`}>
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <Label className="text-xs font-semibold">
                                Room {idx + 1} Assignment {isChanged && <span className="text-emerald-600 ml-1">(Changed)</span>}
                              </Label>
                              <Select 
                                value={currentRoomId} 
                                onValueChange={(newRoomId) => handleRoomChange(currentRoomId, newRoomId)}
                              >
                                <SelectTrigger className="earms-input mt-1 text-sm h-9">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {availableRoomsForCheckIn.map(r => (
                                    <SelectItem key={r.id} value={r.id}>
                                      Room {r.room_number} ({r.category}) - {r.status === "AVAILABLE" ? "✓ Available" : "Currently Assigned"}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    
                    <Button
                      type="button"
                      onClick={applyRoomChanges}
                      className="w-full bg-emerald-500 hover:bg-emerald-600 text-sm"
                      disabled={JSON.stringify(modifiedRoomIds) === JSON.stringify(selectedBooking.room_ids)}
                    >
                      Apply Room Changes
                    </Button>
                  </div>
                )}
              </div>

              {/* Room Assignment - REDESIGNED with inline family members */}
              <div className="p-4 bg-blue-50 border-2 border-blue-300 rounded-xl">
                <h4 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                  <Bed size={18} className="text-blue-600" weight="fill" /> Room-Wise Guest Assignment
                </h4>
                <p className="text-xs text-blue-700 mb-4 bg-blue-100 p-2 rounded-md">
                  <WarningCircle size={14} className="inline mr-1" weight="fill" />
                  Assign <strong>Self</strong> to one room and add family members to each room. If any family member lacks a <strong>Dependent Card</strong>, that room will be charged at <strong>Def Civ rates</strong>.
                </p>
                
                {roomGuestMapping.map((room, roomIdx) => {
                  const guestCount = (room.has_self ? 1 : 0) + room.family_members.length;
                  
                  return (
                    <div key={roomIdx} className="mb-4 p-4 bg-white rounded-lg border border-blue-200">
                      <div className="flex justify-between items-center mb-3">
                        <div>
                          <h5 className="font-bold text-slate-800">Room {room.room_number}</h5>
                          <p className="text-xs text-slate-600">
                            {room.room_category} → Charging at: 
                            <span className={room.charge_category === "Def Civ" ? "text-red-600 font-bold ml-1" : "text-emerald-600 font-bold ml-1"}>
                              {room.charge_category}
                            </span>
                          </p>
                        </div>
                        <Badge variant={room.charge_category === "Def Civ" ? "destructive" : "default"}>
                          {guestCount} Guest{guestCount !== 1 ? "s" : ""}
                        </Badge>
                      </div>

                      {/* Self Assignment (Checkbox) */}
                      <div className="mb-3 p-2 bg-slate-50 rounded border border-slate-200">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={room.has_self}
                            onChange={() => toggleSelfInRoom(roomIdx)}
                            className="h-4 w-4"
                          />
                          <span className="text-sm font-medium text-slate-700">
                            {selectedBooking?.guest_name || "Guest"} (Self)
                          </span>
                        </label>
                        {room.has_self && !actionForm.identity_card_number && (
                          <p className="text-xs text-red-500 mt-1 ml-6">⚠️ Enter Identity Card No in Personal Details section above</p>
                        )}
                      </div>

                      {/* Family Members in this room */}
                      <div className="space-y-3">
                        {room.family_members.map((member, memberIdx) => (
                          <div key={memberIdx} className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-sm font-medium text-slate-700">Family Member {memberIdx + 1}</span>
                              <Button 
                                type="button" 
                                variant="ghost" 
                                size="sm" 
                                onClick={() => removeFamilyMemberFromRoom(roomIdx, memberIdx)} 
                                className="text-red-400 hover:text-red-600 h-6 w-6 p-0"
                              >
                                <Trash size={14} />
                              </Button>
                            </div>
                            
                            <div className="grid grid-cols-3 gap-2 mb-2">
                              <div>
                                <Label className="text-xs">Relation</Label>
                                <Select 
                                  value={member.relation} 
                                  onValueChange={(v) => updateRoomFamilyMember(roomIdx, memberIdx, "relation", v)}
                                >
                                  <SelectTrigger className="earms-input mt-1 text-xs h-8"><SelectValue /></SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="w/o">Wife (w/o)</SelectItem>
                                    <SelectItem value="s/o">Son (s/o)</SelectItem>
                                    <SelectItem value="d/o">Daughter (d/o)</SelectItem>
                                    <SelectItem value="other">Other</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label className="text-xs">Name</Label>
                                <Input 
                                  value={member.name} 
                                  onChange={(e) => updateRoomFamilyMember(roomIdx, memberIdx, "name", e.target.value)}
                                  onFocus={(e) => e.target.select()} 
                                  className="earms-input mt-1 text-xs h-8" 
                                  placeholder="Full name" 
                                />
                              </div>
                              <div>
                                <Label className="text-xs">Age</Label>
                                <Input 
                                  type="number" 
                                  min="0" 
                                  value={member.age} 
                                  onChange={(e) => updateRoomFamilyMember(roomIdx, memberIdx, "age", e.target.value)}
                                  onFocus={(e) => e.target.select()} 
                                  className="earms-input mt-1 text-xs h-8" 
                                />
                              </div>
                              <div>
                                <Label className="text-xs">Sex</Label>
                                <Select 
                                  value={member.sex} 
                                  onValueChange={(v) => updateRoomFamilyMember(roomIdx, memberIdx, "sex", v)}
                                >
                                  <SelectTrigger className="earms-input mt-1 text-xs h-8"><SelectValue /></SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="M">M</SelectItem>
                                    <SelectItem value="F">F</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div>
                                <Label className="text-xs">Mobile</Label>
                                <Input 
                                  value={member.mobile} 
                                  onChange={(e) => {
                                    const formatted = formatIndianPhone(e.target.value);
                                    updateRoomFamilyMember(roomIdx, memberIdx, "mobile", formatted);
                                  }}
                                  onFocus={(e) => e.target.select()} 
                                  className="earms-input mt-1 text-xs h-8" 
                                  placeholder="10-digit" 
                                  maxLength={11}
                                />
                              </div>
                            </div>

                            {/* Dependent Card Checkbox */}
                            <div className="flex items-center gap-2 p-2 bg-white rounded border border-slate-200">
                              <input
                                type="checkbox"
                                checked={member.has_dependent_card}
                                onChange={(e) => updateRoomFamilyMember(roomIdx, memberIdx, "has_dependent_card", e.target.checked)}
                                className="h-4 w-4"
                                id={`dep-card-${roomIdx}-${memberIdx}`}
                              />
                              <label htmlFor={`dep-card-${roomIdx}-${memberIdx}`} className="text-xs font-medium text-slate-700 cursor-pointer">
                                Dependent Card Available?
                              </label>
                            </div>

                            {/* Conditional Dependent ID Field */}
                            {member.has_dependent_card && (
                              <div className="mt-2">
                                <Label className="text-xs">Dependent ID Ser No</Label>
                                <Input 
                                  value={member.dependent_id || ""} 
                                  onChange={(e) => updateRoomFamilyMember(roomIdx, memberIdx, "dependent_id", toUpperCase(e.target.value))}
                                  onFocus={(e) => e.target.select()} 
                                  className="earms-input mt-1 text-xs h-8" 
                                  placeholder="Enter ID Serial Number" 
                                />
                              </div>
                            )}
                          </div>
                        ))}

                        {/* Add Family Member Button */}
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => addFamilyMemberToRoom(roomIdx)}
                          className="w-full text-xs"
                        >
                          <Plus size={14} className="mr-1" /> Add Family Member to Room {room.room_number}
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Bank / UPI Details */}
              <div>
                <h4 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <Bank size={16} className="text-slate-500" /> Bank / UPI Details (for refund if cancelled)
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Bank Name</Label>
                    <Input value={actionForm.bank_name} onChange={(e) => setActionForm({...actionForm, bank_name: e.target.value})}
                      onFocus={(e) => e.target.select()} placeholder="e.g., State Bank of India" className="earms-input mt-1" data-testid="input-checkin-bank-name" />
                  </div>
                  <div>
                    <Label>IFSC Code</Label>
                    <Input 
                      value={actionForm.bank_ifsc} 
                      onChange={(e) => {
                        const value = toUpperCase(e.target.value);
                        setActionForm({...actionForm, bank_ifsc: value});
                        setCheckinIfscError(value && !validateIFSC(value) ? "Invalid IFSC format (e.g., SBIN0001234)" : "");
                      }}
                      onFocus={(e) => e.target.select()} 
                      placeholder="e.g., SBIN0001234" 
                      className={`earms-input mt-1 ${checkinIfscError ? 'border-red-500' : ''}`}
                      data-testid="input-checkin-bank-ifsc" 
                      maxLength={11}
                    />
                    {checkinIfscError && <p className="text-xs text-red-500 mt-1">{checkinIfscError}</p>}
                  </div>
                  <div>
                    <Label>Account Number</Label>
                    <Input value={actionForm.bank_account} onChange={(e) => setActionForm({...actionForm, bank_account: e.target.value})}
                      onFocus={(e) => e.target.select()} placeholder="Bank account number" className="earms-input mt-1" data-testid="input-checkin-bank-account" />
                  </div>
                  <div>
                    <Label>UPI ID</Label>
                    <Input value={actionForm.upi_id} onChange={(e) => setActionForm({...actionForm, upi_id: e.target.value})}
                      onFocus={(e) => e.target.select()} placeholder="e.g., name@upi" className="earms-input mt-1" data-testid="input-checkin-upi-id" />
                  </div>
                  <div>
                    <Label>UPI Phone</Label>
                    <Input 
                      value={actionForm.upi_phone} 
                      onChange={(e) => {
                        const formatted = formatIndianPhone(e.target.value);
                        setActionForm({...actionForm, upi_phone: formatted});
                        setCheckinUpiPhoneError(formatted && !validateIndianPhone(formatted) ? "Enter a valid 10-digit Indian mobile number" : "");
                      }}
                      onFocus={(e) => e.target.select()} 
                      placeholder="10-digit mobile" 
                      className={`earms-input mt-1 ${checkinUpiPhoneError ? 'border-red-500' : ''}`}
                      data-testid="input-checkin-upi-phone" 
                      maxLength={11}
                    />
                    {checkinUpiPhoneError && <p className="text-xs text-red-500 mt-1">{checkinUpiPhoneError}</p>}
                  </div>
                </div>
              </div>

              {/* Bill Preview at Check-In */}
              {selectedBooking && (
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <h4 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                    <CurrencyInr size={16} className="text-blue-500" /> Bill Summary (Updated with Room Assignments)
                  </h4>
                  {(() => {
                    const nights = Math.ceil(
                      (new Date(selectedBooking.check_out_date) - new Date(selectedBooking.check_in_date)) / 86400000
                    );
                    
                    // Calculate per-room charges based on room-guest mapping
                    let roomChargesTotal = 0;
                    const roomChargesBreakdown = roomGuestMapping.map(room => {
                      let ratePerNight = 0;
                      
                      // Determine rate based on charge category
                      if (room.charge_category === "Def Civ") {
                        // Defense Civilian rates
                        ratePerNight = room.room_category === "Cat I" 
                          ? (settings?.def_civ_cat_i_rate || 600)
                          : (settings?.def_civ_cat_ii_rate || 600);
                      } else {
                        // Regular Cat I/II rates
                        ratePerNight = room.room_category === "Cat I"
                          ? (settings?.cat_i_rate || 500)
                          : (settings?.cat_ii_rate || 400);
                      }
                      
                      const roomTotal = ratePerNight * nights;
                      roomChargesTotal += roomTotal;
                      
                      return {
                        room_number: room.room_number,
                        room_category: room.room_category,
                        charge_category: room.charge_category,
                        rate_per_night: ratePerNight,
                        total: roomTotal
                      };
                    });
                    
                    const extraBedCharge = actionForm.extra_beds * 75;
                    const totalWithExtra = roomChargesTotal + extraBedCharge;
                    const balance = totalWithExtra - (selectedBooking.advance_paid || 0);
                    
                    return (
                      <div className="space-y-1 text-sm">
                        {/* Per-Room Breakdown */}
                        {roomChargesBreakdown.length > 0 && (
                          <div className="mb-2 p-2 bg-white rounded border border-slate-200">
                            <p className="text-xs font-semibold text-slate-700 mb-1">Per-Room Charges ({nights} night{nights > 1 ? "s" : ""}):</p>
                            {roomChargesBreakdown.map((rc, idx) => (
                              <div key={idx} className="flex justify-between text-xs">
                                <span className="text-slate-600">
                                  Room {rc.room_number} ({rc.room_category})
                                  {rc.charge_category === "Def Civ" && <span className="text-red-600 font-bold ml-1">→ Def Civ</span>}
                                  : ₹{rc.rate_per_night} × {nights}
                                </span>
                                <span className="font-medium">₹{rc.total.toFixed(2)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                        
                        <div className="flex justify-between font-semibold">
                          <span className="text-slate-700">Total Room Charges:</span>
                          <span className="font-bold">₹{roomChargesTotal.toFixed(2)}</span>
                        </div>
                        
                        {actionForm.extra_beds > 0 && (
                          <div className="flex justify-between text-amber-700">
                            <span>Extra Beds ({actionForm.extra_beds} × ₹75):</span>
                            <span className="font-medium">+ ₹{extraBedCharge.toFixed(2)}</span>
                          </div>
                        )}
                        <div className="flex justify-between text-blue-700 border-t border-slate-200 pt-1 mt-1">
                          <span>Advance Already Paid:</span>
                          <span className="font-medium">- ₹{(selectedBooking.advance_paid || 0).toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between font-bold text-emerald-700 border-t-2 border-emerald-300 pt-1 mt-1">
                          <span>Balance Due at Checkout:</span>
                          <span className="text-base">₹{balance.toFixed(2)}</span>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Notes */}
              <div>
                <Label>Notes</Label>
                <Textarea value={actionForm.notes} onChange={(e) => setActionForm({...actionForm, notes: e.target.value})}
                  placeholder="Check-in notes..." className="mt-1" data-testid="checkin-notes" />
              </div>

            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowCheckIn(false); setSelectedBooking(null); resetActionForm(); setPhoneError(""); setRoomGuestMapping([]); }}>Cancel</Button>
            <Button onClick={handleCheckIn} className="bg-emerald-500 hover:bg-emerald-600" disabled={!actionForm.staff_id} data-testid="confirm-checkin">
              Confirm Check-In
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== CHECK-OUT DIALOG ===== */}
      <Dialog open={showCheckOut} onOpenChange={setShowCheckOut}>
        <DialogContent data-testid="checkout-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <SignOut size={24} className="text-blue-500" />
              Check-Out Guest
            </DialogTitle>
          </DialogHeader>
          {selectedBooking && (
            <div className="space-y-4 py-4">
              <div className="p-4 bg-slate-50 rounded-xl">
                <p className="font-medium">{selectedBooking.guest_name}</p>
                <p className="text-sm text-slate-500">Room {getRoomDisplay(selectedBooking)}</p>
                {selectedBooking.extra_beds > 0 && (
                  <p className="text-xs text-amber-600">Extra Beds (at check-in): {selectedBooking.extra_beds} × ₹75 = ₹{selectedBooking.extra_bed_charge}</p>
                )}
                <p className="text-sm font-medium text-amber-600 mt-2">Balance Due: ₹{selectedBooking.balance_amount}</p>
              </div>
              
              {/* Extra Bed Usage During Stay */}
              <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
                <h4 className="font-semibold text-blue-800 mb-3">Extra Bed Usage (If any additional beds used)</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Extra Beds Used</Label>
                    <Input
                      type="number"
                      min="0"
                      max="5"
                      value={actionForm.extra_beds_checkout || 0}
                      onChange={(e) => {
                        const beds = parseInt(e.target.value) || 0;
                        setActionForm({...actionForm, extra_beds_checkout: beds});
                      }}
                      onFocus={(e) => e.target.select()}
                      placeholder="0"
                      className="earms-input mt-1"
                      data-testid="input-extra-beds-checkout"
                    />
                    <p className="text-xs text-slate-500 mt-1">Number of extra beds (0-5)</p>
                  </div>
                  <div>
                    <Label>Days Used</Label>
                    <Input
                      type="number"
                      min="0"
                      value={actionForm.extra_bed_days || 0}
                      onChange={(e) => {
                        const days = parseInt(e.target.value) || 0;
                        setActionForm({...actionForm, extra_bed_days: days});
                      }}
                      onFocus={(e) => e.target.select()}
                      placeholder="0"
                      className="earms-input mt-1"
                      data-testid="input-extra-bed-days"
                    />
                    <p className="text-xs text-slate-500 mt-1">How many days used</p>
                  </div>
                </div>
                {(actionForm.extra_beds_checkout > 0 && actionForm.extra_bed_days > 0) && (
                  <div className="mt-3 p-2 bg-white rounded border border-blue-300">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-600">Extra Bed Charges:</span>
                      <span className="font-semibold text-blue-700">
                        {actionForm.extra_beds_checkout} beds × {actionForm.extra_bed_days} days × ₹75 = ₹{actionForm.extra_beds_checkout * actionForm.extra_bed_days * 75}
                      </span>
                    </div>
                  </div>
                )}
              </div>
              <div>
                <Label>Staff Member *</Label>
                <Select value={actionForm.staff_id} onValueChange={(v) => setActionForm({...actionForm, staff_id: v})}>
                  <SelectTrigger className="earms-input mt-1" data-testid="select-staff-checkout">
                    <SelectValue placeholder="Select staff" />
                  </SelectTrigger>
                  <SelectContent>
                    {staff.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name} ({s.staff_type})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Final Payment *</Label>
                  <Input
                    type="number"
                    value={(() => {
                      const extraBedCharge = (actionForm.extra_beds_checkout || 0) * (actionForm.extra_bed_days || 0) * 75;
                      const totalDue = (selectedBooking.balance_amount || 0) + extraBedCharge;
                      return actionForm.final_payment !== undefined ? actionForm.final_payment : totalDue;
                    })()}
                    onChange={(e) => setActionForm({...actionForm, final_payment: parseFloat(e.target.value) || 0})}
                    onFocus={(e) => {
                      // Auto-fill with calculated total on first focus
                      const extraBedCharge = (actionForm.extra_beds_checkout || 0) * (actionForm.extra_bed_days || 0) * 75;
                      const totalDue = (selectedBooking.balance_amount || 0) + extraBedCharge;
                      if (actionForm.final_payment === 0 || actionForm.final_payment === undefined) {
                        setActionForm({...actionForm, final_payment: totalDue});
                      }
                      e.target.select();
                    }}
                    className="earms-input mt-1"
                    data-testid="input-final-payment"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    Balance (₹{selectedBooking.balance_amount}) + Extra Beds (₹{(actionForm.extra_beds_checkout || 0) * (actionForm.extra_bed_days || 0) * 75})
                  </p>
                </div>
                <div>
                  <Label>Payment Mode</Label>
                  <Select value={actionForm.payment_mode} onValueChange={(v) => setActionForm({...actionForm, payment_mode: v})}>
                    <SelectTrigger className="earms-input mt-1" data-testid="select-payment-mode-checkout">
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
                  data-testid="checkout-notes"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCheckOut(false)}>Cancel</Button>
            <Button onClick={handleProceedToFeedback} className="bg-blue-500 hover:bg-blue-600" data-testid="confirm-checkout">Proceed to Feedback</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== CANCEL BOOKING DIALOG ===== */}
      <Dialog open={showCancel} onOpenChange={(open) => { setShowCancel(open); if (!open) { setSelectedBooking(null); setRefundInfo(null); } }}>
        <DialogContent data-testid="cancel-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <X size={24} />
              Cancel Booking
            </DialogTitle>
          </DialogHeader>
          {selectedBooking && (
            <div className="space-y-4 py-4">
              <div className="p-4 bg-red-50 rounded-xl">
                <p className="font-medium text-red-800">{selectedBooking.guest_name}</p>
                <p className="text-sm text-red-600">Booking #{selectedBooking.booking_number}</p>
                <p className="text-sm text-red-600">Advance Paid: ₹{selectedBooking.advance_paid}</p>
              </div>

              {/* Refund Calculation */}
              {refundInfo ? (
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
                  <h4 className="font-semibold text-amber-800 mb-2">Refund Calculation</h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Days until check-in:</span>
                      <span className="font-medium">{refundInfo.days_until_checkin} days</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Advance Paid:</span>
                      <span>₹{refundInfo.advance_paid}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Cancellation Charge ({refundInfo.charge_percent}%):</span>
                      <span className="text-red-600">- ₹{refundInfo.cancellation_charge}</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t border-amber-200 mt-2">
                      <span className="font-semibold text-amber-800">Refund Amount:</span>
                      <span className="font-bold text-lg text-emerald-700">₹{refundInfo.refund_amount}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2 p-3 bg-slate-50 rounded-xl text-slate-500">
                  <SpinnerGap size={18} className="animate-spin" />
                  Calculating refund...
                </div>
              )}

              <div>
                <Label>Cancellation Reason</Label>
                <Textarea
                  value={actionForm.reason}
                  onChange={(e) => setActionForm({...actionForm, reason: e.target.value})}
                  placeholder="Reason for cancellation..."
                  className="mt-1"
                  data-testid="cancel-reason"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCancel(false)}>Go Back</Button>
            <Button
              onClick={handleCancel}
              variant="destructive"
              data-testid="confirm-cancel"
              disabled={!refundInfo}
            >
              Confirm Cancellation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== PENDING REFUNDS DIALOG ===== */}
      <Dialog open={showPendingRefunds} onOpenChange={setShowPendingRefunds}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="pending-refunds-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-700">
              <ArrowCounterClockwise size={24} />
              Pending Refunds
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            {pendingRefunds.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <ArrowCounterClockwise size={40} className="mx-auto mb-3 text-slate-300" />
                <p>No pending refunds</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <p className="text-sm text-amber-700 font-medium">{pendingRefunds.length} refund(s) pending</p>
                  <Button size="sm" onClick={() => {
                    const result = generateRefundsPDF(pendingRefunds);
                    showPDFNotification(result, `Refunds Report (${result.count} refunds)`);
                  }} className="flex items-center gap-1 bg-red-600 hover:bg-red-700 text-white" data-testid="print-refunds-btn">
                    <FilePdf size={16} /> Print PDF
                  </Button>
                </div>
                {pendingRefunds.map((refund) => (
                  <div key={refund.id} className="p-4 border border-amber-200 bg-amber-50 rounded-xl" data-testid={`refund-item-${refund.id}`}>
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="font-semibold text-slate-800">{refund.guest_name}</p>
                        <p className="text-sm text-slate-500">Booking #{refund.booking_number}</p>
                        <p className="text-lg font-bold text-amber-700 mt-1">₹{refund.amount}</p>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleProcessRefund(refund)}
                        className="bg-emerald-500 hover:bg-emerald-600 text-white"
                        data-testid={`process-refund-btn-${refund.id}`}
                      >
                        Mark Refunded
                      </Button>
                    </div>
                    {/* Bank / UPI details */}
                    <div className="mt-2 p-3 bg-white rounded-lg border border-amber-100 text-sm">
                      <p className="font-medium text-slate-700 mb-1">Refund Details:</p>
                      {refund.bank_name && <p className="text-slate-600"><span className="font-medium">Bank:</span> {refund.bank_name}</p>}
                      {refund.bank_account && <p className="text-slate-600"><span className="font-medium">Account:</span> {refund.bank_account}</p>}
                      {refund.bank_ifsc && <p className="text-slate-600"><span className="font-medium">IFSC:</span> {refund.bank_ifsc}</p>}
                      {refund.upi_id && <p className="text-slate-600"><span className="font-medium">UPI ID:</span> {refund.upi_id}</p>}
                      {refund.upi_phone && <p className="text-slate-600"><span className="font-medium">UPI Phone:</span> {refund.upi_phone}</p>}
                      {refund.upi_number && !refund.upi_id && !refund.upi_phone && <p className="text-slate-600"><span className="font-medium">UPI:</span> {refund.upi_number}</p>}
                      {!refund.bank_name && !refund.bank_account && !refund.upi_id && !refund.upi_phone && !refund.upi_number && (
                        <p className="text-slate-400 italic">No bank/UPI details on record</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPendingRefunds(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== PROCESS REFUND DIALOG ===== */}
      <Dialog open={!!refundAction} onOpenChange={(open) => { if (!open) setRefundAction(null); }}>
        <DialogContent data-testid="process-refund-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-emerald-700">
              <ArrowCounterClockwise size={24} />
              Mark Refund as Completed
            </DialogTitle>
          </DialogHeader>
          {refundAction && (
            <div className="space-y-4 py-4">
              <div className="p-4 bg-emerald-50 rounded-xl">
                <p className="font-medium">{refundAction.guest_name}</p>
                <p className="text-sm text-slate-500">Booking #{refundAction.booking_number}</p>
                <p className="text-lg font-bold text-emerald-700">Refund Amount: ₹{refundAction.amount}</p>
              </div>
              <div>
                <Label>Transaction Reference *</Label>
                <Input
                  value={refundForm.transaction_ref}
                  onChange={(e) => setRefundForm({...refundForm, transaction_ref: e.target.value})}
                  onFocus={(e) => e.target.select()}
                  placeholder="UTR / Transaction ID / Reference number"
                  className="earms-input mt-1"
                  data-testid="input-transaction-ref"
                />
              </div>
              <div>
                <Label>Refund Date</Label>
                <Input
                  type="date"
                  value={refundForm.refund_date}
                  onChange={(e) => setRefundForm({...refundForm, refund_date: e.target.value})}
                  className="earms-input mt-1"
                  data-testid="input-refund-date"
                />
              </div>
              <div>
                <Label>Notes</Label>
                <Textarea
                  value={refundForm.notes}
                  onChange={(e) => setRefundForm({...refundForm, notes: e.target.value})}
                  placeholder="Additional notes..."
                  className="mt-1"
                  data-testid="refund-notes"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setRefundAction(null)}>Cancel</Button>
            <Button onClick={handleConfirmRefund} className="bg-emerald-500 hover:bg-emerald-600" data-testid="confirm-refund">
              Confirm Refund
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== FEEDBACK FORM (before completing checkout) ===== */}
      {showFeedback && pendingCheckoutBooking && (
        <FeedbackForm
          booking={pendingCheckoutBooking}
          open={showFeedback}
          onClose={() => { setShowFeedback(false); setPendingCheckoutBooking(null); }}
          onSubmitted={handleFeedbackSubmitted}
        />
      )}


      {/* ===== GUEST HISTORY DIALOG ===== */}
      <Dialog open={showGuestHistory} onOpenChange={(open) => { setShowGuestHistory(open); if (!open) resetGuestHistorySearch(); }}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto" data-testid="guest-history-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MagnifyingGlass size={24} className="text-indigo-500" weight="fill" />
              Guest History Lookup
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6">
            {/* Search Form */}
            <div className="space-y-4">
              <p className="text-sm text-slate-600">Search by guest's phone number or army/service number</p>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Phone Number</Label>
                  <Input
                    value={guestHistorySearch.phone}
                    onChange={(e) => setGuestHistorySearch(prev => ({ ...prev, phone: formatIndianPhone(e.target.value) }))}
                    onFocus={(e) => e.target.select()}
                    placeholder="10-digit mobile number"
                    className="earms-input mt-1"
                    data-testid="history-phone-input"
                    maxLength={11}
                  />
                </div>
                <div>
                  <Label>Army / Service Number</Label>
                  <Input
                    value={guestHistorySearch.army_number}
                    onChange={(e) => setGuestHistorySearch(prev => ({ ...prev, army_number: toUpperCase(e.target.value) }))}
                    onFocus={(e) => e.target.select()}
                    placeholder="e.g., 15814432-F"
                    className="earms-input mt-1"
                    data-testid="history-army-input"
                  />
                </div>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={handleSearchGuestHistory}
                  disabled={loadingHistory}
                  className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-600"
                  data-testid="search-history-btn"
                >
                  {loadingHistory ? (
                    <><SpinnerGap size={20} className="animate-spin" /> Searching...</>
                  ) : (
                    <><MagnifyingGlass size={20} /> Search</>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={resetGuestHistorySearch}
                  className="flex items-center gap-2"
                >
                  Clear
                </Button>
              </div>
            </div>

            {/* Results */}
            {guestHistoryData && guestHistoryData.found && (
              <div className="space-y-6 mt-6 border-t pt-6">
                {/* Guest Info Summary */}
                <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
                  <h3 className="font-semibold text-indigo-900 mb-3 flex items-center gap-2">
                    <User size={20} />
                    Guest Information
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                    <div>
                      <p className="text-slate-500">Name</p>
                      <p className="font-medium text-slate-800">{guestHistoryData.guest_info.guest_name}</p>
                    </div>
                    {guestHistoryData.guest_info.guest_contact && (
                      <div>
                        <p className="text-slate-500">Phone</p>
                        <p className="font-medium text-slate-800">{guestHistoryData.guest_info.guest_contact}</p>
                      </div>
                    )}
                    {guestHistoryData.guest_info.guest_rank && (
                      <div>
                        <p className="text-slate-500">Rank</p>
                        <p className="font-medium text-slate-800">{guestHistoryData.guest_info.guest_rank}</p>
                      </div>
                    )}
                    {guestHistoryData.guest_info.army_number && (
                      <div>
                        <p className="text-slate-500">Army Number</p>
                        <p className="font-medium text-slate-800">{guestHistoryData.guest_info.army_number}</p>
                      </div>
                    )}
                    {guestHistoryData.guest_info.guest_unit && (
                      <div>
                        <p className="text-slate-500">Unit</p>
                        <p className="font-medium text-slate-800">{guestHistoryData.guest_info.guest_unit}</p>
                      </div>
                    )}
                    {guestHistoryData.guest_info.guest_service_status && (
                      <div>
                        <p className="text-slate-500">Service Status</p>
                        <p className="font-medium text-slate-800">{guestHistoryData.guest_info.guest_service_status}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-center">
                    <div className="text-2xl font-bold text-blue-800">{guestHistoryData.statistics.total_bookings}</div>
                    <div className="text-xs text-blue-600 mt-1">Total Bookings</div>
                  </div>
                  <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
                    <div className="text-2xl font-bold text-emerald-800">{guestHistoryData.statistics.completed_stays}</div>
                    <div className="text-xs text-emerald-600 mt-1">Completed Stays</div>
                  </div>
                  <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 text-center">
                    <div className="text-2xl font-bold text-purple-800">{guestHistoryData.statistics.total_nights_stayed}</div>
                    <div className="text-xs text-purple-600 mt-1">Total Nights</div>
                  </div>
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-center">
                    <div className="text-2xl font-bold text-amber-800">₹{guestHistoryData.statistics.total_spent}</div>
                    <div className="text-xs text-amber-600 mt-1">Total Spent</div>
                  </div>
                </div>

                {/* Booking History */}
                <div>
                  <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
                    <CalendarCheck size={20} />
                    Booking History ({guestHistoryData.bookings.length})
                  </h3>
                  <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                    {guestHistoryData.bookings.map((booking) => (
                      <div 
                        key={booking.id} 
                        className="border border-slate-200 rounded-xl p-4 hover:border-indigo-300 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <p className="font-semibold text-slate-800">#{booking.booking_number}</p>
                            <p className="text-xs text-slate-500">
                              {format(parseISO(booking.check_in_date), "dd MMM yyyy")} - {format(parseISO(booking.check_out_date), "dd MMM yyyy")}
                            </p>
                          </div>
                          <Badge className={
                            booking.status === "checked_out" ? "badge-success" :
                            booking.status === "checked_in" ? "badge-warning" :
                            booking.status === "confirmed" ? "badge-info" :
                            "badge-danger"
                          }>
                            {booking.status === "checked_in" ? "Checked In" :
                             booking.status === "checked_out" ? "Checked Out" :
                             booking.status === "confirmed" ? "Confirmed" :
                             "Cancelled"}
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                          <div>
                            <p className="text-slate-500 text-xs">Room(s)</p>
                            <p className="font-medium text-slate-700">{booking.room_numbers.join(", ")}</p>
                          </div>
                          <div>
                            <p className="text-slate-500 text-xs">Category</p>
                            <p className="font-medium text-slate-700">{[...new Set(booking.room_categories)].join(", ")}</p>
                          </div>
                          <div>
                            <p className="text-slate-500 text-xs">Total Amount</p>
                            <p className="font-medium text-slate-700">₹{booking.total_amount}</p>
                          </div>
                          <div>
                            <p className="text-slate-500 text-xs">Payment</p>
                            <p className="font-medium text-slate-700">{booking.payment_mode || "N/A"}</p>
                          </div>
                        </div>

                        {booking.extra_beds > 0 && (
                          <p className="text-xs text-slate-500 mt-2">Extra Beds: {booking.extra_beds}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {guestHistoryData && !guestHistoryData.found && (
              <div className="text-center py-8 text-slate-500">
                <MagnifyingGlass size={48} className="mx-auto mb-3 opacity-30" />
                <p>No booking history found for this guest</p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button onClick={() => { setShowGuestHistory(false); resetGuestHistorySearch(); }}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== 4-NIGHT CONFIRMATION DIALOG ===== */}
      <Dialog open={showNightConfirmation} onOpenChange={setShowNightConfirmation}>
        <DialogContent className="max-w-md" data-testid="night-confirmation-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-600">
              <WarningCircle size={24} weight="fill" />
              Extended Stay Confirmation
            </DialogTitle>
          </DialogHeader>
          
          <div className="py-4">
            <p className="text-slate-700 mb-4">
              You are booking room(s) for more than 4 nights.
            </p>
            <p className="text-slate-700 font-semibold">
              Please confirm that you have taken due approval from OIC ECSAG for the same.
            </p>
          </div>

          <DialogFooter className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowNightConfirmation(false);
                setPendingBookingData(null);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={executeBooking}
              className="bg-amber-500 hover:bg-amber-600"
            >
              Confirm & Proceed
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>


      {/* ===== WHATSAPP MESSAGE MODAL ===== */}
      <Dialog open={showWhatsAppModal} onOpenChange={setShowWhatsAppModal}>
        <DialogContent className="max-w-lg" data-testid="whatsapp-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-emerald-600">
              <CheckSquare size={24} weight="fill" />
              Booking Confirmed!
            </DialogTitle>
          </DialogHeader>
          
          {createdBookingData && (
            <div className="space-y-4 py-4">
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                <p className="text-sm text-emerald-700 mb-2">✅ Booking created successfully!</p>
                <p className="font-semibold text-emerald-800">Booking #{createdBookingData.booking_number}</p>
                <p className="text-sm text-emerald-700">{createdBookingData.guest_name}</p>
                <p className="text-sm text-emerald-600">
                  Room {(createdBookingData.room_numbers || []).join(", ")} · {(createdBookingData.room_categories || []).filter((v, i, arr) => arr.indexOf(v) === i).join(", ")}
                </p>
              </div>

              <div>
                <Label className="font-semibold text-slate-700 mb-2 block">
                  WhatsApp Message (Ready to Copy)
                </Label>
                <div className="relative">
                  <Textarea
                    readOnly
                    value={`🏠 *ARAAMGAH BOOKING CONFIRMATION*

Dear ${createdBookingData.guest_name},

Your booking has been confirmed! 🎉

📋 *Booking Details:*
• Booking No: ${createdBookingData.booking_number}
• Guest: ${createdBookingData.guest_name}
${createdBookingData.guest_rank ? `• Rank: ${createdBookingData.guest_rank}` : ""}
${createdBookingData.guest_unit ? `• Unit: ${createdBookingData.guest_unit}` : ""}
• Room(s): ${(createdBookingData.room_numbers || []).join(", ")}
• Category: ${(createdBookingData.room_categories || []).filter((v, i, arr) => arr.indexOf(v) === i).join(", ")}

📅 *Stay Period:*
• Check-in: ${format(parseISO(createdBookingData.check_in_date), "dd MMM yyyy")} - 1300h
• Check-out: ${format(parseISO(createdBookingData.check_out_date), "dd MMM yyyy")} - 0800h

💰 *Payment:*
• Total Amount: ₹${createdBookingData.total_amount}
• Advance Paid: ₹${createdBookingData.advance_paid}
• Balance Due: ₹${createdBookingData.balance_amount}

*Guidelines for guests pl*
1. Pl carry aadhar card as ID proof for smooth check in. *Non Dependent and Unaccompanied Civil Guest* are not allowed without serving pers. Dependent Card & Aadhar card reqd for verification.
2. Max 4 days res at a time.
3. Extra bed charges is Rs 75/- per day.
4. Cancellation- 100% Adv booking will be refunded only if indl info the JCO I/C ECSAG regarding cancellation 04 days before the date of booking. 50% booking amt will be refunded if informed within 2-4 days of booking. No refund will be given if informed within 2 days of booking date.
5. Only alloted rooms will be opened by the incharge.
6. Pets are not allowed.

Have A comfortable stay,
Regards
ECSAG Shillong`}
                    className="mt-2 font-mono text-sm min-h-[400px] bg-slate-50"
                    onClick={(e) => e.target.select()}
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    className="absolute top-2 right-2 bg-white"
                    onClick={() => {
                      const message = `🏠 *ARAAMGAH BOOKING CONFIRMATION*

Dear ${createdBookingData.guest_name},

Your booking has been confirmed! 🎉

📋 *Booking Details:*
• Booking No: ${createdBookingData.booking_number}
• Guest: ${createdBookingData.guest_name}
${createdBookingData.guest_rank ? `• Rank: ${createdBookingData.guest_rank}\n` : ""}${createdBookingData.guest_unit ? `• Unit: ${createdBookingData.guest_unit}\n` : ""}• Room(s): ${(createdBookingData.room_numbers || []).join(", ")}
• Category: ${(createdBookingData.room_categories || []).filter((v, i, arr) => arr.indexOf(v) === i).join(", ")}

📅 *Stay Period:*
• Check-in: ${format(parseISO(createdBookingData.check_in_date), "dd MMM yyyy")} - 1300h
• Check-out: ${format(parseISO(createdBookingData.check_out_date), "dd MMM yyyy")} - 0800h

💰 *Payment:*
• Total Amount: ₹${createdBookingData.total_amount}
• Advance Paid: ₹${createdBookingData.advance_paid}
• Balance Due: ₹${createdBookingData.balance_amount}

*Guidelines for guests pl*
1. Pl carry aadhar card as ID proof for smooth check in. *Non Dependent and Unaccompanied Civil Guest* are not allowed without serving pers. Dependent Card & Aadhar card reqd for verification.
2. Max 4 days res at a time.
3. Extra bed charges is Rs 75/- per day.
4. Cancellation- 100% Adv booking will be refunded only if indl info the JCO I/C ECSAG regarding cancellation 04 days before the date of booking. 50% booking amt will be refunded if informed within 2-4 days of booking. No refund will be given if informed within 2 days of booking date.
5. Only alloted rooms will be opened by the incharge.
6. Pets are not allowed.

Have A comfortable stay,
Regards
ECSAG Shillong`;
                      navigator.clipboard.writeText(message);
                      toast.success("Message copied to clipboard!");
                    }}
                    data-testid="copy-whatsapp-btn"
                  >
                    Copy Message
                  </Button>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  💡 Click "Copy Message" button, then paste in WhatsApp to send to guest
                </p>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button 
              onClick={() => {
                setShowWhatsAppModal(false);
                setCreatedBookingData(null);
              }}
              className="bg-emerald-500 hover:bg-emerald-600"
            >
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
