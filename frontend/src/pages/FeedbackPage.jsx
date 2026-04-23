import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { format } from "date-fns";
import { toast } from "sonner";
import { ChartBar, Star, ThumbsUp, Users, Printer } from "@phosphor-icons/react";
import jsPDF from "jspdf";
import "jspdf-autotable";

const CATEGORY_LABELS = {
  cleanliness: { en: "Cleanliness", hi: "Swachhata" },
  room_comfort: { en: "Room Comfort", hi: "Kamre Ki Gunvatta" },
  basic_amenities: { en: "Basic Amenities", hi: "Khane Ki Gunvatta" },
  check_in_procedure: { en: "Check-In Procedure", hi: "Check-In Prakriya" },
  check_out_procedure: { en: "Check-Out Procedure", hi: "Check-Out Prakriya" },
  overall_stay: { en: "Overall Stay", hi: "Samagra Pravas" },
  staff_behaviour: { en: "Staff Behaviour", hi: "Staff Vyavhar" }
};

function ScoreBar({ score, maxScore = 5 }) {
  const pct = (score / maxScore) * 100;
  const color = score >= 4 ? "bg-emerald-500" : score >= 2.5 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-slate-100 rounded-full h-3 overflow-hidden">
        <div className={`${color} h-3 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-bold text-slate-700 w-8 text-right">{score}</span>
    </div>
  );
}

function SentimentEmoji({ score }) {
  if (score >= 4) return <span className="text-4xl" data-testid="sentiment-emoji-happy">😊</span>;
  if (score >= 2.5) return <span className="text-4xl" data-testid="sentiment-emoji-neutral">😐</span>;
  return <span className="text-4xl" data-testid="sentiment-emoji-sad">😢</span>;
}

function getSentimentColor(score) {
  if (score >= 4) return { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-800", badge: "bg-emerald-100 text-emerald-800" };
  if (score >= 2.5) return { bg: "bg-orange-50", border: "border-orange-200", text: "text-orange-800", badge: "bg-orange-100 text-orange-800" };
  return { bg: "bg-red-50", border: "border-red-200", text: "text-red-800", badge: "bg-red-100 text-red-800" };
}

export default function FeedbackPage() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalysis = async () => {
    try {
      const res = await axios.get(`${API}/feedback/analysis`);
      setAnalysis(res.data);
    } catch (error) {
      toast.error("Failed to load feedback analysis");
    } finally {
      setLoading(false);
    }
  };

  const printFeedback = (fb) => {
    const doc = new jsPDF('p', 'mm', 'a4');
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 15;
    let yPos = 20;

    // Header
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.text('GUEST FEEDBACK FORM', pageWidth / 2, yPos, { align: 'center' });
    
    yPos += 6;
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('ATITHI PRATIKRIYA PRAPATRA / अतिथि प्रतिक्रिया प्रपत्र', pageWidth / 2, yPos, { align: 'center' });
    
    yPos += 10;
    
    // Section 1: Personal Information
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('1. Personal Information / Vyaktigat Jankari', margin, yPos);
    yPos += 7;
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    const personalInfo = [
      ['Rank & Name:', `${fb.guest_rank || ''} ${fb.guest_name || ''}`],
      ['Service Status:', fb.service_status || '—'],
      ['Unit:', fb.guest_unit || '—'],
      ['Phone:', fb.guest_contact || '—']
    ];
    
    personalInfo.forEach(([label, value]) => {
      doc.text(label, margin, yPos);
      doc.text(value, margin + 50, yPos);
      yPos += 6;
    });
    
    yPos += 3;
    
    // Section 2: Visit Details
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('2. Visit Details / Yatra Vivaran', margin, yPos);
    yPos += 7;
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('Date of Visit:', margin, yPos);
    doc.text(`${fb.check_in_date} to ${fb.check_out_date}`, margin + 50, yPos);
    yPos += 6;
    
    const nights = Math.ceil((new Date(fb.check_out_date) - new Date(fb.check_in_date)) / 86400000);
    doc.text('Duration:', margin, yPos);
    doc.text(`${nights} Night(s)`, margin + 50, yPos);
    yPos += 8;
    
    // Section 3: Satisfaction Ratings
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('3. Satisfaction Rating (1 = Very Dissatisfied, 5 = Very Satisfied)', margin, yPos);
    yPos += 7;
    
    const ratings = [
      ['Cleanliness / Swachhata', fb.cleanliness],
      ['Room Comfort / Kamre Ki Gunvatta', fb.room_comfort],
      ['Basic Amenities / Khane Ki Gunvatta', fb.basic_amenities],
      ['Check-In Procedure / Check-In Prakriya', fb.check_in_procedure],
      ['Check-Out Procedure / Check-Out Prakriya', fb.check_out_procedure],
      ['Overall Stay / Samagra Pravas', fb.overall_stay],
      ['Staff Behaviour / Staff Vyavhar', fb.staff_behaviour]
    ];
    
    doc.autoTable({
      startY: yPos,
      head: [['Category', 'Rating']],
      body: ratings,
      theme: 'grid',
      headStyles: { fillColor: [59, 130, 246], fontSize: 10 },
      bodyStyles: { fontSize: 9 },
      columnStyles: { 0: { cellWidth: 120 }, 1: { cellWidth: 30, halign: 'center' } },
      margin: { left: margin }
    });
    
    yPos = doc.lastAutoTable.finalY + 8;
    
    // Average Score
    const avgScore = ((fb.cleanliness + fb.room_comfort + fb.basic_amenities +
      fb.check_in_procedure + fb.check_out_procedure + fb.overall_stay + fb.staff_behaviour) / 7).toFixed(2);
    
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text(`Average Score: ${avgScore} / 5`, margin, yPos);
    yPos += 8;
    
    // Section 4: Specific Feedback
    doc.setFontSize(12);
    doc.text('4. Specific Feedback / Vishishi Pratikriya', margin, yPos);
    yPos += 7;
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    
    if (fb.enjoyed_most) {
      doc.setFont('helvetica', 'bold');
      doc.text('What did you enjoy most?', margin, yPos);
      yPos += 5;
      doc.setFont('helvetica', 'normal');
      const enjoyedLines = doc.splitTextToSize(fb.enjoyed_most, pageWidth - 2 * margin);
      doc.text(enjoyedLines, margin, yPos);
      yPos += enjoyedLines.length * 5 + 3;
    }
    
    if (fb.issues_problems) {
      doc.setFont('helvetica', 'bold');
      doc.text('Were there any issues or problems?', margin, yPos);
      yPos += 5;
      doc.setFont('helvetica', 'normal');
      const issuesLines = doc.splitTextToSize(fb.issues_problems, pageWidth - 2 * margin);
      doc.text(issuesLines, margin, yPos);
      yPos += issuesLines.length * 5 + 3;
    }
    
    if (fb.improvement_suggestions) {
      doc.setFont('helvetica', 'bold');
      doc.text('How can we improve?', margin, yPos);
      yPos += 5;
      doc.setFont('helvetica', 'normal');
      const suggestionsLines = doc.splitTextToSize(fb.improvement_suggestions, pageWidth - 2 * margin);
      doc.text(suggestionsLines, margin, yPos);
      yPos += suggestionsLines.length * 5 + 3;
    }
    
    // Section 5: Additional Comments
    if (fb.additional_comments) {
      yPos += 2;
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text('5. Additional Comments / Atiriki Tippaniya', margin, yPos);
      yPos += 7;
      
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      const commentsLines = doc.splitTextToSize(fb.additional_comments, pageWidth - 2 * margin);
      doc.text(commentsLines, margin, yPos);
      yPos += commentsLines.length * 5 + 5;
    }
    
    // Section 6: Recommendation
    yPos += 2;
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('6. Would you recommend us?', margin, yPos);
    yPos += 7;
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(fb.would_recommend ? '[✓] Yes / Ha' : '[✗] No / Nahi', margin, yPos);
    
    // Footer
    yPos = doc.internal.pageSize.getHeight() - 20;
    doc.setFontSize(9);
    doc.text(`Date: ${format(new Date(), 'dd MMM yyyy')}`, margin, yPos);
    doc.text('(Signature of Guest / Atithi ka hastakshar)', pageWidth - margin - 60, yPos);
    
    // Save PDF
    const fileName = `Feedback_${fb.guest_name?.replace(/\s+/g, '_')}_${fb.check_out_date}.pdf`;
    doc.save(fileName);
    toast.success('Feedback PDF downloaded successfully');
  };

  useEffect(() => { fetchAnalysis(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="feedback-loading">
        <div className="spinner"></div>
      </div>
    );
  }

  const score = analysis?.average_score || 0;
  const colors = getSentimentColor(score);

  return (
    <div className="space-y-6" data-testid="feedback-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-800" style={{ fontFamily: 'Outfit, sans-serif' }}>
          Guest Feedback Analysis
        </h1>
        <p className="text-slate-500 mt-1">Atithi Pratikriya Vishleshan — overall satisfaction at a glance</p>
      </div>

      {/* Overall Score Card */}
      <Card className={`earms-card border-2 ${colors.border} ${colors.bg}`} data-testid="overall-score-card">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center gap-6">
            <div className="flex items-center gap-4">
              <SentimentEmoji score={score} />
              <div>
                <p className={`text-4xl font-extrabold ${colors.text}`} data-testid="average-score">
                  {score > 0 ? score.toFixed(2) : "—"}
                </p>
                <p className="text-slate-500 text-sm">Overall Average Score / 5</p>
                <Badge className={`mt-1 ${colors.badge}`}>
                  {score >= 4 ? "Excellent / Uchcha" : score >= 2.5 ? "Satisfactory / Santushṭajanak" : score > 0 ? "Needs Improvement / Sudhar Chahiye" : "No Feedbacks Yet"}
                </Badge>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 flex-1">
              <div className="text-center p-3 bg-white rounded-xl border border-slate-100">
                <div className="text-2xl font-bold text-slate-800" data-testid="total-feedbacks">{analysis?.total_count || 0}</div>
                <div className="text-xs text-slate-500">Total Feedbacks</div>
              </div>
              <div className="text-center p-3 bg-white rounded-xl border border-slate-100">
                <div className="text-2xl font-bold text-emerald-600" data-testid="recommend-rate">
                  {analysis?.recommendation_rate || 0}%
                </div>
                <div className="text-xs text-slate-500">Would Recommend</div>
              </div>
              <div className="text-center p-3 bg-white rounded-xl border border-slate-100">
                <div className={`text-2xl font-bold ${colors.text}`}>
                  {score >= 4 ? "😊" : score >= 2.5 ? "😐" : score > 0 ? "😢" : "—"}
                </div>
                <div className="text-xs text-slate-500">Satisfaction</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Category Averages */}
      {analysis?.total_count > 0 && (
        <Card className="earms-card" data-testid="category-scores-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ChartBar size={22} className="text-blue-500" weight="fill" />
              Category-wise Scores / Vibhag Anusaar Ank
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(CATEGORY_LABELS).map(([key, labels]) => {
                const avg = analysis?.category_averages?.[key] || 0;
                return (
                  <div key={key} className="grid grid-cols-12 gap-3 items-center" data-testid={`category-${key}`}>
                    <div className="col-span-4">
                      <p className="text-sm font-medium text-slate-800">{labels.en}</p>
                      <p className="text-xs text-slate-400">{labels.hi}</p>
                    </div>
                    <div className="col-span-8">
                      <ScoreBar score={avg} />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Feedbacks */}
      {analysis?.recent_feedbacks?.length > 0 && (
        <Card className="earms-card" data-testid="recent-feedbacks-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users size={22} className="text-purple-500" weight="fill" />
              Recent Feedbacks / Haaliya Pratikriyaen
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analysis.recent_feedbacks.map((fb) => {
                const avgScore = ((fb.cleanliness + fb.room_comfort + fb.basic_amenities +
                  fb.check_in_procedure + fb.check_out_procedure + fb.overall_stay + fb.staff_behaviour) / 7).toFixed(1);
                const fbColors = getSentimentColor(parseFloat(avgScore));
                return (
                  <div key={fb.id} className={`p-4 rounded-xl border ${fbColors.border} ${fbColors.bg}`} data-testid={`feedback-${fb.id}`}>
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="font-semibold text-slate-800">{fb.guest_name}</p>
                        {fb.guest_rank && <p className="text-xs text-slate-500">{fb.guest_rank}{fb.service_status ? ` (${fb.service_status})` : ""}</p>}
                        <p className="text-xs text-slate-400">{fb.check_in_date} to {fb.check_out_date}</p>
                      </div>
                      <div className="text-right flex items-start gap-2">
                        <div>
                          <p className={`text-xl font-bold ${fbColors.text}`}>{avgScore}/5</p>
                          <p className="text-xs text-slate-400">{fb.would_recommend ? "👍 Would recommend" : "No recommendation"}</p>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => printFeedback(fb)}
                          className="h-8 w-8 p-0"
                          title="Print Feedback"
                          data-testid={`print-feedback-${fb.id}`}
                        >
                          <Printer size={16} />
                        </Button>
                      </div>
                    </div>
                    <div className="grid grid-cols-4 gap-2 mb-3">
                      {Object.entries(CATEGORY_LABELS).map(([key, labels]) => (
                        <div key={key} className="text-center bg-white rounded-lg p-1 border border-white">
                          <div className="text-sm font-bold text-slate-700">{fb[key]}</div>
                          <div className="text-[10px] text-slate-400 truncate">{labels.en.split(" ")[0]}</div>
                        </div>
                      ))}
                    </div>
                    {fb.enjoyed_most && (
                      <p className="text-xs text-slate-600 mt-1"><span className="font-medium">Liked:</span> {fb.enjoyed_most}</p>
                    )}
                    {fb.issues_problems && (
                      <p className="text-xs text-slate-600 mt-1"><span className="font-medium">Issues:</span> {fb.issues_problems}</p>
                    )}
                    {fb.improvement_suggestions && (
                      <p className="text-xs text-slate-600 mt-1"><span className="font-medium">Suggestions:</span> {fb.improvement_suggestions}</p>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {analysis?.total_count === 0 && (
        <Card className="earms-card">
          <CardContent className="py-12 text-center">
            <Star size={48} className="mx-auto mb-4 text-slate-300" />
            <p className="text-slate-500 text-lg">No feedback collected yet</p>
            <p className="text-slate-400 text-sm mt-1">Feedback will appear here after guests complete their checkout</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
