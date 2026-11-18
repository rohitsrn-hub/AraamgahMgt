import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChartBar, Bed, Users, FileText, FileXls } from "@phosphor-icons/react";
import MonthlySummaryTab from "./reports/MonthlySummaryTab";
import RoomOccupancyTab from "./reports/RoomOccupancyTab";
import RoomAllotmentTab from "./reports/RoomAllotmentTab";
import GuestDetailsTab from "./reports/GuestDetailsTab";
import ManualExcelTab from "./reports/ManualExcelTab";
import axios from "axios";
import { toast } from "sonner";
import { API } from "@/App";
import { useAuth } from "@/contexts/AuthContext";

export default function ReportsPage({ settings }) {
  const [activeTab, setActiveTab] = useState("monthly");

  // Audit check: admin-only, read-only. Runs GET /reports/audit-check and
  // copies the result to the clipboard so it can be pasted (from a phone) into
  // the month-end reconciliation session — see
  // docs/month-end-reconciliation-agent.md.
  const { user } = useAuth();
  const [auditCheckBusy, setAuditCheckBusy] = useState(false);
  const [auditCheckText, setAuditCheckText] = useState("");
  const runAuditCheck = async () => {
    setAuditCheckBusy(true);
    try {
      const res = await axios.get(`${API}/reports/audit-check`);
      const text = JSON.stringify(res.data);
      setAuditCheckText(text);
      try {
        await navigator.clipboard.writeText(text);
        toast.success("Audit check finished — result copied. Paste it into the month-end check.");
      } catch {
        toast.warning("Audit check finished, but copying failed. Long-press the box below, Select All, Copy.");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Audit check failed");
    } finally {
      setAuditCheckBusy(false);
    }
  };

  // Approved data corrections (admin): a few specific stored bills / stale values agreed with the
  // owner after the October 2026 check. Preview changes nothing; Apply takes a full backup first and
  // saves every original value; Undo puts them back. See services/corrections_service.py.
  const [corrBusy, setCorrBusy] = useState(false);
  const [corrText, setCorrText] = useState("");
  const corrCall = async (fn) => {
    setCorrBusy(true);
    try { await fn(); }
    catch (error) { toast.error(error.response?.data?.detail || "That did not work. Nothing was changed unless a message above says so."); }
    finally { setCorrBusy(false); }
  };
  const showCorr = async (data, message) => {
    const text = JSON.stringify(data, null, 1);
    setCorrText(text);
    try { await navigator.clipboard.writeText(text); toast.success(`${message} Details copied.`); }
    catch { toast.success(message); }
  };
  const previewCorrections = () => corrCall(async () => {
    const res = await axios.get(`${API}/admin/corrections`);
    const ready = res.data.preview.filter((p) => p.status === "ready").length;
    await showCorr(res.data, `${ready} correction(s) ready, nothing changed.`);
  });
  const applyCorrections = () => corrCall(async () => {
    const pre = await axios.get(`${API}/admin/corrections`);
    const ready = pre.data.preview.filter((p) => p.status === "ready");
    if (ready.length === 0) { await showCorr(pre.data, "Nothing to apply."); return; }
    const list = ready.map((p) => `${p.booking_number}: ${p.description || p.label}`).join("\n");
    if (!window.confirm(`Apply ${ready.length} correction(s)?\n\n${list}\n\nThese change live bookings and the October reports. A full backup is taken first and every original value is saved, so this can be undone.`)) return;
    const res = await axios.post(`${API}/admin/corrections/apply`);
    await showCorr(res.data, `${res.data.applied} correction(s) applied. Keep the copied details.`);
  });
  const undoCorrections = () => corrCall(async () => {
    const pre = await axios.get(`${API}/admin/corrections`);
    const batch = pre.data.batches.find((b) => b.records.some((r) => !r.reverted_at));
    if (!batch) { await showCorr(pre.data, "Nothing to undo."); return; }
    if (!window.confirm(`Put back the original values from the corrections applied on ${batch.applied_at.slice(0, 10)} (${batch.records.length} record(s))?`)) return;
    const res = await axios.post(`${API}/admin/corrections/undo/${batch.batch_id}`);
    await showCorr(res.data, `${res.data.restored} record(s) restored to their original values.`);
  });

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
          <ChartBar size={36} weight="duotone" className="text-blue-500" />
          Reports
        </h1>
        <p className="text-slate-500 mt-1">Comprehensive reports and analytics</p>
      </div>

      {/* Month-end audit check (admin only) */}
      {user?.role === "admin" && (
        <div className="p-3 rounded-xl border border-slate-200 bg-slate-50 text-sm" data-testid="audit-check-box">
          <button
            onClick={runAuditCheck}
            disabled={auditCheckBusy}
            className="px-4 py-2 rounded-lg bg-slate-700 text-white font-semibold disabled:opacity-60"
          >
            {auditCheckBusy ? "Running…" : "Audit check (copies result)"}
          </button>
          <span className="ml-3 text-slate-600">For month-end reconciliation. Read-only — changes nothing.</span>
          {auditCheckText && (
            <textarea readOnly value={auditCheckText} rows={4} onFocus={(e) => e.target.select()}
              className="mt-2 w-full text-xs font-mono p-2 border border-slate-300 rounded" />
          )}

          <div className="mt-4 pt-3 border-t border-slate-200" data-testid="corrections-box">
            <p className="font-semibold text-slate-700">Approved data corrections</p>
            <p className="text-slate-600 mt-1">
              Corrections agreed after the October check and the register comparison. Preview changes nothing. Apply takes a full backup
              first and saves every original value; Undo puts them back. The October register corrections DO change October's
              reports (they make the app match the register), so run the Audit check and the Monthly Report again after Apply.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <button onClick={previewCorrections} disabled={corrBusy} className="px-3 py-2 rounded-lg bg-white border border-slate-300 font-semibold disabled:opacity-60">Preview</button>
              <button onClick={applyCorrections} disabled={corrBusy} className="px-3 py-2 rounded-lg bg-slate-700 text-white font-semibold disabled:opacity-60">Apply</button>
              <button onClick={undoCorrections} disabled={corrBusy} className="px-3 py-2 rounded-lg bg-white border border-slate-300 font-semibold disabled:opacity-60">Undo last</button>
            </div>
            {corrText && (
              <textarea readOnly value={corrText} rows={6} onFocus={(e) => e.target.select()}
                className="mt-2 w-full text-xs font-mono p-2 border border-slate-300 rounded" />
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 h-auto bg-gradient-to-r from-blue-50 to-indigo-50 p-1 rounded-xl shadow-sm">
          <TabsTrigger 
            value="monthly"
            className="data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200 py-3 px-4 rounded-lg font-semibold"
          >
            <ChartBar size={20} className="mr-2" weight="fill" />
            <span className="hidden sm:inline">Monthly Summary</span>
            <span className="sm:hidden">Monthly</span>
          </TabsTrigger>
          
          <TabsTrigger 
            value="occupancy"
            className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200 py-3 px-4 rounded-lg font-semibold"
          >
            <Bed size={20} className="mr-2" weight="fill" />
            <span className="hidden sm:inline">Room Occupancy</span>
            <span className="sm:hidden">Occupancy</span>
          </TabsTrigger>
          
          <TabsTrigger 
            value="allotment"
            className="data-[state=active]:bg-purple-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200 py-3 px-4 rounded-lg font-semibold"
          >
            <FileText size={20} className="mr-2" weight="fill" />
            <span className="hidden sm:inline">Room Allotment</span>
            <span className="sm:hidden">Allotment</span>
          </TabsTrigger>
          
          <TabsTrigger
            value="guests"
            className="data-[state=active]:bg-teal-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200 py-3 px-4 rounded-lg font-semibold"
          >
            <Users size={20} className="mr-2" weight="fill" />
            <span className="hidden sm:inline">Guest Details</span>
            <span className="sm:hidden">Guests</span>
          </TabsTrigger>

          <TabsTrigger
            value="manual-excel"
            className="data-[state=active]:bg-emerald-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-200 py-3 px-4 rounded-lg font-semibold"
          >
            <FileXls size={20} className="mr-2" weight="fill" />
            <span className="hidden sm:inline">Manual Excel</span>
            <span className="sm:hidden">Excel</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab Content - Monthly Summary */}
        <TabsContent value="monthly" className="mt-6 bg-blue-50/30 p-6 rounded-xl">
          <MonthlySummaryTab settings={settings} />
        </TabsContent>

        {/* Tab Content - Room Occupancy */}
        <TabsContent value="occupancy" className="mt-6 bg-indigo-50/30 p-6 rounded-xl">
          <RoomOccupancyTab settings={settings} />
        </TabsContent>

        {/* Tab Content - Room Allotment */}
        <TabsContent value="allotment" className="mt-6 bg-purple-50/30 p-6 rounded-xl">
          <RoomAllotmentTab settings={settings} />
        </TabsContent>

        {/* Tab Content - Guest Details */}
        <TabsContent value="guests" className="mt-6 bg-teal-50/30 p-6 rounded-xl">
          <GuestDetailsTab settings={settings} />
        </TabsContent>

        {/* Tab Content - Manual-Format Excel Export */}
        <TabsContent value="manual-excel" className="mt-6 bg-emerald-50/30 p-6 rounded-xl">
          <ManualExcelTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
