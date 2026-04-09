import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { WarningCircle } from "@phosphor-icons/react";

export default function BackupWarningModal({ open, onClose, onBackupNow, missedInfo }) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 text-amber-900">
            <WarningCircle size={32} weight="fill" className="text-amber-500" />
            Backup Warning
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-900 font-medium">
              {missedInfo?.message || "Scheduled backup was not completed"}
            </p>
            {missedInfo?.hours_since_last && (
              <p className="text-sm text-amber-800 mt-2">
                Last successful backup was <strong>{missedInfo.hours_since_last} hours ago</strong>
              </p>
            )}
          </div>
          
          <div className="space-y-2 text-sm text-slate-700">
            <p><strong>Why backup is important:</strong></p>
            <ul className="list-disc list-inside space-y-1 text-slate-600">
              <li>Protects against data loss</li>
              <li>Enables recovery from errors</li>
              <li>Maintains 90-day data retention</li>
              <li>Ensures business continuity</li>
            </ul>
          </div>
        </div>
        
        <DialogFooter className="sm:justify-between">
          <Button 
            variant="outline" 
            onClick={onClose}
            className="text-slate-600"
          >
            Remind Me Later
          </Button>
          <Button 
            onClick={() => {
              onBackupNow();
              onClose();
            }}
            className="bg-amber-600 hover:bg-amber-700"
          >
            Backup Now
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
