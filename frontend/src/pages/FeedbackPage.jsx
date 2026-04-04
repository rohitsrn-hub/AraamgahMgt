import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";
import { toast } from "sonner";
import { ChartBar, Star, ThumbsUp, Users } from "@phosphor-icons/react";

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
                      <div className="text-right">
                        <p className={`text-xl font-bold ${fbColors.text}`}>{avgScore}/5</p>
                        <p className="text-xs text-slate-400">{fb.would_recommend ? "👍 Would recommend" : "No recommendation"}</p>
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
