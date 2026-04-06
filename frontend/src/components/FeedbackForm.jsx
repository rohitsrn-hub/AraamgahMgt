import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { format } from "date-fns";
import axios from "axios";
import { API } from "@/App";
import { toast } from "sonner";

const RATINGS = [
  {
    key: "cleanliness",
    en: "Cleanliness",
    hi: "Swachhata / स्वच्छता"
  },
  {
    key: "room_comfort",
    en: "Room Comfort",
    hi: "Kamre Ki Gunvatta / कमरे की गुणवत्ता"
  },
  {
    key: "basic_amenities",
    en: "Basic Amenities Provided",
    hi: "Khane Ki Gunvatta / खाने की गुणवत्ता"
  },
  {
    key: "check_in_procedure",
    en: "Check-In Procedure",
    hi: "Check-In Prakriya / चेक-इन प्रक्रिया"
  },
  {
    key: "check_out_procedure",
    en: "Check-Out Procedure",
    hi: "Check-Out Prakriya / चेक-आउट प्रक्रिया"
  },
  {
    key: "overall_stay",
    en: "Overall Stay Experience",
    hi: "Samagra Pravas Anubhav / समग्र प्रवास अनुभव"
  },
  {
    key: "staff_behaviour",
    en: "Staff Behaviour",
    hi: "Staff Vyavhar / स्टाफ व्यवहार"
  }
];

