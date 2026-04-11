import { useState, useEffect, useCallback } from "react";
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
import { DayPicker } from "react-day-picker";
import "react-day-picker/dist/style.css";
import { generateCheckoutReceipt, generateRefundsPDF, generateBookingSlips } from "@/utils/pdfUtils";
import FeedbackForm from "@/components/FeedbackForm";
import RoomSegmentSelector from "@/components/RoomSegmentSelector";
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
  WarningCircle,
  NotePencil,
  Pencil,
  CheckCircle
} from "@phosphor-icons/react";
import { format, parseISO } from "date-fns";
import { useLocation, useNavigate } from "react-router-dom";

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
  const location = useLocation();
  const navigate = useNavigate();
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
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [bookingToDelete, setBookingToDelete] = useState(null);
  const [showAmend, setShowAmend] = useState(false);
  const [amendBooking, setAmendBooking] = useState(null);
  const [amendForm, setAmendForm] = useState({
    check_in_date: null,
    check_out_date: null,
    room_ids: [],
    num_rooms: 1,
    total_members: 1,
    member_ages: [0],
    additional_advance: 0,
    payment_mode: "",
    payment_id: "",
    bank_name: "",
    bank_ifsc: "",
    bank_account: "",
    upi_id: "",
    upi_phone: "",
    amendment_reason: ""
  });
  const [availableRoomsForAmend, setAvailableRoomsForAmend] = useState([]);
  const [loadingRoomsForAmend, setLoadingRoomsForAmend] = useState(false);
  const [amendCheckInOpen, setAmendCheckInOpen] = useState(false);
  const [amendCheckOutOpen, setAmendCheckOutOpen] = useState(false);

  // Guest History
  const [showGuestHistory, setShowGuestHistory] = useState(false);
  const [guestHistorySearch, setGuestHistorySearch] = useState({ phone: "" });
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
    is_org: false,         // NEW: Organization/Non-Org classification
    org_color: "",         // NEW: Color category (only for Org guests)
    num_rooms: 1,
    room_ids: [],
    room_segments: null,   // NEW: Mix & Match room segments
    has_room_changes: false, // NEW: Flag for segmented bookings
    check_in_date: null,
    check_out_date: null,
    advance_paid: 0,
    payment_mode: "",
    payment_id: "",
    bank_name: "",
    bank_ifsc: "",
    bank_account: "",
    upi_id: "",        // NEW: UPI ID for refunds
    upi_phone: "",     // NEW: UPI Phone for refunds
    total_members: 1,  // NEW: Total number of members including guest
    member_ages: [0]   // NEW: Array of ages for all members (default 1 member)
  });
  
  // NEW: State for Mix & Match room selection
  const [showRoomSegmentSelector, setShowRoomSegmentSelector] = useState(false);
  const [useSegmentedBooking, setUseSegmentedBooking] = useState(false);

  const [actionForm, setActionForm] = useState({
    staff_id: "",
    notes: "",
    final_payment: 0,
    payment_mode: "",
    payment_id: "",  // Transaction/receipt ID
    reason: "",
    refund_amount: 0,
    extra_beds: 0,
    extra_beds_checkout: 0,  // Extra beds used at checkout
    extra_bed_days: 0,        // Days extra beds were used
    // Payment details
    card_last4: "",
    card_type: "",
    upi_id: "",
    upi_phone: "",
    bank_name: "",
    bank_ifsc: "",
    bank_account: "",
    // Check-in personal details
    guest_contact: "",
    guest_age: "",
    guest_sex: "",
    guest_address: "",
    org_color: "",  // Organization color (filled at check-in/checkout if Org guest)
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

  // URL-based action handler (from Dashboard quick actions)
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const action = params.get('action');
    const bookingId = params.get('bookingId');
    
    if (!action) return;
    
    // Clear URL params after reading them to prevent re-triggering
    const clearParams = () => {
      navigate('/app/bookings', { replace: true });
    };
    
    if (action === 'new') {
      setShowNewBooking(true);
      clearParams();
    } else if (action === 'pending-refunds') {
      fetchPendingRefunds();
      setShowPendingRefunds(true);
      clearParams();
    } else if (action === 'checkin') {
      // Only process if bookings are loaded
      if (bookings.length === 0) return;
      
      // If bookingId is provided, find and open that specific booking
      if (bookingId) {
        const targetBooking = bookings.find(b => b.id === bookingId);
        if (targetBooking) {
          if (targetBooking.status === 'confirmed') {
            openCheckInDialog(targetBooking);
            clearParams();
          } else {
            toast.error(`Booking cannot be checked in (status: ${targetBooking.status})`);
            clearParams();
          }
        } else {
          toast.error("Booking not found");
          clearParams();
        }
      } else {
        // Fallback: Find first confirmed booking
        const confirmedBooking = bookings.find(b => b.status === 'confirmed');
        if (confirmedBooking) {
          openCheckInDialog(confirmedBooking);
          clearParams();
        } else {
          toast.info("No confirmed bookings available for check-in");
          clearParams();
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
            clearParams();
          } else {
            toast.error(`Booking cannot be checked out (status: ${targetBooking.status})`);
            clearParams();
          }
        } else {
          toast.error("Booking not found");
          clearParams();
        }
      } else {
        // Fallback: Find first checked-in booking
        const checkedInBooking = bookings.find(b => b.status === 'checked_in');
        if (checkedInBooking) {
          openCheckOutDialog(checkedInBooking);
          clearParams();
        } else {
          toast.info("No checked-in bookings available for check-out");
          clearParams();
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
            clearParams();
          } else {
            toast.error(`Booking cannot be cancelled (status: ${targetBooking.status})`);
            clearParams();
          }
        } else {
          toast.error("Booking not found");
          clearParams();
        }
      } else {
        // Fallback: Find first cancelable booking
        const cancelableBooking = bookings.find(b => b.status === 'confirmed' || b.status === 'checked_in');
        if (cancelableBooking) {
          openCancelDialog(cancelableBooking);
          clearParams();
        } else {
          toast.info("No bookings available for cancellation");
          clearParams();
        }
      }
    }
  }, [location.search, bookings, navigate]);

  const fetchData = useCallback(async () => {
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
  }, []);

  const fetchPendingRefunds = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/refunds`, { params: { status: "pending" } });
      setPendingRefunds(res.data);
    } catch (error) {
      toast.error("Failed to load pending refunds");
    }
  }, []);

  useEffect(() => {
    if (settings?.default_advance_amount && bookingForm.check_in_date) {
      // Check if same-day booking
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const checkInDate = new Date(bookingForm.check_in_date);
      checkInDate.setHours(0, 0, 0, 0);
      
      const isSameDay = checkInDate.getTime() === today.getTime();
      const newAdvance = isSameDay ? 0 : settings.default_advance_amount * bookingForm.num_rooms;
      
      // Only update if advance amount actually needs to change
      if (bookingForm.advance_paid !== newAdvance) {
        setBookingForm(prev => ({
          ...prev,
          advance_paid: newAdvance
        }));
      }
    }
  }, [bookingForm.num_rooms, bookingForm.check_in_date, settings?.default_advance_amount]);

  useEffect(() => {
    setBookingForm(prev => ({ ...prev, room_ids: [] }));
  }, [bookingForm.num_rooms]);

  const fetchAvailableRooms = useCallback(async (checkIn, checkOut) => {
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
  }, []);

  useEffect(() => {
    if (bookingForm.check_in_date && bookingForm.check_out_date) {
      fetchAvailableRooms(bookingForm.check_in_date, bookingForm.check_out_date);
      setBookingForm(prev => ({ ...prev, room_ids: [] }));
    }
  }, [bookingForm.check_in_date, bookingForm.check_out_date, fetchAvailableRooms]);

  useEffect(() => { fetchData(); }, [fetchData]);

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
      is_org: false,
      org_color: "",
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
    
    // Room validation - support both traditional and segmented bookings
    const isSegmented = useSegmentedBooking && bookingForm.room_segments;
    if (!isSegmented) {
      // Traditional booking validation
      if (bookingForm.room_ids.length === 0) {
        toast.error("Please select at least one room");
        return;
      }
      if (bookingForm.room_ids.length !== bookingForm.num_rooms) {
        toast.error(`Please select exactly ${bookingForm.num_rooms} room(s)`);
        return;
      }
    } else {
      // Segmented booking validation
      if (!bookingForm.room_segments || bookingForm.room_segments.length === 0) {
        toast.error("Please configure room segments");
        return;
      }
    }
    
    // Advance amount validation
    if (bookingForm.advance_paid < 0) {
      toast.error("Advance amount cannot be negative");
      return;
    }
    
    // Payment validation - only if advance is greater than 0
    if (bookingForm.advance_paid > 0) {
      if (!bookingForm.payment_mode) {
        toast.error("Please select payment mode");
        return;
      }
      if (!isPaymentDetailsFilled()) {
        toast.error("Please fill in the required payment details");
        return;
      }
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
        is_org: formData.is_org || false,
        org_color: formData.org_color || null,
        aadhaar_number: formData.aadhaar_number,
        room_ids: formData.room_ids,
        room_segments: formData.room_segments || null,  // NEW: Mix & Match support
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
        upi_phone: formData.upi_phone,
        total_members: formData.total_members,
        member_ages: formData.member_ages
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
    guest_contact: "", guest_age: "", guest_sex: "", guest_address: "", org_color: "",
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
        has_org_card: false,  // Default: no org card
        org_id: ""
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
    // Check if any family member lacks org card
    const anyMemberWithoutCard = roomMapping.family_members.some(m => !m.has_org_card);
    
    // If Self is not in this room and there are no family members, keep original category
    if (!roomMapping.has_self && roomMapping.family_members.length === 0) {
      return {
        ...roomMapping,
        charge_category: roomMapping.room_category
      };
    }
    
    // If any family member lacks org card → Non-Org rate
    if (anyMemberWithoutCard) {
      return {
        ...roomMapping,
        charge_category: "Non-Org"
      };
    }
    
    // Removed identity card validation - no longer applicable
    const selfHasValidId = true;  // Always allow check-in
    
    if (roomMapping.has_self && !selfHasValidId) {
      // Removed Def Civ logic - now using Non-Org for non-organization guests
      return {
        ...roomMapping,
        charge_category: selectedBooking?.is_org ? roomMapping.room_category : "Non-Org"
      };
    }
    
    // All conditions met → Original category (Cat I/II for Org, Non-Org for others)
    return {
      ...roomMapping,
      charge_category: selectedBooking?.is_org ? roomMapping.room_category : "Non-Org"
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
    
    // Identity card validation removed - no longer required for sanitized system
    
    // Service status validation removed - no longer required for sanitized system
    
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
          has_org_card: member.has_org_card,
          org_id: member.has_org_card ? member.org_id : ""  // Only send if card available
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
        org_color: actionForm.org_color || undefined,  // Organization color for Org guests
        bank_name: actionForm.bank_name || undefined,
        bank_ifsc: actionForm.bank_ifsc || undefined,
        bank_account: actionForm.bank_account || undefined,
        upi_id: actionForm.upi_id || undefined,
        upi_phone: actionForm.upi_phone || undefined,
        family_members: allFamilyMembers.length > 0 ? allFamilyMembers : undefined,
        room_guest_mapping: roomGuestMapping  // Send room-guest mapping with inline family members
      });
      toast.success("Check-in successful!");
      
      // Generate Org Data Form for Organization guests
      if (selectedBooking.is_org) {
        setTimeout(async () => {
          try {
            const { generateOrgDataForm } = await import("../utils/pdfUtils");
            // Pass booking with family members from check-in form
            const bookingWithFamily = {
              ...selectedBooking,
              family_members: allFamilyMembers
            };
            const filename = generateOrgDataForm(bookingWithFamily);
            toast.info(`📄 Org Data Form: ${filename} downloaded. Print and fill manually.`, { duration: 10000 });
          } catch (err) {
            console.error("Org Data Form generation failed:", err);
          }
        }, 500);
      }
      
      setShowCheckIn(false);
      setRoomGuestMapping([]); // Reset room-guest mapping first
      setSelectedBooking(null); // Clear selected booking
      resetActionForm(); // Reset form
      setPhoneError(""); // Clear phone error
      fetchData(); // Refresh booking list
    } catch (error) {
      toast.error(error.response?.data?.detail || "Check-in failed");
    }
  };

  const handleProceedToFeedback = () => {
    if (!actionForm.staff_id) { toast.error("Please select staff member"); return; }
    
    // Validate payment details based on payment mode
    if (actionForm.payment_mode) {
      if (!actionForm.payment_id) {
        const modeLabel = actionForm.payment_mode === "cash" ? "Receipt Number" : 
                         actionForm.payment_mode === "card" ? "Card Transaction Reference" :
                         actionForm.payment_mode === "upi" ? "UPI Transaction ID" :
                         "Bank Transfer Reference";
        toast.error(`Please enter ${modeLabel}`);
        return;
      }
    }
    
    setPendingCheckoutBooking({ ...selectedBooking, _checkoutForm: { ...actionForm } });
    setShowCheckOut(false);
    setShowFeedback(true);
  };

  const handleFeedbackSubmitted = async () => {
    setShowFeedback(false);
    const booking = pendingCheckoutBooking;
    const form = booking._checkoutForm;
    try {
      const response = await axios.post(`${API}/bookings/check-out`, {
        booking_id: booking.id,
        staff_id: form.staff_id,
        final_payment: form.final_payment,
        payment_mode: form.payment_mode,
        payment_id: form.payment_id,
        notes: form.notes,
        extra_beds_checkout: form.extra_beds_checkout || 0,
        extra_bed_days: form.extra_bed_days || 0,
        // Include payment details
        card_last4: form.card_last4 || undefined,
        card_type: form.card_type || undefined,
        upi_id: form.upi_id || undefined,
        upi_phone: form.upi_phone || undefined,
        bank_name: form.bank_name || undefined,
        bank_ifsc: form.bank_ifsc || undefined,
        bank_account: form.bank_account || undefined
      });
      
      toast.success("Check-out successful!");
      
      // Get updated booking from response for PDF generation
      const updatedBooking = response.data.booking || {
        ...booking,
        final_payment: form.final_payment,
        extra_beds_checkout: form.extra_beds_checkout || 0,
        extra_bed_days: form.extra_bed_days || 0,
        extra_bed_charge_checkout: (form.extra_beds_checkout || 0) * (form.extra_bed_days || 0) * 75
      };
      
      // Generate receipt with updated booking data
      const result = generateCheckoutReceipt(updatedBooking, settings);
      showPDFNotification(result, "Checkout Receipt Generated");
      setPendingCheckoutBooking(null);
      setSelectedBooking(null);
      setActionForm({ 
        staff_id: "", notes: "", final_payment: 0, payment_mode: "", payment_id: "",
        reason: "", refund_amount: 0, extra_beds: 0,
        extra_beds_checkout: 0, extra_bed_days: 0,
        card_last4: "", card_type: "", upi_id: "", upi_phone: "",
        bank_name: "", bank_ifsc: "", bank_account: "",
        guest_contact: "", guest_age: "", guest_sex: "", guest_address: "", identity_card_number: "",
        guest_service_status: "", service_type: "", command_hq: "",
        family_members: [] 
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Check-out failed");
    }
  };

  const openCancelDialog = async (booking) => {
    setSelectedBooking(booking);
    setRefundInfo(null);
    // Reset reason field when opening cancel dialog
    setActionForm(prev => ({ ...prev, reason: "", refund_amount: 0 }));
    setShowCancel(true);
    try {
      const res = await axios.get(`${API}/bookings/${booking.id}/calculate-refund`);
      setRefundInfo(res.data);
      setActionForm(prev => ({ ...prev, refund_amount: res.data.refund_amount }));
    } catch (err) {
      console.error("Failed to calculate refund:", err);
    }
  };

  const openDeleteDialog = (booking) => {
    setBookingToDelete(booking);
    setShowDeleteConfirm(true);
  };

  const handleDeleteBooking = async () => {
    if (!bookingToDelete) return;
    
    try {
      await axios.delete(`${API}/bookings/${bookingToDelete.id}`);
      toast.success(`Booking #${bookingToDelete.booking_number} permanently deleted`);
      setShowDeleteConfirm(false);
      setBookingToDelete(null);
      fetchData(); // Refresh bookings list
    } catch (error) {
      console.error("Delete booking error:", error);
      toast.error(error.response?.data?.detail || "Failed to delete booking");
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
      
      // Organization color (if already set during booking)
      org_color: booking.org_color || "",
      
      // Reset other fields to empty (will be filled during check-in)
      staff_id: "",
      extra_beds: 0,
      notes: "",
      guest_age: booking.guest_age || 
                 (booking.member_ages && booking.member_ages.length > 0 && booking.member_ages[0]) 
                 ? String(booking.guest_age || booking.member_ages[0])
                 : "",  // Autofill from guest_age or M1 age
      guest_sex: booking.guest_sex || "M",  // Default to Male
      guest_address: "",
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
            charge_category: room.charge_category === "Non-Org" ? "Non-Org" : newRoom.category
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
    if (!guestHistorySearch.phone && !guestHistorySearch.aadhaar && !guestHistorySearch.name) {
      toast.error("Please enter at least one search parameter");
      return;
    }

    setLoadingHistory(true);
    try {
      const params = {};
      if (guestHistorySearch.phone) {
        params.phone_number = guestHistorySearch.phone;
      }
      if (guestHistorySearch.aadhaar) {
        params.aadhaar_number = guestHistorySearch.aadhaar;
      }
      if (guestHistorySearch.name) {
        params.guest_name = guestHistorySearch.name;
      }

      const response = await axios.get(`${API}/guest-history`, { params });
      
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
    
    // Import and generate
    import("../utils/pdfUtils").then(module => {
      const result = module.generateBookingSlips(eligibleBookings);
      toast.success(`Generated ${result.count} booking slip(s): ${result.filename}`);
    });
  };

  // Amendment handlers
  const handleOpenAmend = (booking) => {
    console.log("Opening amend dialog for booking:", booking);
    setAmendBooking(booking);
    setAmendForm({
      check_in_date: parseISO(booking.check_in_date),
      check_out_date: parseISO(booking.check_out_date),
      room_ids: booking.room_ids || [],
      num_rooms: booking.num_rooms || 1,
      total_members: booking.total_members || 1,
      member_ages: booking.member_ages || [0],
      additional_advance: 0,
      payment_mode: "",
      payment_id: "",
      bank_name: "",
      bank_ifsc: "",
      bank_account: "",
      upi_id: "",
      upi_phone: "",
      amendment_reason: ""
    });
    // Fetch available rooms for the booking's current dates
    fetchAvailableRoomsForAmend(
      parseISO(booking.check_in_date),
      parseISO(booking.check_out_date),
      booking.id
    );
    console.log("Setting showAmend to true");
    setShowAmend(true);
  };

  const fetchAvailableRoomsForAmend = async (checkIn, checkOut, excludeBookingId) => {
    if (!checkIn || !checkOut) { setAvailableRoomsForAmend([]); return; }
    setLoadingRoomsForAmend(true);
    try {
      // Use /api/rooms/available with exclude_booking_id to include currently booked rooms
      const response = await axios.get(`${API}/rooms/available`, {
        params: {
          check_in: format(checkIn, "yyyy-MM-dd"),
          check_out: format(checkOut, "yyyy-MM-dd"),
          exclude_booking_id: excludeBookingId
        }
      });
      setAvailableRoomsForAmend(response.data || []);
    } catch (error) {
      toast.error("Failed to check room availability");
      setAvailableRoomsForAmend([]);
    } finally {
      setLoadingRoomsForAmend(false);
    }
  };

  const calculateAmendmentCost = () => {
    if (!amendBooking || !amendForm.check_in_date || !amendForm.check_out_date || amendForm.room_ids.length === 0) {
      return { oldTotal: 0, newTotal: 0, difference: 0, nights: 0 };
    }

    const nights = Math.max(1, Math.floor((amendForm.check_out_date - amendForm.check_in_date) / (1000 * 60 * 60 * 24)));
    
    console.log("=== Frontend Cost Calculation ===");
    console.log("Nights:", nights);
    console.log("Selected room IDs:", amendForm.room_ids);
    console.log("Available rooms:", availableRoomsForAmend);
    
    // Get selected rooms for amendment
    const selectedRooms = availableRoomsForAmend.filter(r => amendForm.room_ids.includes(r.id));
    console.log("Selected rooms:", selectedRooms);
    
    // Calculate new total
    let newTotal = 0;
    selectedRooms.forEach(room => {
      const isNonOrg = !amendBooking.is_org;
      let rate;
      if (room.category === "Cat I") {
        rate = isNonOrg 
          ? ((settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30))
          : settings?.cat_i_rate;
      } else {
        // Cat II Non-Org uses same rate as Cat I Non-Org (570+30=600)
        rate = isNonOrg 
          ? ((settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30))
          : settings?.cat_ii_rate;
      }
      console.log(`Room ${room.room_number} (${room.category}): ₹${rate} × ${nights} nights = ₹${rate * nights}`);
      newTotal += (rate || 0) * nights;
    });

    const oldTotal = amendBooking.total_amount || 0;
    const difference = newTotal - oldTotal;
    
    console.log("Old Total:", oldTotal);
    console.log("New Total:", newTotal);
    console.log("Difference:", difference);
    console.log("=== End Calculation ===");

    return { oldTotal, newTotal, difference, nights };
  };

  // Auto-populate additional advance when cost increases
  useEffect(() => {
    if (amendForm.check_in_date && amendForm.check_out_date && amendForm.room_ids.length > 0) {
      const cost = calculateAmendmentCost();
      if (cost.difference > 0) {
        setAmendForm(prev => ({
          ...prev,
          additional_advance: cost.difference
        }));
      } else if (cost.difference <= 0) {
        // For refunds or no change, set additional_advance to 0
        setAmendForm(prev => ({
          ...prev,
          additional_advance: 0
        }));
      }
    }
  }, [amendForm.check_in_date, amendForm.check_out_date, amendForm.room_ids, availableRoomsForAmend]);

  const handleAmendBooking = async () => {
    try {
      const costAnalysis = calculateAmendmentCost();
      
      // Only validate payment details if cost increased (refunds don't need payment validation)
      if (costAnalysis.difference > 0) {
        // Validate additional advance if cost increased
        if (amendForm.additional_advance < costAnalysis.difference) {
          toast.error(`Additional advance required: ₹${costAnalysis.difference}`);
          return;
        }

        // Validate payment details if additional advance required
        if (amendForm.additional_advance > 0) {
          if (!amendForm.payment_mode) {
            toast.error("Please select payment mode");
            return;
          }
          
          // Validate payment details based on mode
          if (amendForm.payment_mode === "UPI") {
            if (!amendForm.upi_id && !amendForm.upi_phone) {
              toast.error("Please fill UPI ID or UPI Phone");
              return;
            }
          } else if (amendForm.payment_mode === "Bank Transfer") {
            if (!amendForm.bank_name || !amendForm.bank_account) {
              toast.error("Please fill Bank Name and Account Number");
              return;
            }
          }
          // Cash mode doesn't need additional details
        }
      }

      const payload = {
        booking_id: amendBooking.id,
        check_in_date: format(amendForm.check_in_date, "yyyy-MM-dd"),
        check_out_date: format(amendForm.check_out_date, "yyyy-MM-dd"),
        room_ids: amendForm.room_ids,
        num_rooms: amendForm.num_rooms,
        total_members: amendForm.total_members,
        member_ages: amendForm.member_ages,
        additional_advance: costAnalysis.difference > 0 ? amendForm.additional_advance : 0,
        payment_mode: costAnalysis.difference > 0 ? (amendForm.payment_mode || null) : null,
        payment_id: costAnalysis.difference > 0 ? (amendForm.payment_id || null) : null,
        bank_name: costAnalysis.difference > 0 ? (amendForm.bank_name || null) : null,
        bank_ifsc: costAnalysis.difference > 0 ? (amendForm.bank_ifsc || null) : null,
        bank_account: costAnalysis.difference > 0 ? (amendForm.bank_account || null) : null,
        upi_id: costAnalysis.difference > 0 ? (amendForm.upi_id || null) : null,
        upi_phone: costAnalysis.difference > 0 ? (amendForm.upi_phone || null) : null,
        amendment_reason: amendForm.amendment_reason || null
      };

      const response = await axios.post(`${API}/bookings/amend`, payload);
      
      toast.success(`Booking amended successfully!`);
      
      // Show changes summary
      if (response.data.changes && response.data.changes.length > 0) {
        setTimeout(() => {
          toast.info(
            `Changes: ${response.data.changes.join("; ")}`,
            { duration: 8000 }
          );
        }, 500);
      }

      setShowAmend(false);
      setAmendBooking(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to amend booking");
    }
  };

  const resetGuestHistorySearch = () => {
    setGuestHistorySearch({ phone: "", aadhaar: "", name: "" });
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
      const isNonOrg = !bookingForm.is_org;  // Non-Org guests get Def Civ rates
      if (room.category === "Cat I") {
        rate = isNonOrg 
          ? ((settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30))
          : settings?.cat_i_rate;
      } else {
        // Cat II Non-Org uses same rate as Cat I Non-Org (570+30=600)
        rate = isNonOrg 
          ? ((settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30))
          : settings?.cat_ii_rate;
      }
      return total + (rate || 0);
    }, 0);
  };
  const totalRoomRate = calculateTotalRate();
  const nights = bookingForm.check_in_date && bookingForm.check_out_date
    ? Math.ceil((bookingForm.check_out_date - bookingForm.check_in_date) / (1000 * 60 * 60 * 24))
    : 0;

  const ranks = settings?.ranks || [];
  const colors = settings?.colors || ["Red", "Green", "Brown", "Orange", "Yellow", "Violet", "Black", "Blue", "White", "Light Blue"];

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
                        {booking.is_org !== undefined && (
                          <div className="flex items-center gap-1 mt-1">
                            <span className={`text-xs px-1.5 py-0.5 rounded ${booking.is_org ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'}`}>
                              {booking.is_org ? "Org" : "Non-Org"}
                            </span>
                            {booking.org_color && (
                              <span className="text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-700">
                                {booking.org_color}
                              </span>
                            )}
                          </div>
                        )}
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
                        <div className="flex gap-2 flex-wrap">
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
                                onClick={() => handleOpenAmend(booking)}
                                className="text-blue-600 border-blue-200 hover:bg-blue-50"
                                title="Amend booking (dates, rooms, party)"
                                data-testid={`amend-btn-${booking.id}`}>
                                <NotePencil size={16} className="mr-1" />Amend
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
                          {/* Delete button - available for all statuses */}
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => openDeleteDialog(booking)}
                            className="text-slate-600 border-slate-300 hover:bg-slate-100"
                            title="Permanently delete this booking"
                            data-testid={`delete-btn-${booking.id}`}>
                            <Trash size={16} />
                          </Button>
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
      <Dialog open={showNewBooking} onOpenChange={(open) => { 
        if (!open) {
          resetBookingForm(); 
        }
        setShowNewBooking(open);
      }}>
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
                
                {/* NEW: Organization Classification */}
                <div className="col-span-2">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="is-org"
                      checked={bookingForm.is_org}
                      onChange={(e) => setBookingForm({...bookingForm, is_org: e.target.checked, org_color: e.target.checked ? bookingForm.org_color : ""})}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      data-testid="checkbox-is-org"
                    />
                    <Label htmlFor="is-org" className="cursor-pointer">Organization Guest</Label>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Check if guest belongs to the organization</p>
                </div>

                {/* Color Dropdown - Only show if Org guest */}
                {bookingForm.is_org && (
                  <div>
                    <Label>Color Category</Label>
                    <Select value={bookingForm.org_color} onValueChange={(v) => setBookingForm({...bookingForm, org_color: v})}>
                      <SelectTrigger className="earms-input mt-1" data-testid="select-org-color">
                        <SelectValue placeholder="Select color (optional)" />
                      </SelectTrigger>
                      <SelectContent>
                        {colors.map(color => <SelectItem key={color} value={color}>{color}</SelectItem>)}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-slate-500 mt-1">Can be filled at check-in if unknown</p>
                  </div>
                )}

                <div>
                  <Label>Number of Rooms *</Label>
                  <Input type="number" min="1" value={bookingForm.num_rooms} onChange={(e) => setBookingForm({...bookingForm, num_rooms: parseInt(e.target.value) || 1})} onFocus={(e) => e.target.select()} className="earms-input mt-1" data-testid="input-num-rooms" />
                </div>
              </div>

              {/* NEW: Total Members and Age Fields */}
              <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-800 mb-3 text-sm">👥 Party Composition</h4>
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <Label className="text-sm">Total Members (including self) *</Label>
                    <Input 
                      type="number" 
                      min="1" 
                      max="20"
                      value={bookingForm.total_members} 
                      onChange={(e) => {
                        const count = parseInt(e.target.value) || 1;
                        const ages = Array(count).fill(0);
                        setBookingForm({...bookingForm, total_members: count, member_ages: ages});
                      }}
                      onFocus={(e) => e.target.select()} 
                      className="earms-input mt-1" 
                      data-testid="input-total-members" 
                    />
                    <p className="text-xs text-blue-600 mt-1">Total people in your party</p>
                  </div>
                </div>
                
                {/* Dynamic Age Fields */}
                {bookingForm.total_members > 0 && (
                  <div>
                    <Label className="text-xs text-slate-700 font-medium">Ages of all members:</Label>
                    <div className="grid grid-cols-5 gap-2 mt-2">
                      {bookingForm.member_ages.map((age, idx) => (
                        <div key={idx}>
                          <Input 
                            type="number" 
                            min="0" 
                            max="120"
                            value={age || ""} 
                            onChange={(e) => {
                              const newAges = [...bookingForm.member_ages];
                              newAges[idx] = parseInt(e.target.value) || 0;
                              setBookingForm({...bookingForm, member_ages: newAges});
                            }}
                            onFocus={(e) => e.target.select()} 
                            placeholder={`M${idx + 1}`}
                            className="earms-input text-sm h-9 text-center" 
                            data-testid={`input-age-${idx}`} 
                          />
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-slate-500 mt-2">M1 = Member 1 (usually the guest), M2 = Member 2, etc.</p>
                  </div>
                )}
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
                  <div className="p-3 bg-blue-50 rounded-lg mb-3 flex items-center justify-between">
                    <p className="text-sm text-blue-700 font-medium">
                      Select {bookingForm.num_rooms} room(s) — {bookingForm.room_ids.length} of {bookingForm.num_rooms} selected
                      {!bookingForm.is_org && <span className="ml-2 text-orange-600 font-semibold">(Non-Org rates apply)</span>}
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowRoomSegmentSelector(true)}
                      className="flex items-center gap-2 text-xs bg-white"
                    >
                      <CalendarBlank size={14} />
                      Mix & Match Rooms
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-56 overflow-y-auto p-1">
                    {availableRooms.map((room) => {
                      const isSelected = bookingForm.room_ids.includes(room.id);
                      const isNonOrg = !bookingForm.is_org;  // Non-Org guests get Def Civ rates
                      const rate = room.category === "Cat I"
                        ? (isNonOrg 
                            ? ((settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30))
                            : settings?.cat_i_rate)
                        : (isNonOrg 
                            ? ((settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30))
                            : settings?.cat_ii_rate);
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
                    {(() => {
                      const today = new Date();
                      today.setHours(0, 0, 0, 0);
                      const checkInDate = bookingForm.check_in_date ? new Date(bookingForm.check_in_date) : null;
                      if (checkInDate) checkInDate.setHours(0, 0, 0, 0);
                      const isSameDay = checkInDate && checkInDate.getTime() === today.getTime();
                      
                      return isSameDay ? (
                        <p className="text-xs text-green-600 font-semibold mt-1">✓ Same-day booking - No advance required</p>
                      ) : (
                        <p className="text-xs text-slate-500 mt-1">Default: ₹{settings?.default_advance_amount || 400} × {bookingForm.num_rooms} room(s)</p>
                      );
                    })()}
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
              disabled={
                !bookingForm.guest_name || 
                bookingForm.room_ids.length !== bookingForm.num_rooms || 
                !bookingForm.check_in_date || 
                !bookingForm.check_out_date || 
                (bookingForm.advance_paid > 0 && (!bookingForm.payment_mode || !isPaymentDetailsFilled()))
              }
            >
              Create Booking{bookingForm.num_rooms > 1 ? ` (${bookingForm.num_rooms} Rooms)` : ''}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== CHECK-IN DIALOG ===== */}
      <Dialog open={showCheckIn} onOpenChange={(open) => {
        if (!open) { 
          setSelectedBooking(null); 
          resetActionForm(); 
          setPhoneError("");
          setRoomGuestMapping([]);
        } else if (open && selectedBooking?.guest_contact) {
          // Pre-populate phone from booking data only when explicitly opening
          const phoneOnly = selectedBooking.guest_contact.replace(/^\+91\s*/, "").replace(/\s/g, "");
          const formatted = formatIndianPhone(phoneOnly);
          setActionForm(prev => ({ ...prev, guest_contact: formatted }));
        }
        setShowCheckIn(open);
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
                {selectedBooking.is_org !== undefined && (
                  <div className="flex items-center gap-2 mt-1 mb-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${selectedBooking.is_org ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'}`}>
                      {selectedBooking.is_org ? "Organization" : "Non-Org"}
                    </span>
                    {selectedBooking.org_color && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                        {selectedBooking.org_color}
                      </span>
                    )}
                  </div>
                )}
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
                  
                  {/* Color Category for Org guests */}
                  {selectedBooking?.is_org && (
                    <div>
                      <Label>Color Category</Label>
                      <Select value={actionForm.org_color} onValueChange={(v) => setActionForm({...actionForm, org_color: v})}>
                        <SelectTrigger className="earms-input mt-1" data-testid="select-checkin-org-color"><SelectValue placeholder="Select color" /></SelectTrigger>
                        <SelectContent>
                          {colors.map(color => <SelectItem key={color} value={color}>{color}</SelectItem>)}
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-slate-500 mt-1">Organization color classification</p>
                    </div>
                  )}
                  
                  <div>
                    <Label>Address</Label>
                    <Input value={actionForm.guest_address} onChange={(e) => setActionForm({...actionForm, guest_address: e.target.value})}
                      onFocus={(e) => e.target.select()} placeholder="Permanent/Contact address" className="earms-input mt-1" data-testid="input-checkin-address" />
                  </div>
                </div>
              </div>

              {/* Service Details section removed - no longer capturing defense information */}

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
                  Assign <strong>Self</strong> to one room and add family members to each room. If any family member lacks an <strong>Org Card</strong>, that room will be charged at <strong>Non-Org rates</strong>.
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
                            <span className={room.charge_category === "Non-Org" ? "text-red-600 font-bold ml-1" : "text-emerald-600 font-bold ml-1"}>
                              {room.charge_category}
                            </span>
                          </p>
                        </div>
                        <Badge variant={room.charge_category === "Non-Org" ? "destructive" : "default"}>
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
                        {room.has_self && selectedBooking?.is_org && !actionForm.org_color && (
                          <p className="text-xs text-amber-600 mt-1 ml-6">💡 Tip: Select Color for Org guest in Personal Details section above</p>
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
                                    <SelectItem value="father">Father</SelectItem>
                                    <SelectItem value="mother">Mother</SelectItem>
                                    <SelectItem value="brother">Brother</SelectItem>
                                    <SelectItem value="sister">Sister</SelectItem>
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

                            {/* Org Card Checkbox */}
                            <div className="flex items-center gap-2 p-2 bg-white rounded border border-slate-200">
                              <input
                                type="checkbox"
                                checked={member.has_org_card}
                                onChange={(e) => updateRoomFamilyMember(roomIdx, memberIdx, "has_org_card", e.target.checked)}
                                className="h-4 w-4"
                                id={`org-card-${roomIdx}-${memberIdx}`}
                              />
                              <label htmlFor={`org-card-${roomIdx}-${memberIdx}`} className="text-xs font-medium text-slate-700 cursor-pointer">
                                Org Card Available?
                              </label>
                            </div>
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
                        // Non-Org rates (same for both Cat I and Cat II: 570+30=600)
                        ratePerNight = (settings?.non_org_room_rent || 570) + (settings?.non_org_license_fee || 30);
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
                                  {rc.charge_category === "Non-Org" && <span className="text-red-600 font-bold ml-1">→ Non-Org</span>}
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
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="checkout-dialog">
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
                
                {/* Stay Duration Info */}
                <div className="mt-3 pt-3 border-t border-slate-200">
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="text-slate-500">Check-In Date:</span>
                      <p className="font-medium text-slate-700">
                        {selectedBooking.actual_check_in 
                          ? format(new Date(selectedBooking.actual_check_in), "dd MMM yyyy")
                          : selectedBooking.check_in_date}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500">Check-Out Date:</span>
                      <p className="font-medium text-slate-700">{format(new Date(), "dd MMM yyyy")}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Total Duration:</span>
                      <p className="font-semibold text-blue-600">
                        {(() => {
                          const checkIn = selectedBooking.actual_check_in 
                            ? new Date(selectedBooking.actual_check_in)
                            : new Date(selectedBooking.check_in_date);
                          const checkOut = new Date();
                          const nights = Math.ceil((checkOut - checkIn) / 86400000);
                          return `${nights} day${nights !== 1 ? 's' : ''}`;
                        })()}
                      </p>
                    </div>
                  </div>
                </div>
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
                      max={(() => {
                        const checkIn = selectedBooking.actual_check_in 
                          ? new Date(selectedBooking.actual_check_in)
                          : new Date(selectedBooking.check_in_date);
                        const checkOut = new Date();
                        return Math.ceil((checkOut - checkIn) / 86400000);
                      })()}
                      value={actionForm.extra_bed_days || 0}
                      onChange={(e) => {
                        const maxDays = (() => {
                          const checkIn = selectedBooking.actual_check_in 
                            ? new Date(selectedBooking.actual_check_in)
                            : new Date(selectedBooking.check_in_date);
                          const checkOut = new Date();
                          return Math.ceil((checkOut - checkIn) / 86400000);
                        })();
                        const days = parseInt(e.target.value) || 0;
                        if (days > maxDays) {
                          toast.error(`Days used cannot exceed total stay duration of ${maxDays} day${maxDays !== 1 ? 's' : ''}`);
                          return;
                        }
                        setActionForm({...actionForm, extra_bed_days: days});
                      }}
                      onFocus={(e) => e.target.select()}
                      placeholder="0"
                      className="earms-input mt-1"
                      data-testid="input-extra-bed-days"
                    />
                    <p className="text-xs text-slate-500 mt-1">Max: {(() => {
                      const checkIn = selectedBooking.actual_check_in 
                        ? new Date(selectedBooking.actual_check_in)
                        : new Date(selectedBooking.check_in_date);
                      const checkOut = new Date();
                      return Math.ceil((checkOut - checkIn) / 86400000);
                    })()} days (total stay duration)</p>
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
              
              {/* Detailed Bill Calculation */}
              {(actionForm.extra_beds_checkout > 0 || actionForm.extra_bed_days > 0 || true) && (
                <div className="p-4 bg-green-50 rounded-xl border border-green-300">
                  <h4 className="font-semibold text-green-800 mb-3">Total Bill Calculation</h4>
                  <div className="space-y-2">
                    {(() => {
                      // Calculate actual stay charges based on actual check-in to today
                      const checkInDate = selectedBooking.actual_check_in 
                        ? new Date(selectedBooking.actual_check_in)
                        : new Date(selectedBooking.check_in_date);
                      const checkOutDate = new Date(); // Today
                      const actualNights = Math.ceil((checkOutDate - checkInDate) / 86400000);
                      
                      // Get room categories and calculate rates
                      const roomCategories = selectedBooking.room_categories || [];
                      const numRooms = selectedBooking.num_rooms || selectedBooking.room_ids.length || 1;
                      const isNonOrg = !selectedBooking.is_org;
                      
                      let totalRoomCharges = 0;
                      
                      // Calculate room charges (rate INCLUDES license fee)
                      roomCategories.forEach(category => {
                        let fullRate; // Room rate + License fee
                        
                        if (category === "Cat I") {
                          // Cat I: Room Rate + License Fee
                          const roomRate = isNonOrg 
                            ? (settings?.non_org_room_rent || settings?.def_civ_cat_i_rate || 570)
                            : (settings?.cat_i_room_rent || settings?.cat_i_rate || 470);
                          const licenseFee = isNonOrg 
                            ? (settings?.non_org_license_fee || 30)
                            : (settings?.cat_i_license_fee || 30);
                          fullRate = roomRate + licenseFee;
                        } else {
                          // Cat II: Room Rate + License Fee
                          // Non-Org uses same rate as Cat I Non-Org (570+30=600)
                          const roomRate = isNonOrg
                            ? (settings?.non_org_room_rent || settings?.def_civ_cat_ii_rate || 570)
                            : (settings?.cat_ii_room_rent || settings?.cat_ii_rate || 385);
                          const licenseFee = isNonOrg 
                            ? (settings?.non_org_license_fee || 30)
                            : (settings?.cat_ii_license_fee || 15);
                          fullRate = roomRate + licenseFee;
                        }
                        
                        totalRoomCharges += fullRate * actualNights;
                      });
                      
                      // If no categories, use num_rooms
                      if (roomCategories.length === 0 && numRooms > 0) {
                        const roomRate = isNonOrg ? 570 : 470; // Default Cat I
                        const fullRate = roomRate + 30; // Add license fee
                        totalRoomCharges = fullRate * actualNights * numRooms;
                      }
                      
                      // Advance paid (to be subtracted)
                      const advancePaid = selectedBooking.advance_paid || 0;
                      
                      // Refund due from amendment (if booking was reduced)
                      const refundDue = selectedBooking.refund_due || 0;
                      
                      // ONLY use checkout extra bed charges (actual usage)
                      const extraBedActual = (actionForm.extra_beds_checkout || 0) * (actionForm.extra_bed_days || 0) * 75;
                      
                      // Final calculation: Room Charges - Advance + Extra Beds - Refund Due
                      // If refund_due exists, it means customer overpaid and needs money back
                      const amountDue = totalRoomCharges - advancePaid + extraBedActual - refundDue;
                      
                      return (
                        <>
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600">Room Charges ({actualNights} night{actualNights !== 1 ? 's' : ''} × {numRooms} room{numRooms > 1 ? 's' : ''}):</span>
                            <span className="font-medium">₹{totalRoomCharges.toFixed(0)}</span>
                          </div>
                          {advancePaid > 0 && (
                            <div className="flex justify-between text-sm text-orange-600">
                              <span>Less: Advance Paid:</span>
                              <span className="font-medium">-₹{advancePaid.toFixed(0)}</span>
                            </div>
                          )}
                          {refundDue > 0 && (
                            <div className="flex justify-between text-sm text-green-600">
                              <span>Less: Refund Due (from amendment):</span>
                              <span className="font-medium">-₹{refundDue.toFixed(0)}</span>
                            </div>
                          )}
                          {(actionForm.extra_beds_checkout > 0 && actionForm.extra_bed_days > 0) && (
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-600">Extra Beds (actual usage):</span>
                              <span className="font-medium">₹{extraBedActual} ({actionForm.extra_beds_checkout} bed{actionForm.extra_beds_checkout > 1 ? 's' : ''} × {actionForm.extra_bed_days} day{actionForm.extra_bed_days > 1 ? 's' : ''})</span>
                            </div>
                          )}
                          <div className="border-t border-green-300 pt-2 mt-2">
                            <div className="flex justify-between">
                              <span className="font-semibold text-green-900">
                                {amountDue >= 0 ? 'Amount Due at Checkout:' : 'Refund to Customer:'}
                              </span>
                              <span className={`text-xl font-bold ${amountDue >= 0 ? 'text-green-700' : 'text-red-600'}`}>
                                {amountDue >= 0 ? '₹' : '-₹'}{Math.abs(amountDue).toFixed(0)}
                              </span>
                              <input type="hidden" id="calculated-total" value={amountDue.toFixed(0)} />
                            </div>
                            {amountDue < 0 && (
                              <p className="text-xs text-red-600 mt-2">⚠️ Customer has overpaid. Please process refund of ₹{Math.abs(amountDue).toFixed(0)}</p>
                            )}
                          </div>
                        </>
                      );
                    })()}
                  </div>
                  
                  {/* Amend and Confirm Buttons */}
                  <div className="flex gap-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        // Focus on final payment input to allow manual editing
                        const finalPaymentInput = document.querySelector('input[data-testid="input-final-payment"]');
                        if (finalPaymentInput) {
                          finalPaymentInput.focus();
                          finalPaymentInput.select();
                          toast.info("You can now manually edit the payment amount");
                        }
                      }}
                      className="flex items-center gap-1"
                    >
                      <Pencil size={14} />
                      Amend Amount
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => {
                        const totalInput = document.getElementById('calculated-total');
                        const totalDue = totalInput ? parseFloat(totalInput.value) : 0;
                        setActionForm({...actionForm, final_payment: totalDue});
                        toast.success(`Amount confirmed: ₹${totalDue}`);
                      }}
                      className="flex items-center gap-1 bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle size={14} />
                      Confirm Amount
                    </Button>
                  </div>
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
                    value={actionForm.final_payment || 0}
                    onChange={(e) => setActionForm({...actionForm, final_payment: parseFloat(e.target.value) || 0})}
                    onFocus={(e) => e.target.select()}
                    className="earms-input mt-1"
                    data-testid="input-final-payment"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    Click "Confirm Amount" to auto-fill calculated total, or "Amend Amount" to edit manually
                  </p>
                </div>
                <div>
                  <Label>Payment Mode *</Label>
                  <Select value={actionForm.payment_mode} onValueChange={(v) => setActionForm({...actionForm, payment_mode: v, payment_id: ""})}>
                    <SelectTrigger className="earms-input mt-1" data-testid="select-payment-mode-checkout">
                      <SelectValue placeholder="Mode" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cash">Cash</SelectItem>
                      <SelectItem value="upi">UPI</SelectItem>
                      <SelectItem value="card">Card</SelectItem>
                      <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Payment Details Fields Based on Mode */}
              {actionForm.payment_mode === "cash" && (
                <div>
                  <Label>Cash Receipt Number *</Label>
                  <Input 
                    value={actionForm.payment_id || ""} 
                    onChange={(e) => setActionForm({...actionForm, payment_id: e.target.value})}
                    onFocus={(e) => e.target.select()} 
                    placeholder="Receipt / Voucher number" 
                    className="earms-input mt-1" 
                    data-testid="input-cash-receipt-checkout" 
                  />
                </div>
              )}

              {actionForm.payment_mode === "card" && (
                <div className="space-y-3">
                  <div>
                    <Label>Card Transaction Reference *</Label>
                    <Input 
                      value={actionForm.payment_id || ""} 
                      onChange={(e) => setActionForm({...actionForm, payment_id: e.target.value})}
                      onFocus={(e) => e.target.select()} 
                      placeholder="Card approval / transaction ID" 
                      className="earms-input mt-1" 
                      data-testid="input-card-transaction-checkout" 
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>Last 4 Digits of Card</Label>
                      <Input 
                        value={actionForm.card_last4 || ""} 
                        onChange={(e) => setActionForm({...actionForm, card_last4: e.target.value.slice(0, 4)})}
                        onFocus={(e) => e.target.select()} 
                        placeholder="XXXX" 
                        className="earms-input mt-1" 
                        maxLength={4}
                        data-testid="input-card-last4-checkout" 
                      />
                    </div>
                    <div>
                      <Label>Card Type</Label>
                      <Select 
                        value={actionForm.card_type || ""} 
                        onValueChange={(v) => setActionForm({...actionForm, card_type: v})}
                      >
                        <SelectTrigger className="earms-input mt-1">
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="visa">Visa</SelectItem>
                          <SelectItem value="mastercard">Mastercard</SelectItem>
                          <SelectItem value="rupay">RuPay</SelectItem>
                          <SelectItem value="amex">Amex</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              )}

              {actionForm.payment_mode === "upi" && (
                <div className="space-y-3">
                  <div>
                    <Label>UPI Transaction ID *</Label>
                    <Input 
                      value={actionForm.payment_id || ""} 
                      onChange={(e) => setActionForm({...actionForm, payment_id: e.target.value})}
                      onFocus={(e) => e.target.select()} 
                      placeholder="UPI Transaction/Reference ID" 
                      className="earms-input mt-1" 
                      data-testid="input-upi-transaction-checkout" 
                    />
                    <p className="text-xs text-amber-600 mt-1">⚠️ Transaction ID is unique for each payment</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>UPI ID (Optional)</Label>
                      <Input 
                        value={actionForm.upi_id || (selectedBooking.upi_id || "")} 
                        onChange={(e) => setActionForm({...actionForm, upi_id: e.target.value})}
                        onFocus={(e) => e.target.select()} 
                        placeholder="example@upi" 
                        className="earms-input mt-1 bg-slate-50" 
                        data-testid="input-upi-id-checkout" 
                      />
                      {selectedBooking.upi_id && (
                        <p className="text-xs text-green-600 mt-1">✓ Auto-filled from booking</p>
                      )}
                    </div>
                    <div>
                      <Label>UPI Phone (Optional)</Label>
                      <Input 
                        value={actionForm.upi_phone || (selectedBooking.upi_phone || "")} 
                        onChange={(e) => setActionForm({...actionForm, upi_phone: formatIndianPhone(e.target.value)})}
                        onFocus={(e) => e.target.select()} 
                        placeholder="10-digit mobile" 
                        className="earms-input mt-1 bg-slate-50" 
                        maxLength={11}
                        data-testid="input-upi-phone-checkout" 
                      />
                      {selectedBooking.upi_phone && (
                        <p className="text-xs text-green-600 mt-1">✓ Auto-filled from booking</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {actionForm.payment_mode === "bank_transfer" && (
                <div className="space-y-3">
                  <div>
                    <Label>Bank Transfer Reference *</Label>
                    <Input 
                      value={actionForm.payment_id || ""} 
                      onChange={(e) => setActionForm({...actionForm, payment_id: e.target.value})}
                      onFocus={(e) => e.target.select()} 
                      placeholder="NEFT/IMPS/RTGS reference" 
                      className="earms-input mt-1" 
                      data-testid="input-bank-transfer-checkout" 
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>Bank Name</Label>
                      <Input 
                        value={actionForm.bank_name || (selectedBooking.bank_name || "")} 
                        onChange={(e) => setActionForm({...actionForm, bank_name: e.target.value})}
                        onFocus={(e) => e.target.select()} 
                        placeholder="Bank name" 
                        className="earms-input mt-1 bg-slate-50" 
                        data-testid="input-bank-name-checkout" 
                      />
                      {selectedBooking.bank_name && (
                        <p className="text-xs text-green-600 mt-1">✓ Auto-filled from booking</p>
                      )}
                    </div>
                    <div>
                      <Label>IFSC Code</Label>
                      <Input 
                        value={actionForm.bank_ifsc || (selectedBooking.bank_ifsc || "")} 
                        onChange={(e) => setActionForm({...actionForm, bank_ifsc: toUpperCase(e.target.value)})}
                        onFocus={(e) => e.target.select()} 
                        placeholder="e.g., SBIN0001234" 
                        className="earms-input mt-1 bg-slate-50" 
                        maxLength={11}
                        data-testid="input-bank-ifsc-checkout" 
                      />
                      {selectedBooking.bank_ifsc && (
                        <p className="text-xs text-green-600 mt-1">✓ Auto-filled from booking</p>
                      )}
                    </div>
                  </div>
                  <div>
                    <Label>Account Number</Label>
                    <Input 
                      value={actionForm.bank_account || (selectedBooking.bank_account || "")} 
                      onChange={(e) => setActionForm({...actionForm, bank_account: e.target.value})}
                      onFocus={(e) => e.target.select()} 
                      placeholder="Account number" 
                      className="earms-input mt-1 bg-slate-50" 
                      data-testid="input-bank-account-checkout" 
                    />
                    {selectedBooking.bank_account && (
                      <p className="text-xs text-green-600 mt-1">✓ Auto-filled from booking</p>
                    )}
                  </div>
                </div>
              )}
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
            <Button 
              onClick={handleProceedToFeedback} 
              className="bg-blue-500 hover:bg-blue-600" 
              data-testid="confirm-checkout"
              disabled={(() => {
                // Basic validation
                if (!actionForm.payment_mode || !actionForm.final_payment || actionForm.final_payment === 0) {
                  return true;
                }
                
                // Mode-specific validation
                if (actionForm.payment_mode === "UPI") {
                  // Require transaction ID for UPI
                  return !actionForm.payment_id || actionForm.payment_id.trim() === "";
                }
                
                if (actionForm.payment_mode === "Card") {
                  // Require transaction ID for Card
                  return !actionForm.payment_id || actionForm.payment_id.trim() === "";
                }
                
                if (actionForm.payment_mode === "Bank Transfer") {
                  // Require transaction ID for Bank Transfer
                  return !actionForm.payment_id || actionForm.payment_id.trim() === "";
                }
                
                // Cash mode doesn't require transaction ID
                return false;
              })()}
            >
              Proceed to Feedback
            </Button>
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
                      <span className="font-medium">{Math.round(refundInfo.hours_until_checkin / 24)} days</span>
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
              disabled={!refundInfo || !actionForm.reason || actionForm.reason.trim() === ""}
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
              <p className="text-sm text-slate-600">Search by any of the following (at least one required)</p>
              
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
                  <Label>Aadhaar Number</Label>
                  <Input
                    value={guestHistorySearch.aadhaar}
                    onChange={(e) => setGuestHistorySearch(prev => ({ ...prev, aadhaar: e.target.value.replace(/\D/g, '').slice(0, 12) }))}
                    onFocus={(e) => e.target.select()}
                    placeholder="12-digit Aadhaar number"
                    className="earms-input mt-1"
                    data-testid="history-aadhaar-input"
                    maxLength={12}
                  />
                </div>
                <div className="col-span-2">
                  <Label>Guest Name</Label>
                  <Input
                    value={guestHistorySearch.name}
                    onChange={(e) => setGuestHistorySearch(prev => ({ ...prev, name: e.target.value }))}
                    onFocus={(e) => e.target.select()}
                    placeholder="Full or partial name"
                    className="earms-input mt-1"
                    data-testid="history-name-input"
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
                    {guestHistoryData.guest_info.is_org !== undefined && (
                      <div>
                        <p className="text-slate-500">Classification</p>
                        <p className="font-medium text-slate-800">{guestHistoryData.guest_info.is_org ? "Organization" : "Non-Organization"}</p>
                      </div>
                    )}
                    {guestHistoryData.guest_info.org_color && (
                      <div>
                        <p className="text-slate-500">Color</p>
                        <p className="font-medium text-slate-800">{guestHistoryData.guest_info.org_color}</p>
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
${createdBookingData.is_org !== undefined ? `• Type: ${createdBookingData.is_org ? "Organization" : "Non-Organization"}\n` : ""}${createdBookingData.org_color ? `• Color: ${createdBookingData.org_color}\n` : ""}• Room(s): ${(createdBookingData.room_numbers || []).join(", ")}
• Category: ${(createdBookingData.room_categories || []).filter((v, i, arr) => arr.indexOf(v) === i).join(", ")}

📅 *Stay Period:*
• Check-in: ${format(parseISO(createdBookingData.check_in_date), "dd MMM yyyy")} - 1300h
• Check-out: ${format(parseISO(createdBookingData.check_out_date), "dd MMM yyyy")} - 0800h

💰 *Payment:*
• Total Amount: ₹${createdBookingData.total_amount}
• Advance Paid: ₹${createdBookingData.advance_paid}
• Balance Due: ₹${createdBookingData.balance_amount}

*Guidelines for guests pl*
1. Pl carry aadhar card as ID proof for smooth check in. *Non-Org guests and unaccompanied guests* are not allowed without organization member. Org Card & Aadhar card required for verification.
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
1. Pl carry aadhar card as ID proof for smooth check in. *Non-Org guests and unaccompanied guests* are not allowed without organization member. Org Card & Aadhar card required for verification.
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

      {/* ===== DELETE CONFIRMATION DIALOG ===== */}
      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent data-testid="delete-confirm-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <WarningCircle size={24} weight="fill" />
              Permanently Delete Booking?
            </DialogTitle>
          </DialogHeader>
          {bookingToDelete && (
            <div className="space-y-4 py-4">
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
                <p className="font-semibold text-red-900">{bookingToDelete.guest_name}</p>
                <p className="text-sm text-red-700">Booking #{bookingToDelete.booking_number}</p>
                <p className="text-sm text-red-700">Rooms: {getRoomDisplay(bookingToDelete)}</p>
                <p className="text-sm text-red-700">
                  {format(parseISO(bookingToDelete.check_in_date), "dd MMM yyyy")} - {format(parseISO(bookingToDelete.check_out_date), "dd MMM yyyy")}
                </p>
              </div>

              <div className="p-4 bg-amber-50 border border-amber-300 rounded-xl">
                <div className="flex gap-2 items-start">
                  <WarningCircle size={20} className="text-amber-600 flex-shrink-0 mt-0.5" weight="bold" />
                  <div className="text-sm text-amber-900">
                    <p className="font-semibold mb-1">This action cannot be undone!</p>
                    <ul className="list-disc list-inside space-y-1 text-amber-800">
                      <li>Booking will be permanently removed from the database</li>
                      <li>All associated data (payments, refunds) will be deleted</li>
                      <li>Rooms will be freed for future bookings</li>
                      <li>This is NOT a cancellation - use Cancel for normal cancellations</li>
                    </ul>
                  </div>
                </div>
              </div>

              <p className="text-sm text-slate-600">
                <strong>Use this only for:</strong> Wrong entries, duplicate bookings, or test data that needs complete removal.
              </p>
            </div>
          )}
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => {
                setShowDeleteConfirm(false);
                setBookingToDelete(null);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleDeleteBooking}
              variant="destructive"
              className="bg-red-600 hover:bg-red-700"
              data-testid="confirm-delete-btn"
            >
              <Trash size={16} className="mr-2" />
              Delete Permanently
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== AMEND BOOKING DIALOG ===== */}
      {console.log("Rendering amend dialog, showAmend:", showAmend, "amendBooking:", amendBooking)}
      <Dialog open={showAmend} onOpenChange={(open) => {
        console.log("Amendment dialog onOpenChange called, open:", open);
        if (!open) {
          setAmendBooking(null);
          setAvailableRoomsForAmend([]);
        }
        setShowAmend(open);
      }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <NotePencil size={24} className="text-blue-500" />
              Amend Booking
            </DialogTitle>
          </DialogHeader>
          
          {amendBooking && (
            <div className="space-y-6 py-4">
              {/* Current Booking Info */}
              <div className="p-4 bg-slate-50 rounded-lg border">
                <h4 className="font-semibold text-sm mb-2">Current Booking</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-slate-600">Booking:</span> <span className="font-medium">{amendBooking.booking_number}</span></div>
                  <div><span className="text-slate-600">Guest:</span> <span className="font-medium">{amendBooking.guest_name}</span></div>
                  <div><span className="text-slate-600">Check-in:</span> {format(parseISO(amendBooking.check_in_date), "dd MMM yyyy")}</div>
                  <div><span className="text-slate-600">Check-out:</span> {format(parseISO(amendBooking.check_out_date), "dd MMM yyyy")}</div>
                  <div><span className="text-slate-600">Rooms:</span> {amendBooking.room_numbers?.join(", ")}</div>
                  <div><span className="text-slate-600">Amount:</span> <span className="font-medium">₹{amendBooking.total_amount}</span></div>
                </div>
              </div>

              {/* Amendment Form */}
              <div className="space-y-4">
                <h4 className="font-semibold text-sm">Amend Details</h4>
                
                {/* Dates */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Check-in Date</Label>
                    <Popover open={amendCheckInOpen} onOpenChange={setAmendCheckInOpen}>
                      <PopoverTrigger asChild>
                        <Button variant="outline" className="w-full mt-1 justify-start text-left font-normal">
                          <CalendarBlank size={18} className="mr-2" />
                          {amendForm.check_in_date ? format(amendForm.check_in_date, "dd MMM yyyy") : "Select date"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={amendForm.check_in_date}
                          onSelect={(date) => {
                            setAmendForm({...amendForm, check_in_date: date, check_out_date: null, room_ids: []});
                            setAmendCheckInOpen(false);
                            if (date && amendForm.check_out_date) {
                              fetchAvailableRoomsForAmend(date, amendForm.check_out_date, amendBooking.id);
                            }
                          }}
                          disabled={(date) => date < new Date(new Date().setHours(0,0,0,0))}
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                  
                  <div>
                    <Label>Check-out Date</Label>
                    <Popover open={amendCheckOutOpen} onOpenChange={setAmendCheckOutOpen}>
                      <PopoverTrigger asChild>
                        <Button variant="outline" className="w-full mt-1 justify-start text-left font-normal" disabled={!amendForm.check_in_date}>
                          <CalendarBlank size={18} className="mr-2" />
                          {amendForm.check_out_date ? format(amendForm.check_out_date, "dd MMM yyyy") : "Select date"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={amendForm.check_out_date}
                          onSelect={(date) => {
                            setAmendForm({...amendForm, check_out_date: date});
                            setAmendCheckOutOpen(false);
                            if (amendForm.check_in_date && date) {
                              fetchAvailableRoomsForAmend(amendForm.check_in_date, date, amendBooking.id);
                            }
                          }}
                          disabled={(date) => !amendForm.check_in_date || date <= amendForm.check_in_date}
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>

                {/* Room Selection */}
                {loadingRoomsForAmend ? (
                  <div className="text-center py-4 text-slate-500">Loading available rooms...</div>
                ) : availableRoomsForAmend.length > 0 ? (
                  <div>
                    <Label>Select Rooms ({amendForm.room_ids.length} selected)</Label>
                    <div className="grid grid-cols-3 gap-2 mt-2 max-h-48 overflow-y-auto p-2 border rounded">
                      {availableRoomsForAmend.map(room => (
                        <div
                          key={room.id}
                          onClick={() => {
                            const isSelected = amendForm.room_ids.includes(room.id);
                            setAmendForm({
                              ...amendForm,
                              room_ids: isSelected 
                                ? amendForm.room_ids.filter(id => id !== room.id)
                                : [...amendForm.room_ids, room.id],
                              num_rooms: isSelected ? amendForm.room_ids.length - 1 : amendForm.room_ids.length + 1
                            });
                          }}
                          className={`p-2 border rounded cursor-pointer text-center text-sm ${
                            amendForm.room_ids.includes(room.id) 
                              ? 'bg-blue-100 border-blue-500' 
                              : 'hover:bg-slate-50'
                          }`}
                        >
                          <div className="font-medium">{room.room_number}</div>
                          <div className="text-xs text-slate-600">{room.category}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : amendForm.check_in_date && amendForm.check_out_date ? (
                  <div className="text-center py-4 text-slate-500">No rooms available for selected dates</div>
                ) : null}

                {/* Party Composition */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Total Members</Label>
                    <Input
                      type="number"
                      min="1"
                      value={amendForm.total_members}
                      onChange={(e) => {
                        const count = parseInt(e.target.value) || 1;
                        const newAges = Array(count).fill(0).map((_, i) => amendForm.member_ages[i] || 0);
                        setAmendForm({...amendForm, total_members: count, member_ages: newAges});
                      }}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Member Ages (comma-separated)</Label>
                    <Input
                      value={amendForm.member_ages.join(", ")}
                      onChange={(e) => {
                        const ages = e.target.value.split(",").map(a => parseInt(a.trim()) || 0);
                        setAmendForm({...amendForm, member_ages: ages});
                      }}
                      placeholder="30, 28, 5, 3"
                      className="mt-1"
                    />
                  </div>
                </div>

                {/* Cost Analysis */}
                {amendForm.room_ids.length > 0 && amendForm.check_in_date && amendForm.check_out_date && (
                  <div className="p-4 bg-slate-50 rounded-lg border">
                    <h4 className="font-semibold text-sm mb-2">Cost Analysis</h4>
                    {(() => {
                      const cost = calculateAmendmentCost();
                      return (
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span>Current Amount:</span>
                            <span className="font-medium">₹{cost.oldTotal}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>New Amount ({cost.nights} nights):</span>
                            <span className="font-medium">₹{cost.newTotal}</span>
                          </div>
                          <div className={`flex justify-between pt-2 border-t font-semibold ${
                            cost.difference > 0 ? 'text-red-600' : cost.difference < 0 ? 'text-green-600' : ''
                          }`}>
                            <span>Difference:</span>
                            <span>{cost.difference > 0 ? '+' : ''}₹{cost.difference}</span>
                          </div>
                          {cost.difference > 0 && (
                            <p className="text-xs text-amber-600 mt-2">⚠️ Additional advance payment required</p>
                          )}
                          {cost.difference < 0 && (
                            <div className="mt-2 p-2 bg-green-50 rounded border border-green-200">
                              <p className="text-xs text-green-700 font-medium">✓ Amount reduced by ₹{Math.abs(cost.difference)}</p>
                              <p className="text-xs text-green-600 mt-1">This refund will be deducted from the final checkout bill</p>
                            </div>
                          )}
                          {cost.difference === 0 && (
                            <p className="text-xs text-blue-600 mt-2">✓ No payment change required</p>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                )}

                {/* Payment Section (if cost increased) */}
                {calculateAmendmentCost().difference > 0 && (
                  <div className="space-y-3 p-4 border rounded-lg">
                    <h4 className="font-semibold text-sm">Additional Payment</h4>
                    <div>
                      <Label>Additional Advance (₹)</Label>
                      <Input
                        type="number"
                        min="0"
                        value={amendForm.additional_advance}
                        onChange={(e) => setAmendForm({...amendForm, additional_advance: parseFloat(e.target.value) || 0})}
                        className="mt-1"
                      />
                      <p className="text-xs text-slate-500 mt-1">Required: ₹{calculateAmendmentCost().difference}</p>
                    </div>
                    
                    <div>
                      <Label>Payment Mode</Label>
                      <Select value={amendForm.payment_mode} onValueChange={(v) => setAmendForm({...amendForm, payment_mode: v, payment_id: ""})}>
                        <SelectTrigger className="mt-1">
                          <SelectValue placeholder="Select payment mode" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Cash">Cash</SelectItem>
                          <SelectItem value="UPI">UPI</SelectItem>
                          <SelectItem value="Bank Transfer">Bank Transfer</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {amendForm.payment_mode === "UPI" && (
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label>UPI ID</Label>
                          <Input value={amendForm.upi_id} onChange={(e) => setAmendForm({...amendForm, upi_id: e.target.value})} className="mt-1" />
                        </div>
                        <div>
                          <Label>UPI Phone</Label>
                          <Input value={amendForm.upi_phone} onChange={(e) => setAmendForm({...amendForm, upi_phone: e.target.value})} className="mt-1" />
                        </div>
                      </div>
                    )}

                    {amendForm.payment_mode === "Bank Transfer" && (
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label>Bank Name</Label>
                          <Input value={amendForm.bank_name} onChange={(e) => setAmendForm({...amendForm, bank_name: e.target.value})} className="mt-1" />
                        </div>
                        <div>
                          <Label>Account Number</Label>
                          <Input value={amendForm.bank_account} onChange={(e) => setAmendForm({...amendForm, bank_account: e.target.value})} className="mt-1" />
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Amendment Reason */}
                <div>
                  <Label>Reason for Amendment (Optional)</Label>
                  <Textarea
                    value={amendForm.amendment_reason}
                    onChange={(e) => setAmendForm({...amendForm, amendment_reason: e.target.value})}
                    placeholder="e.g., Guest requested date change"
                    className="mt-1"
                    rows={2}
                  />
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAmend(false)}>Cancel</Button>
            <Button 
              onClick={handleAmendBooking}
              className="bg-blue-500 hover:bg-blue-600"
              disabled={!amendForm.check_in_date || !amendForm.check_out_date || amendForm.room_ids.length === 0}
            >
              Confirm Amendment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Mix & Match Room Segment Selector Dialog */}
      <Dialog open={showRoomSegmentSelector} onOpenChange={setShowRoomSegmentSelector}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CalendarBlank size={24} className="text-blue-500" />
              Mix & Match Rooms - Smart Room Allocation
            </DialogTitle>
          </DialogHeader>
          
          {bookingForm.check_in_date && bookingForm.check_out_date && (
            <RoomSegmentSelector
              checkInDate={bookingForm.check_in_date}
              checkOutDate={bookingForm.check_out_date}
              numRooms={bookingForm.num_rooms}
              isOrg={bookingForm.is_org}
              settings={settings}
              onAccept={(segmentData) => {
                setBookingForm({
                  ...bookingForm,
                  room_segments: segmentData.room_segments,
                  has_room_changes: segmentData.has_room_changes,
                  room_ids: [] // Clear traditional room_ids when using segments
                });
                setUseSegmentedBooking(true);
                setShowRoomSegmentSelector(false);
                toast.success('Room combination selected successfully!');
              }}
              onCancel={() => setShowRoomSegmentSelector(false)}
            />
          )}
        </DialogContent>
      </Dialog>


    </div>
  );
}
