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

const emptyCategoryForm = (categories) =>
  Object.fromEntries(categories.map((c) => [c.name, { room_rent: "", license_fee: "" }]));

export default function RateSchedule({ onUpdate }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [categories, setCategories] = useState([]);
  const [todayRates, setTodayRates] = useState({});
  const [todayNonOrgRate, setTodayNonOrgRate] = useState({});
  const [scheduled, setScheduled] = useState([]);
  const [effectiveDate, setEffectiveDate] = useState("");
  const [note, setNote] = useState("");
  const [categoryForm, setCategoryForm] = useState({});
  const [nonOrgForm, setNonOrgForm] = useState({ room_rent: "", license_fee: "" });

  const fetchSchedule = async () => {
    try {
      const res = await axios.get(`${API}/settings/rate-schedule`);
      const cats = res.data.categories || [];
      setCategories(cats);
      setTodayRates(res.data.today_effective_rates || {});
      setTodayNonOrgRate(res.data.today_effective_non_org_rate || {});
      setScheduled(res.data.scheduled_changes || []);
      setCategoryForm((prev) => (Object.keys(prev).length ? prev : emptyCategoryForm(cats)));
    } catch (error) {
      toast.error("Failed to load rate schedule");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedule();
  }, []);

  const resetForm = () => {
    setEffectiveDate("");
    setNote("");
    setCategoryForm(emptyCategoryForm(categories));
    setNonOrgForm({ room_rent: "", license_fee: "" });
  };

  const handleAdd = async () => {
    if (!effectiveDate) {
      toast.error("Pick the date this rate takes effect from");
      return;
    }
    const category_rates = {};
    for (const cat of categories) {
      const entry = categoryForm[cat.name] || {};
      const fields = {};
      if (entry.room_rent !== "" && entry.room_rent != null) fields.room_rent = parseFloat(entry.room_rent);
      if (entry.license_fee !== "" && entry.license_fee != null) fields.license_fee = parseFloat(entry.license_fee);
      if (Object.keys(fields).length > 0) category_rates[cat.name] = fields;
    }
    const nonOrgFields = {};
    if (nonOrgForm.room_rent !== "" && nonOrgForm.room_rent != null) nonOrgFields.non_org_room_rent = parseFloat(nonOrgForm.room_rent);
    if (nonOrgForm.license_fee !== "" && nonOrgForm.license_fee != null) nonOrgFields.non_org_license_fee = parseFloat(nonOrgForm.license_fee);

    if (Object.keys(category_rates).length === 0 && Object.keys(nonOrgFields).length === 0) {
      toast.error("Enter at least one new rate value");
      return;
    }
    setSaving(true);
    try {
      await axios.post(`${API}/settings/rate-schedule`, {
        effective_date: effectiveDate,
        note: note || undefined,
        category_rates,
        ...nonOrgFields,
      });
      toast.success(`Rate change scheduled from ${effectiveDate}`);
      resetForm();
      fetchSchedule();
      onUpdate?.(); // refresh the parent's settings so Room Categories etc. can't go stale
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
      onUpdate?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to remove scheduled rate change");
    }
  };

  const describeEntry = (entry) => {
    const parts = Object.entries(entry.category_rates || {}).map(
      ([name, r]) => `${name}: ₹${r.room_rent ?? "—"} + ₹${r.license_fee ?? "—"}`
    );
    if (entry.non_org_room_rent != null || entry.non_org_license_fee != null) {
      parts.push(`Non-Org: ₹${entry.non_org_room_rent ?? "—"} + ₹${entry.non_org_license_fee ?? "—"}`);
    }
    return parts.join("  ·  ");
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
          change date. Change any one category, several, or all of them, plus
          Non-Org, in a single scheduled entry.
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
                  <p className="text-xs text-amber-700 mt-1">{describeEntry(entry)}</p>
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
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                className="earms-input mt-1"
                data-testid="rate-schedule-date"
              />
            </div>
            <div>
              <Label>Note (optional)</Label>
              <Input
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="e.g. Administration rate revision"
                className="earms-input mt-1"
              />
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            {categories.map((cat) => (
              <div key={cat.id || cat.name} className="p-3 bg-white rounded-xl border border-slate-200">
                <h4 className="font-semibold mb-2 text-sm text-slate-700">Org ({cat.name})</h4>
                <div className="space-y-2">
                  <div>
                    <Label className="text-xs text-slate-500">Room Rent (₹)</Label>
                    <Input
                      type="number"
                      value={categoryForm[cat.name]?.room_rent ?? ""}
                      onChange={(e) => setCategoryForm({
                        ...categoryForm,
                        [cat.name]: { ...categoryForm[cat.name], room_rent: e.target.value },
                      })}
                      placeholder={String(todayRates?.[cat.name]?.room_rent ?? "")}
                      className="earms-input mt-1"
                      data-testid={`rate-schedule-${cat.name}-room-rent`}
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-slate-500">License Fee (₹)</Label>
                    <Input
                      type="number"
                      value={categoryForm[cat.name]?.license_fee ?? ""}
                      onChange={(e) => setCategoryForm({
                        ...categoryForm,
                        [cat.name]: { ...categoryForm[cat.name], license_fee: e.target.value },
                      })}
                      placeholder={String(todayRates?.[cat.name]?.license_fee ?? "")}
                      className="earms-input mt-1"
                      data-testid={`rate-schedule-${cat.name}-license-fee`}
                    />
                  </div>
                </div>
              </div>
            ))}

            <div className="p-3 bg-white rounded-xl border border-slate-200">
              <h4 className="font-semibold mb-2 text-sm text-slate-700">Non-Org</h4>
              <div className="space-y-2">
                <div>
                  <Label className="text-xs text-slate-500">Room Rent (₹)</Label>
                  <Input
                    type="number"
                    value={nonOrgForm.room_rent}
                    onChange={(e) => setNonOrgForm({ ...nonOrgForm, room_rent: e.target.value })}
                    placeholder={String(todayNonOrgRate?.room_rent ?? "")}
                    className="earms-input mt-1"
                    data-testid="rate-schedule-non-org-room-rent"
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-500">License Fee (₹)</Label>
                  <Input
                    type="number"
                    value={nonOrgForm.license_fee}
                    onChange={(e) => setNonOrgForm({ ...nonOrgForm, license_fee: e.target.value })}
                    placeholder={String(todayNonOrgRate?.license_fee ?? "")}
                    className="earms-input mt-1"
                    data-testid="rate-schedule-non-org-license-fee"
                  />
                </div>
              </div>
            </div>
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
