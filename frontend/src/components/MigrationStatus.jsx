import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  CheckCircle,
  WarningCircle,
  Spinner,
  DownloadSimple,
  TrashSimple,
  Database
} from "@phosphor-icons/react";

export default function MigrationStatus() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API}/migration/status`);
      setStatus(res.data);
    } catch (err) {
      console.error("Failed to fetch migration status", err);
    } finally {
      setLoading(false);
    }
  };

  const downloadArchive = async () => {
    try {
      const response = await axios.get(`${API}/migration/download-archive`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', status.archive_file || 'DEFENSE_DATA_ARCHIVE.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("Archive downloaded successfully");
    } catch (err) {
      toast.error("Failed to download archive");
      console.error(err);
    }
  };

  const deleteArchive = async () => {
    if (!window.confirm("Are you sure? This will permanently delete the archive file. Make sure you have downloaded and stored it safely offline.")) {
      return;
    }

    setDeleting(true);
    try {
      await axios.delete(`${API}/migration/delete-archive`);
      toast.success("Archive deleted successfully");
      fetchStatus(); // Refresh status
    } catch (err) {
      toast.error("Failed to delete archive");
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Spinner size={32} className="animate-spin text-blue-500" />
          <span className="ml-3 text-slate-600">Loading migration status...</span>
        </CardContent>
      </Card>
    );
  }

  if (!status || status.status === "pending") {
    return (
      <Card className="border-yellow-200 bg-yellow-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-yellow-800">
            <WarningCircle size={24} weight="fill" />
            Migration Pending
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-yellow-700">
            One-time data sanitization will run automatically on first application startup.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (status.status === "completed") {
    return (
      <Card className="border-green-200 bg-green-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-800">
            <CheckCircle size={24} weight="fill" />
            Migration Completed
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-green-700">
            <p className="font-semibold">✅ Database sanitization completed successfully</p>
            <p className="mt-2">{status.result}</p>
          </div>

          {status.archive_file && !status.archive_deleted && (
            <div className="bg-white border border-green-200 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Database size={20} className="text-green-600" />
                <span className="font-medium text-slate-800">Defense Data Archive</span>
              </div>
              
              <p className="text-sm text-slate-600">
                All sensitive defense data has been archived to: <code className="bg-slate-100 px-2 py-1 rounded">{status.archive_file}</code>
              </p>

              <div className="flex gap-2">
                <Button
                  onClick={downloadArchive}
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
                >
                  <DownloadSimple size={20} />
                  Download Archive
                </Button>

                <Button
                  onClick={deleteArchive}
                  disabled={deleting}
                  variant="destructive"
                  className="flex items-center gap-2"
                >
                  <TrashSimple size={20} />
                  {deleting ? "Deleting..." : "Delete Archive"}
                </Button>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-xs text-yellow-800">
                  ⚠️ <strong>Important:</strong> Download and store this file securely offline before deleting.
                  This is your only backup of the removed sensitive data.
                </p>
              </div>
            </div>
          )}

          {status.archive_deleted && (
            <div className="bg-slate-100 border border-slate-200 rounded p-3">
              <p className="text-sm text-slate-600">
                ✓ Archive file has been deleted from server
              </p>
            </div>
          )}

          {status.logs && status.logs.length > 0 && (
            <details className="text-xs">
              <summary className="cursor-pointer text-green-700 font-medium">View Migration Logs</summary>
              <div className="mt-2 bg-slate-900 text-green-400 p-3 rounded font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
                {status.logs.join('\n')}
              </div>
            </details>
          )}
        </CardContent>
      </Card>
    );
  }

  if (status.status === "failed") {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-800">
            <WarningCircle size={24} weight="fill" />
            Migration Failed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-700 mb-4">
            {status.result || "An error occurred during migration"}
          </p>
          
          {status.logs && status.logs.length > 0 && (
            <details className="text-xs">
              <summary className="cursor-pointer text-red-700 font-medium">View Error Logs</summary>
              <div className="mt-2 bg-slate-900 text-red-400 p-3 rounded font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
                {status.logs.join('\n')}
              </div>
            </details>
          )}
        </CardContent>
      </Card>
    );
  }

  return null;
}
