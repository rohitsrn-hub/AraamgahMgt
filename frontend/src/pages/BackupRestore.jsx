import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  Database,
  ArrowCounterClockwise,
  CloudArrowUp,
  CloudArrowDown,
  Clock,
  CheckCircle,
  WarningCircle,
  SpinnerGap,
  CalendarBlank,
  Info
} from "@phosphor-icons/react";
import { parseISO, format } from "date-fns";
import { formatInTimeZone } from "date-fns-tz";

// Helper function to format UTC date to IST
const formatIST = (utcDateString, formatStr = "dd MMM yyyy, HH:mm") => {
  if (!utcDateString) return "N/A";
  
  try {
    // Parse the UTC date string
    const utcDate = parseISO(utcDateString);
    
    // Format in IST timezone (Asia/Kolkata)
    const istFormatted = formatInTimeZone(utcDate, 'Asia/Kolkata', formatStr);
    
    return `${istFormatted} IST`;
  } catch (error) {
    console.error("Error formatting IST:", error);
    return "Invalid date";
  }
};

export default function BackupRestore() {
  const [status, setStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [restoreType, setRestoreType] = useState(null);
  const [selectedBackupId, setSelectedBackupId] = useState(null);
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [scheduleTime, setScheduleTime] = useState({ hour: 2, minute: 0 });
  const [showNoDataWarning, setShowNoDataWarning] = useState(false);
  const [pendingBackupType, setPendingBackupType] = useState(null);

  useEffect(() => {
    fetchBackupStatus();
    fetchBackupHistory();
  }, []);

  const fetchBackupStatus = async () => {
    try {
      const res = await axios.get(`${API}/backups/status`);
      setStatus(res.data);
      
      // Set schedule time from last backup or default
      if (res.data.scheduler?.jobs?.length > 0) {
        const job = res.data.scheduler.jobs.find(j => j.id === 'daily_backup');
        if (job?.next_run) {
          // Parse and convert to IST to extract hour/minute
          const nextRunUTC = parseISO(job.next_run);
          const nextRunIST = formatInTimeZone(nextRunUTC, 'Asia/Kolkata', 'HH:mm');
          const [hour, minute] = nextRunIST.split(':').map(Number);
          setScheduleTime({ hour, minute });
        }
      }

      // Notify parent (App.js) to refresh backup status and clear warnings
      if (res.data?.missed_backup_warning?.missed === false) {
        window.dispatchEvent(new CustomEvent('backupCompleted'));
      }
    } catch (error) {
      console.error("Error fetching backup status:", error);
      toast.error("Failed to fetch backup status");
    } finally {
      setLoading(false);
    }
  };

  const fetchBackupHistory = async () => {
    try {
      const res = await axios.get(`${API}/backups/history?limit=20`);
      setHistory(res.data.backups || []);
    } catch (error) {
      console.error("Error fetching backup history:", error);
    }
  };

  const triggerFullBackup = async () => {
    setActionLoading(true);
    try {
      const res = await axios.post(`${API}/backups/manual/full`);
      toast.success("Full backup completed successfully!");
      await fetchBackupStatus();
      await fetchBackupHistory();
      
      // Clear warnings immediately after successful backup
      window.dispatchEvent(new CustomEvent('backupCompleted'));
    } catch (error) {
      toast.error(error.response?.data?.detail || "Backup failed");
    } finally {
      setActionLoading(false);
    }
  };

  const triggerIncrementalBackup = async () => {
    setActionLoading(true);
    try {
      const res = await axios.post(`${API}/backups/manual/incremental`);
      const backup = res.data?.backup;
      
      // Check if no new data was backed up
      const totalRecords = backup?.record_count ? Object.values(backup.record_count).reduce((a, b) => a + b, 0) : 0;
      
      if (totalRecords === 0) {
        // No new data - show warning
        setPendingBackupType('incremental');
        setShowNoDataWarning(true);
        setActionLoading(false);
        return;
      }
      
      toast.success("Incremental backup completed successfully!");
      await fetchBackupStatus();
      await fetchBackupHistory();
      
      // Clear warnings immediately after successful backup
      window.dispatchEvent(new CustomEvent('backupCompleted'));
    } catch (error) {
      toast.error(error.response?.data?.detail || "Backup failed");
    } finally {
      setActionLoading(false);
    }
  };

  const handleNoDataWarningConfirm = async () => {
    setShowNoDataWarning(false);
    // Trigger full backup instead
    await triggerFullBackup();
  };

  const handleRestore = async () => {
    setActionLoading(true);
    try {
      let res;
      if (restoreType === 'last') {
        res = await axios.post(`${API}/backups/restore/last`);
      } else if (restoreType === 'full' && selectedBackupId) {
        res = await axios.post(`${API}/backups/restore/full/${selectedBackupId}`);
      } else if (restoreType === 'range') {
        res = await axios.post(`${API}/backups/restore/range`, {
          start_date: dateRange.start,
          end_date: dateRange.end
        });
      }
      
      toast.success("Restore completed successfully!");
      setShowRestoreDialog(false);
      fetchBackupStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Restore failed");
    } finally {
      setActionLoading(false);
    }
  };

  const updateSchedule = async () => {
    try {
      await axios.put(`${API}/backups/schedule`, scheduleTime);
      toast.success(`Backup schedule updated to ${scheduleTime.hour.toString().padStart(2, '0')}:${scheduleTime.minute.toString().padStart(2, '0')} IST`);
      fetchBackupStatus();
    } catch (error) {
      toast.error("Failed to update schedule");
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 MB';
    const mb = bytes;
    return `${mb.toFixed(2)} MB`;
  };

  const getStatusBadge = (backupStatus) => {
    if (backupStatus === "SUCCESS") {
      return <Badge className="bg-green-100 text-green-800">Success</Badge>;
    }
    return <Badge className="bg-red-100 text-red-800">Failed</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <SpinnerGap size={40} className="animate-spin text-blue-500" />
      </div>
    );
  }

  const lastBackup = status?.last_backup;
  const missedWarning = status?.missed_backup_warning;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
          <Database size={36} weight="duotone" className="text-blue-500" />
          Backup & Restore
        </h1>
        <p className="text-slate-500 mt-1">Manage data backups and restore operations</p>
      </div>

      {/* Warning Banner for Missed Backups */}
      {missedWarning?.missed && (
        <Card className="border-amber-300 bg-amber-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <WarningCircle size={24} className="text-amber-600 flex-shrink-0" weight="fill" />
              <div>
                <h3 className="font-semibold text-amber-900">Backup Warning</h3>
                <p className="text-sm text-amber-800 mt-1">{missedWarning.message}</p>
                <Button 
                  size="sm" 
                  className="mt-3 bg-amber-600 hover:bg-amber-700"
                  onClick={triggerIncrementalBackup}
                  disabled={actionLoading}
                >
                  Backup Now
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Backup Status Dashboard */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* Last Backup */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock size={20} className="text-blue-500" />
              Last Backup
            </CardTitle>
          </CardHeader>
          <CardContent>
            {lastBackup ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Type:</span>
                  <Badge className={lastBackup.backup_type === "FULL" ? "bg-blue-100 text-blue-800" : "bg-purple-100 text-purple-800"}>
                    {lastBackup.backup_type}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Time:</span>
                  <span className="text-sm font-medium">
                    {formatIST(lastBackup.timestamp, "dd MMM yyyy, HH:mm")}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Records:</span>
                  <span className="text-sm font-medium">
                    {Object.values(lastBackup.record_count || {}).reduce((a, b) => a + b, 0)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Size:</span>
                  <span className="text-sm font-medium">{formatBytes(lastBackup.file_size_mb || 0)}</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">No backup found</p>
            )}
          </CardContent>
        </Card>

        {/* Total Backups */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Database size={20} className="text-green-500" />
              Total Backups
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-slate-800">{status?.total_backups || 0}</div>
              <div className="text-sm text-slate-600">
                {status?.first_backup_date && (
                  <>Since {formatIST(status.first_backup_date, "dd MMM yyyy")}</>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Scheduler Status */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <CalendarBlank size={20} className="text-purple-500" />
              Next Scheduled
            </CardTitle>
          </CardHeader>
          <CardContent>
            {status?.scheduler?.jobs?.find(j => j.id === 'daily_backup') ? (
              <div className="space-y-2">
                <div className="text-sm font-medium">
                  {formatIST(status.scheduler.jobs.find(j => j.id === 'daily_backup').next_run, "dd MMM yyyy, HH:mm")}
                </div>
                <Badge className="bg-green-100 text-green-800">Active</Badge>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Not scheduled</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Manual Backup Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CloudArrowUp size={24} className="text-blue-500" />
            Manual Backup
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <Button 
              onClick={triggerFullBackup}
              disabled={actionLoading}
              className="h-20 flex flex-col items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700"
            >
              {actionLoading ? (
                <SpinnerGap size={24} className="animate-spin" />
              ) : (
                <>
                  <Database size={24} />
                  <span>Full Backup</span>
                  <span className="text-xs opacity-80">Backup entire dataset</span>
                </>
              )}
            </Button>
            
            <Button 
              onClick={triggerIncrementalBackup}
              disabled={actionLoading}
              className="h-20 flex flex-col items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700"
            >
              {actionLoading ? (
                <SpinnerGap size={24} className="animate-spin" />
              ) : (
                <>
                  <CloudArrowUp size={24} />
                  <span>Incremental Backup</span>
                  <span className="text-xs opacity-80">Backup new data only</span>
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Restore Options */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CloudArrowDown size={24} className="text-green-500" />
            Restore Data
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-3 gap-4">
            <Button 
              variant="outline"
              onClick={() => {
                setRestoreType('last');
                setShowRestoreDialog(true);
              }}
              className="h-16 border-green-300 text-green-700 hover:bg-green-50"
            >
              <div className="flex flex-col items-center gap-1">
                <ArrowCounterClockwise size={20} />
                <span className="text-sm">Last Backup</span>
              </div>
            </Button>
            
            <Button 
              variant="outline"
              onClick={() => {
                setRestoreType('full');
                setShowRestoreDialog(true);
              }}
              className="h-16 border-blue-300 text-blue-700 hover:bg-blue-50"
            >
              <div className="flex flex-col items-center gap-1">
                <Database size={20} />
                <span className="text-sm">Select Backup</span>
              </div>
            </Button>
            
            <Button 
              variant="outline"
              onClick={() => {
                setRestoreType('range');
                setShowRestoreDialog(true);
              }}
              className="h-16 border-purple-300 text-purple-700 hover:bg-purple-50"
            >
              <div className="flex flex-col items-center gap-1">
                <CalendarBlank size={20} />
                <span className="text-sm">Date Range</span>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Schedule Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock size={24} className="text-orange-500" />
            Backup Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-4">
            <div>
              <Label>Hour (IST)</Label>
              <Input 
                type="number" 
                min="0" 
                max="23" 
                value={scheduleTime.hour}
                onChange={(e) => setScheduleTime({...scheduleTime, hour: parseInt(e.target.value) || 0})}
                className="w-20 mt-1"
              />
            </div>
            <div>
              <Label>Minute</Label>
              <Input 
                type="number" 
                min="0" 
                max="59" 
                value={scheduleTime.minute}
                onChange={(e) => setScheduleTime({...scheduleTime, minute: parseInt(e.target.value) || 0})}
                className="w-20 mt-1"
              />
            </div>
            <Button onClick={updateSchedule}>
              Update Schedule
            </Button>
          </div>
          <p className="text-sm text-slate-500 mt-3">
            Current schedule: Daily at {scheduleTime.hour.toString().padStart(2, '0')}:{scheduleTime.minute.toString().padStart(2, '0')} IST
          </p>
        </CardContent>
      </Card>

      {/* Backup History */}
      <Card>
        <CardHeader>
          <CardTitle>Backup History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Timestamp</th>
                  <th className="text-left p-2">Type</th>
                  <th className="text-left p-2">Records</th>
                  <th className="text-left p-2">Size</th>
                  <th className="text-left p-2">Duration</th>
                  <th className="text-left p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {history.map((backup) => (
                  <tr key={backup.backup_id} className="border-b hover:bg-slate-50">
                    <td className="p-2 text-sm">
                      {formatIST(backup.timestamp, "dd MMM yyyy, HH:mm")}
                    </td>
                    <td className="p-2">
                      <Badge className={backup.backup_type === "FULL" ? "bg-blue-100 text-blue-800" : "bg-purple-100 text-purple-800"}>
                        {backup.backup_type}
                      </Badge>
                    </td>
                    <td className="p-2 text-sm">
                      {Object.values(backup.record_count || {}).reduce((a, b) => a + b, 0)}
                    </td>
                    <td className="p-2 text-sm">{formatBytes(backup.file_size_mb || 0)}</td>
                    <td className="p-2 text-sm">{backup.duration_seconds || 0}s</td>
                    <td className="p-2">{getStatusBadge(backup.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Restore Dialog */}
      <Dialog open={showRestoreDialog} onOpenChange={setShowRestoreDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Restore</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            {restoreType === 'last' && (
              <p>Restore the most recent successful backup?</p>
            )}
            {restoreType === 'full' && (
              <div className="space-y-3">
                <Label>Select Backup</Label>
                <select 
                  className="w-full p-2 border rounded"
                  onChange={(e) => setSelectedBackupId(e.target.value)}
                >
                  <option value="">Select a backup</option>
                  {history.filter(b => b.status === "SUCCESS").map(backup => (
                    <option key={backup.backup_id} value={backup.backup_id}>
                      {formatIST(backup.timestamp, "dd MMM yyyy, HH:mm")} - {backup.backup_type}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {restoreType === 'range' && (
              <div className="space-y-3">
                <div>
                  <Label>Start Date</Label>
                  <Input 
                    type="datetime-local" 
                    value={dateRange.start}
                    onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label>End Date</Label>
                  <Input 
                    type="datetime-local" 
                    value={dateRange.end}
                    onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                    className="mt-1"
                  />
                </div>
              </div>
            )}
            <div className="mt-4 p-3 bg-amber-50 rounded border border-amber-200">
              <p className="text-sm text-amber-800">
                <strong>Strategy: MERGE</strong> - Existing newer records will be kept, missing data will be added.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRestoreDialog(false)}>Cancel</Button>
            <Button 
              onClick={handleRestore}
              disabled={actionLoading || (restoreType === 'full' && !selectedBackupId)}
              className="bg-green-600 hover:bg-green-700"
            >
              {actionLoading ? <SpinnerGap size={16} className="animate-spin" /> : "Restore"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* No New Data Warning Dialog */}
      <Dialog open={showNoDataWarning} onOpenChange={setShowNoDataWarning}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-900">
              <Info size={24} weight="fill" className="text-amber-500" />
              No New Data to Backup
            </DialogTitle>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm text-amber-900">
                <strong>No changes detected since last backup.</strong>
              </p>
              <p className="text-sm text-amber-800 mt-2">
                An incremental backup found <strong>0 new or modified records</strong> since your last backup.
              </p>
            </div>
            
            <div className="space-y-2 text-sm">
              <p className="font-medium text-slate-700">What would you like to do?</p>
              <ul className="list-disc list-inside space-y-1 text-slate-600 ml-2">
                <li><strong>Cancel:</strong> No backup needed right now</li>
                <li><strong>Full Backup:</strong> Create a complete backup anyway (recommended if you want a new baseline)</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowNoDataWarning(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleNoDataWarningConfirm}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Do Full Backup Instead
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
