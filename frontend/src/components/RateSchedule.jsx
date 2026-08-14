import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Plus, Trash, Clock } from "@phosphor-icons/react";
import { format, parseISO } from "date-fns";

const RATE_ROWS = [
  { label: "Org (Cat I)", rentKey: "cat_i_room_rent", feeKey: "cat_i_license_fee" },
  { label: "Org (Cat II)", rentKey: "cat_ii_room_rent", feeKey: "cat_ii_license_fee" },
  { label: "Non-Org", rentKey: "non_org_room_rent", feeKey: "non_org_license_fee" },
];

const emptyRates = () => ({
  cat_i_room_rent: "", cat_i_license_fee: "",
  cat_ii_room_rent: "", cat_ii_license_fee: "",
  non_org_room_rent: "", non_org_license_fee: "",
});

export default function RateSchedule() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [todayRates, setTodayRates] = useState(null);
  const [scheduled, setScheduled] = useState([]);
  const [form, setForm] = useState({ effective_date: "", note: "", ...emptyRates() });

  const fetchSchedule = async () => {
    try {
      const res = await axios.get(`${API}/settings/rate-schedule`);
      setTodayRates(res.data.today_effective_rates || {});
      setScheduled(res.data.scheduled_changes || []);
    } catch (error) {
      toast.error("Failed to load rate schedule");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedule();
  }, []);

  const handleAdd = async () => {
    if (!form.effective_date) {
      toast.error("Pick the date this rate takes effect from");
      return;
    }
    const rates = {};
    for (const key of Object.keys(emptyRates())) {
      if (form[key] !== "" && form[key] !== null && form[key] !== undefined) {
        rates[key] = parseFloat(form[key]);
      }
    }
    if (Object.keys(rates).length === 0) {
      toast.error("Enter at least one new rate value");
      return;
    }
    setSaving(true);
    try {
      await axios.post(`${API}/settings/rate-schedule`, {
        effective_date: form.effective_date,
        note: form.note || undefined,
        ...rates,
      });
      toast.success(`Rate change scheduled from ${form.effective_date}`);
      setForm({ effective_date: "", note: "", ...emptyRates() });
      fetchSchedule();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to schedule rate change");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/settings/rate-schedule/${id}`);
      toast.success("Scheduled rate change removed");
      fetchSchedule();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to remove scheduled rate change");
    }
  };

  if (loading) return null;

  return (
    <Card className="earms-card" data-testid="rate-schedule-section">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock size={24} className="text-emerald-500" weight="duotone" />
          Rate Schedule
        </CardTitle>
        <p className="text-sm text-slate-500">
          Schedule a future rate change in advance without affecting today's
          bookings. A stay bills entirely at whichever rate was in effect on
          its own check-in date — a guest already checked in keeps their
          original rate for their whole stay, even if it extends past the
          change date.
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {scheduled.length > 0 && (
          <div className="space-y-2">
            <Label className="text-xs text-slate-500">Upcoming changes</Label>
            {scheduled.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start justify-between gap-3 p-3 bg-amber-50 border border-amber-200 rounded-xl"
                data-testid={`scheduled-rate-${entry.id}`}
              >
                <div>
                  <p className="font-semibold text-amber-800">
                    Effective {format(parseISO(entry.effective_date), "dd/MM/yyyy")}
                  </p>
                  <p className="text-xs text-amber-700 mt-1">
                    {RATE_ROWS
                      .filter((r) => entry[r.rentKey] != null || entry[r.feeKey] != null)
                      .map((r) => `${r.label}: ₹${entry[r.rentKey] ?? "—"} + ₹${entry[r.feeKey] ?? "—"}`)
                      .join("  ·  ")}
                  </p>
                  {entry.note && <p className="text-xs text-slate-500 mt-1">{entry.note}</p>}
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red-500 hover:text-red-600 hover:bg-red-50 shrink-0"
                  onClick={() => handleDelete(entry.id)}
                  data-testid={`delete-scheduled-rate-${entry.id}`}
                >
                  <Trash size={16} />
                </Button>
              </div>
            ))}
          </div>
        )}

        <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label>Effective from (check-in date)</Label>
              <Input
                type="date"
                value={form.effective_date}
                onChange={(e) => setForm({ ...form, effective_date: e.target.value })}
                className="earms-input mt-1"
                data-testid="rate-schedule-date"
              />
            </div>
            <div>
              <Label>Note (optional)</Label>
              <Input
                value={form.note}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
                placeholder="e.g. Administration rate revision"
                className="earms-input mt-1"
              />
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            {RATE_ROWS.map(({ label, rentKey, feeKey }) => (
              <div key={rentKey} className="p-3 bg-white rounded-xl border border-slate-200">
                <h4 className="font-semibold mb-2 text-sm text-slate-700">{label}</h4>
                <div className="space-y-2">
                  <div>
                    <Label className="text-xs text-slate-500">Room Rent (₹)</Label>
                    <Input
                      type="number"
                      value={form[rentKey]}
                      onChange={(e) => setForm({ ...form, [rentKey]: e.target.value })}
                      placeholder={String(todayRates?.[rentKey] ?? "")}
                      className="earms-input mt-1"
                      data-testid={`rate-schedule-${rentKey}`}
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-slate-500">License Fee (₹)</Label>
                    <Input
                      type="number"
                      value={form[feeKey]}
                      onChange={(e) => setForm({ ...form, [feeKey]: e.target.value })}
                      placeholder={String(todayRates?.[feeKey] ?? "")}
                      className="earms-input mt-1"
                      data-testid={`rate-schedule-${feeKey}`}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500">
            Leave a field blank to keep it unchanged from the current rate shown as its placeholder.
          </p>

          <Button
            onClick={handleAdd}
            disabled={saving}
            className="earms-btn-primary flex items-center gap-2"
            data-testid="schedule-rate-btn"
          >
            <Plus size={18} />
            {saving ? "Scheduling..." : "Schedule Rate Change"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
