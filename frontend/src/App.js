import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/contexts/AuthContext";

// Pages
import Login from "@/pages/Login";
import SetupWizard from "@/pages/SetupWizard";
import CommandCenter from "@/components/CommandCenter";
import Dashboard from "@/pages/Dashboard";
import Bookings from "@/pages/Bookings";
import Rooms from "@/pages/Rooms";
import Staff from "@/pages/Staff";
import Toiletry from "@/pages/Toiletry";
import Settings from "@/pages/Settings";
import FeedbackPage from "@/pages/FeedbackPage";
import ReportsPage from "@/pages/ReportsPage";
import BackupRestore from "@/pages/BackupRestore";
import BackupWarningModal from "@/components/BackupWarningModal";
import Layout from "@/components/Layout";
import ProtectedRoute from "@/components/ProtectedRoute";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Configure axios interceptors for authentication
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 responses
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Main app content component (needs useNavigate hook)
function AppContent() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [backupWarning, setBackupWarning] = useState(null);
  const [showBackupModal, setShowBackupModal] = useState(false);
  const [backupBannerDismissed, setBackupBannerDismissed] = useState(false);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
    } catch (e) {
      console.error("Error fetching settings:", e);
    } finally {
      setLoading(false);
    }
  };

  const checkBackupStatus = async () => {
    try {
      const response = await axios.get(`${API}/backups/status`);
      const warning = response.data?.missed_backup_warning;
      
      if (warning?.missed) {
        setBackupWarning(warning);
        setShowBackupModal(true);
      } else {
        // Clear warnings if backup is no longer missed
        setBackupWarning(null);
        setBackupBannerDismissed(false);
      }
    } catch (e) {
      console.error("Error checking backup status:", e);
    }
  };

  const handleBackupNow = () => {
    // Navigate to backup page
    setShowBackupModal(false);
    setBackupBannerDismissed(true);
    navigate('/backup-restore');
  };

  useEffect(() => {
    fetchSettings();
    checkBackupStatus();

    // Listen for backup completion to clear warnings
    const handleBackupCompleted = () => {
      console.log("Backup completed, clearing warnings");
      setBackupWarning(null);
      setBackupBannerDismissed(false);
      setShowBackupModal(false);
    };
    
    window.addEventListener('backupCompleted', handleBackupCompleted);
    
    return () => {
      window.removeEventListener('backupCompleted', handleBackupCompleted);
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50" data-testid="loading-screen">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading E-ARMS...</p>
        </div>
      </div>
    );
  }

  // Show setup wizard if not configured
  if (!settings?.is_setup_complete) {
    return (
      <>
        <SetupWizard onComplete={fetchSettings} />
        <Toaster position="top-right" richColors />
      </>
    );
  }

  return (
    <div className="App">
      {/* Persistent Backup Warning Banner */}
      {backupWarning?.missed && !backupBannerDismissed && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-amber-500 text-white shadow-lg">
          <div className="container mx-auto px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="font-medium">
                ⚠️ Backup Required: {backupWarning.message}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button 
                onClick={handleBackupNow}
                className="px-4 py-1 bg-white text-amber-600 rounded font-medium hover:bg-amber-50 transition"
              >
                Go to Backup Page
              </button>
              <button 
                onClick={() => setBackupBannerDismissed(true)}
                className="px-3 py-1 text-white hover:bg-amber-600 rounded transition"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Backup Warning Modal */}
      <BackupWarningModal
        open={showBackupModal}
        onClose={() => setShowBackupModal(false)}
        onBackupNow={handleBackupNow}
        missedInfo={backupWarning}
      />

      {/* Main Content with top padding if banner is visible */}
      <div className={backupWarning?.missed && !backupBannerDismissed ? "pt-14" : ""}>
        <Routes>
          {/* Login Route (Public) */}
          <Route path="/login" element={<Login />} />
          
          {/* Command Center as main landing */}
          <Route path="/" element={<CommandCenter />} />
          
          {/* App routes with layout */}
          <Route path="/app" element={<Layout settings={settings} />}>
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="bookings" element={<Bookings />} />
            <Route path="rooms" element={<Rooms />} />
            <Route path="staff" element={<Staff />} />
            <Route path="toiletry" element={<Toiletry />} />
            <Route path="settings" element={<Settings settings={settings} onUpdate={fetchSettings} />} />
            <Route path="feedback" element={<FeedbackPage />} />
            <Route path="reports" element={<ReportsPage settings={settings} />} />
            <Route path="backup-restore" element={<BackupRestore />} />
          </Route>
          
          {/* Direct routes (for backward compatibility) */}
          <Route path="/dashboard" element={<Layout settings={settings} />}>
            <Route index element={<Dashboard />} />
          </Route>
          <Route path="/bookings" element={<Layout settings={settings} />}>
            <Route index element={<Bookings />} />
          </Route>
          <Route path="/feedback" element={<Layout settings={settings} />}>
            <Route index element={<FeedbackPage />} />
          </Route>
          <Route path="/reports" element={<Layout settings={settings} />}>
            <Route index element={<ReportsPage settings={settings} />} />
          </Route>
          <Route path="/rooms" element={<Layout settings={settings} />}>
            <Route index element={<Rooms />} />
          </Route>
          <Route path="/staff" element={<Layout settings={settings} />}>
            <Route index element={<Staff />} />
          </Route>
          <Route path="/toiletry" element={<Layout settings={settings} />}>
            <Route index element={<Toiletry />} />
          </Route>
          <Route path="/settings" element={<Layout settings={settings} />}>
            <Route index element={<Settings settings={settings} onUpdate={fetchSettings} />} />
          </Route>
          <Route path="/backup-restore" element={<Layout settings={settings} />}>
            <Route index element={<BackupRestore />} />
          </Route>
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
      <Toaster position="top-right" richColors />
    </div>
  );
}

// Root App component wraps AppContent with BrowserRouter
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