function RatingRow({ item, value, onChange }) {
  return (
    <div className="grid grid-cols-12 gap-2 items-center py-2 border-b border-slate-100">
      <div className="col-span-5">
        <p className="text-sm font-medium text-slate-800">{item.en}</p>
        <p className="text-xs text-slate-500">{item.hi}</p>
      </div>
      <div className="col-span-7 flex gap-2">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onChange(n)}
            className={`w-8 h-8 rounded-full border-2 text-sm font-bold transition-all
              ${value === n
                ? n <= 2 ? "bg-red-500 border-red-500 text-white"
                  : n === 3 ? "bg-amber-500 border-amber-500 text-white"
                  : "bg-emerald-500 border-emerald-500 text-white"
                : "border-slate-300 text-slate-500 hover:border-blue-400 hover:text-blue-600 bg-white"
              }`}
            data-testid={`rating-${item.key}-${n}`}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function FeedbackForm({ booking, open, onClose, onSubmitted }) {
  const [ratings, setRatings] = useState({
    cleanliness: 0,
    room_comfort: 0,
    basic_amenities: 0,
    check_in_procedure: 0,
    check_out_procedure: 0,
    overall_stay: 0,
    staff_behaviour: 0
  });
  const [enjoyedMost, setEnjoyedMost] = useState("");
  const [issues, setIssues] = useState("");
  const [improvements, setImprovements] = useState("");
  const [additionalComments, setAdditionalComments] = useState("");
  const [wouldRecommend, setWouldRecommend] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const allRated = Object.values(ratings).every((v) => v > 0);
  const canSubmit = allRated && wouldRecommend !== null;

  const handleSubmit = async () => {
    if (!canSubmit) {
      toast.error("Please fill all ratings and recommendation before submitting");
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/feedback`, {
        booking_id: booking.id,
        ...ratings,
        enjoyed_most: enjoyedMost,
        issues_problems: issues,
        improvement_suggestions: improvements,
        additional_comments: additionalComments,
        would_recommend: wouldRecommend
      });
      toast.success("Feedback submitted successfully!");
      onSubmitted();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit feedback");
    } finally {
      setSubmitting(false);
    }
  };

  const today = format(new Date(), "dd MMM yyyy");
  
  // Use actual check-in date and today (checkout date) instead of booked dates
  const actualCheckInDate = booking?.actual_check_in || booking?.check_in_date;
  const actualCheckOutDate = format(new Date(), "dd MMM yyyy"); // Today is checkout date
  
  const checkInFormatted = actualCheckInDate ? format(new Date(actualCheckInDate), "dd MMM yyyy") : "";
  const checkOutFormatted = actualCheckOutDate;
  
  // Calculate actual nights stayed (from check-in to today)
  const duration = actualCheckInDate
    ? `${Math.ceil((new Date() - new Date(actualCheckInDate)) / 86400000)} Night(s)`
    : "";

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[92vh] overflow-y-auto" data-testid="feedback-dialog">
        <DialogHeader>
          <DialogTitle className="text-center text-lg font-bold text-slate-800">
            <div className="flex flex-col items-center gap-1">
              <span>GUEST FEEDBACK FORM</span>
              <span className="text-base font-normal text-slate-500">ATITHI PRATIKRIYA PRAPATRA / अतिथि प्रतिक्रिया प्रपत्र</span>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-5 py-2 text-sm">
          {/* Section 1: Personal Information */}
          <div className="p-4 bg-slate-50 rounded-xl">
            <div className="grid grid-cols-2 gap-1 mb-1">
              <h3 className="font-semibold text-slate-700">1. Personal Information</h3>
              <h3 className="font-semibold text-slate-500 text-xs">Vyaktigat Jankari / व्यक्तिगत जानकारी</h3>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-2">
              <div className="flex justify-between border-b border-dotted border-slate-300 pb-1">
                <span className="text-slate-600 text-xs">Rank &amp; Name / Rank &amp; Naam:</span>
                <span className="font-medium text-xs text-slate-800">{booking?.guest_rank ? `${booking.guest_rank} ` : ""}{booking?.guest_name}</span>
              </div>
              <div className="flex justify-between border-b border-dotted border-slate-300 pb-1">
                <span className="text-slate-600 text-xs">Serving/Retired / Sevarat:</span>
                <span className="font-medium text-xs text-slate-800">{booking?.guest_service_status || "—"}</span>
              </div>
              <div className="flex justify-between border-b border-dotted border-slate-300 pb-1">
                <span className="text-slate-600 text-xs">Unit:</span>
                <span className="font-medium text-xs text-slate-800">{booking?.guest_unit || "—"}</span>
              </div>
              <div className="flex justify-between border-b border-dotted border-slate-300 pb-1">
                <span className="text-slate-600 text-xs">Phone No:</span>
                <span className="font-medium text-xs text-slate-800">{booking?.guest_contact || "—"}</span>
              </div>
            </div>
          </div>

          {/* Section 2: Visit Details */}
          <div className="p-4 bg-slate-50 rounded-xl">
            <div className="grid grid-cols-2 gap-1 mb-2">
              <h3 className="font-semibold text-slate-700">2. Visit Details</h3>
              <h3 className="font-semibold text-slate-500 text-xs">Yatra Vivaran / यात्रा विवरण</h3>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
              <div className="flex justify-between border-b border-dotted border-slate-300 pb-1">
                <span className="text-slate-600 text-xs">Date of Visit / Visit Ki Tarikh:</span>
                <span className="text-xs font-medium text-slate-800">{checkInFormatted} to {checkOutFormatted}</span>
              </div>
              <div className="flex justify-between border-b border-dotted border-slate-300 pb-1">
                <span className="text-slate-600 text-xs">Duration / Rahane Ki Avadhi:</span>
                <span className="text-xs font-medium text-slate-800">{duration}</span>
              </div>
            </div>
          </div>

          {/* Section 3: Satisfaction Ratings */}
          <div className="p-4 bg-white rounded-xl border border-slate-200">
            <div className="mb-3">
              <h3 className="font-semibold text-slate-700">3. Satisfaction Rating</h3>
              <p className="text-xs text-slate-500">
                1 = Very Dissatisfied / Bahut Asantusht &nbsp;•&nbsp; 5 = Very Satisfied / Bahut Santusht
              </p>
              <p className="text-xs text-slate-400">
                Santushi Rating (Apni Pasnad ke Nusar ✓ Kare)
              </p>
            </div>
            <div className="space-y-1">
              {RATINGS.map((item) => (
                <RatingRow
                  key={item.key}
                  item={item}
                  value={ratings[item.key]}
                  onChange={(v) => setRatings((prev) => ({ ...prev, [item.key]: v }))}
                />
              ))}
            </div>
            {!allRated && (
              <p className="text-xs text-red-500 mt-2">* Please rate all 7 categories / Kripya sabhi 7 vibhag rate kare</p>
            )}
          </div>

          {/* Section 4: Specific Feedback */}
          <div className="p-4 bg-white rounded-xl border border-slate-200">
            <h3 className="font-semibold text-slate-700 mb-1">4. Specific Feedback / Vishishi Pratikriya</h3>
            <div className="space-y-3">
              <div>
                <Label className="text-xs text-slate-700">
                  What did you enjoy most about your stay?
                  <span className="block text-slate-400">Aapne apne visit ki dohran kisi chiz ka adhik anand liya?</span>
                </Label>
                <Textarea
                  value={enjoyedMost}
                  onChange={(e) => setEnjoyedMost(e.target.value)}
                  placeholder="Please share what you liked most..."
                  className="mt-1 text-sm"
                  rows={2}
                  data-testid="feedback-enjoyed"
                />
              </div>
              <div>
                <Label className="text-xs text-slate-700">
                  Were there any issues or problems during your stay?
                  <span className="block text-slate-400">Kya aapne visit ki dohran kisi prakar ki koe dikat ya parishani ka anubhav kiya?</span>
                </Label>
                <Textarea
                  value={issues}
                  onChange={(e) => setIssues(e.target.value)}
                  placeholder="Please describe any issues..."
                  className="mt-1 text-sm"
                  rows={2}
                  data-testid="feedback-issues"
                />
              </div>
              <div>
                <Label className="text-xs text-slate-700">
                  How can we improve your experience for future visits?
                  <span className="block text-slate-400">Ham bhavishya ki vijit ki liye aapke anubhav ko kaise behtar bana sakte hai?</span>
                </Label>
                <Textarea
                  value={improvements}
                  onChange={(e) => setImprovements(e.target.value)}
                  placeholder="Your suggestions..."
                  className="mt-1 text-sm"
                  rows={2}
                  data-testid="feedback-improvements"
                />
              </div>
            </div>
          </div>

          {/* Section 5: Additional Comments */}
          <div className="p-4 bg-white rounded-xl border border-slate-200">
            <h3 className="font-semibold text-slate-700 mb-2">5. Additional Comments / Atiriki Tippaniya</h3>
            <Textarea
              value={additionalComments}
              onChange={(e) => setAdditionalComments(e.target.value)}
              placeholder="Any additional comments..."
              className="text-sm"
              rows={2}
              data-testid="feedback-additional"
            />
          </div>

          {/* Section 6: Recommendation */}
          <div className="p-4 bg-white rounded-xl border border-slate-200">
            <h3 className="font-semibold text-slate-700 mb-2">
              6. Would you recommend us to others?
              <span className="block text-xs font-normal text-slate-400">Kya aap dusroko hamari anushansa karenge?</span>
            </h3>
            <div className="flex gap-6">
              <button
                type="button"
                onClick={() => setWouldRecommend(true)}
                className={`flex items-center gap-2 px-5 py-2 rounded-xl border-2 font-medium text-sm transition-all
                  ${wouldRecommend === true ? "bg-emerald-500 border-emerald-500 text-white" : "border-slate-200 text-slate-600 hover:border-emerald-300"}`}
                data-testid="recommend-yes"
              >
                [ ✓ ] Yes / Ha
              </button>
              <button
                type="button"
                onClick={() => setWouldRecommend(false)}
                className={`flex items-center gap-2 px-5 py-2 rounded-xl border-2 font-medium text-sm transition-all
                  ${wouldRecommend === false ? "bg-red-500 border-red-500 text-white" : "border-slate-200 text-slate-600 hover:border-red-300"}`}
                data-testid="recommend-no"
              >
                [ ✗ ] No / Nahi
              </button>
            </div>
          </div>

          {/* Date & Signature Line */}
          <div className="flex justify-between items-end px-2 pt-2">
            <div className="border-b border-slate-300 pb-1">
              <p className="text-xs text-slate-500">Date / Tarikh: {today}</p>
            </div>
            <div className="border-b border-slate-300 pb-1 min-w-32">
              <p className="text-xs text-slate-500 text-right">(Signature of Guest / Atithi ka hastakshar)</p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} data-testid="feedback-cancel">
            Fill Later
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit || submitting}
            className="bg-blue-600 hover:bg-blue-700"
            data-testid="feedback-submit"
          >
            {submitting ? "Submitting..." : "Submit Feedback & Complete Checkout"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
