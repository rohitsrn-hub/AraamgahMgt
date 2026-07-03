import { useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { FileXls } from "@phosphor-icons/react";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

export default function ManualExcelTab() {
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [downloading, setDownloading] = useState(false);

  const years = [];
  for (let y = 2024; y <= new Date().getFullYear() + 1; y++) years.push(y);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const res = await axios.get(`${API}/reports/manual-occupancy-excel`, {
        params: { month, year },
        responseType: "blob",
      });
      const blobUrl = URL.createObjectURL(new Blob([res.data]));
      const filename = `Room_Occupancy_${MONTHS[month - 1]}_${year}.xlsx`;
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
      toast.success(`Downloaded ${filename}`);
    } catch (err) {
      toast.error("Failed to generate Excel report");
      console.error(err);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-800">Manual-Format Excel Export</h2>
        <p className="text-sm text-slate-500 mt-1">
          Generates an Excel sheet in the same layout as the paper "Summary of Room Occupancy" ledger, one row per room per booking for the selected month.
        </p>
      </div>

      <Card className="bg-amber-50/50 border-amber-200">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Month</Label>
              <Select value={String(month)} onValueChange={(v) => setMonth(Number(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MONTHS.map((m, i) => <SelectItem key={i} value={String(i + 1)}>{m}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Year</Label>
              <Select value={String(year)} onValueChange={(v) => setYear(Number(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {years.map(y => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button
                onClick={handleDownload}
                disabled={downloading}
                className="w-full bg-emerald-600 hover:bg-emerald-700"
              >
                <FileXls size={20} className="mr-2" />
                {downloading ? "Generating..." : "Download Excel"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">What's in this sheet</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-600 space-y-2">
          <p>Columns match the manual ledger exactly: Ser No, Army No, Rank, Name, Unit, Total Days, Bill No, Advance Amt, Room Rent, Licence Chg, Extra Bed, Total Amt.</p>
          <p>
            <span className="font-semibold text-amber-700">Army No, Rank, Unit, and Bill No are left blank</span> (highlighted) for manual completion — the app does not digitize these fields.
            Two extra columns, <span className="font-semibold">Aadhaar Number</span> and <span className="font-semibold">Org / Non-Org</span>, are included so each row can still be matched to a person by name.
          </p>
          <p>All financial figures (Room Rent, Licence Fee, Extra Bed, Total Amt) use the same calculation as the Room Allotment, Guest Details, Room Occupancy and Monthly reports, so this export will always reconcile with them.</p>
        </CardContent>
      </Card>
    </div>
  );
}
