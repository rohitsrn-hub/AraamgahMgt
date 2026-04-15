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
import UserManagement from "@/pages/UserManagement";
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
  const { isAuthenticated, loading: authLoading } = require('@/contexts/AuthContext').useAuth();
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
      // If settings fetch fails, don't force setup wizard
      // Auth errors (401) will be handled by axios interceptor and redirect to login
      // For other errors, set empty settings but preserve setup state
      if (e.response?.status !== 401) {
        setSettings({});
      }
    } finally {
      setLoading(false);
    }
  };

  const checkBackupStatus = async () => {
    try {
      // Fetch backup history instead of status to avoid stale cache
      const historyResponse = await axios.get(`${API}/backups/history`);
      const backups = historyResponse.data || [];
      
      if (backups.length === 0) {
        // No backups exist
        setBackupWarning({
          missed: true,
          message: "No backups found. Create your first backup now!",
          hours_since: null
        });
        setShowBackupModal(true);
        return;
      }
      
      // Sort backups by timestamp (most recent first) to ensure we get the latest
      const sortedBackups = [...backups].sort((a, b) => {
        const timeA = new Date(a.backup_metadata?.timestamp || a.timestamp).getTime();
        const timeB = new Date(b.backup_metadata?.timestamp || b.timestamp).getTime();
        return timeB - timeA;
      });
      
      const lastBackup = sortedBackups[0];
      const lastBackupTime = new Date(lastBackup.backup_metadata?.timestamp || lastBackup.timestamp);
      const now = new Date();
      const hoursSince = (now - lastBackupTime) / (1000 * 60 * 60);
      
      // Show warning if last backup is older than 24 hours
      if (hoursSince > 24) {
        setBackupWarning({
          missed: true,
          message: `Last backup was ${hoursSince.toFixed(1)} hours ago`,
          hours_since: hoursSince
        });
        setShowBackupModal(true);
      } else {
        // Clear warnings if backup is recent
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
    // Only fetch settings and check backup if user is authenticated
    if (isAuthenticated()) {
      fetchSettings();
      checkBackupStatus();
    } else {
      setLoading(false);
    }

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
  }, [isAuthenticated]);

  // Show loading while auth is initializing
  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50" data-testid="loading-screen">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading SARAI...</p>
        </div>
      </div>
    );
  }

  // If not authenticated, show login page (don't check setup)
  if (!isAuthenticated()) {
    return (
      <>
        <Routes>
          <Route path="*" element={<Login />} />
        </Routes>
        <Toaster position="top-right" richColors />
      </>
    );
  }

  // User is authenticated - now check setup
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
          
          {/* Command Center and App Routes - Require Authentication */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <CommandCenter />
              </ProtectedRoute>
            }
          />
          
          {/* App routes with layout - Protected */}
          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="bookings" element={<Bookings />} />
            <Route path="rooms" element={<Rooms />} />
            <Route path="staff" element={<Staff />} />
            <Route path="toiletry" element={<Toiletry />} />
            <Route
              path="users"
              element={
                <ProtectedRoute roles="admin">
                  <UserManagement />
                </ProtectedRoute>
              }
            />
            <Route path="feedback" element={<FeedbackPage />} />
            <Route path="reports" element={<ReportsPage settings={settings} />} />
            <Route
              path="settings"
              element={
                <ProtectedRoute roles="admin">
                  <Settings settings={settings} onUpdate={fetchSettings} />
                </ProtectedRoute>
              }
            />
            <Route
              path="backup-restore"
              element={
                <ProtectedRoute roles={["admin", "staff"]}>
                  <BackupRestore />
                </ProtectedRoute>
              }
            />
          </Route>
          
          {/* Direct routes (for backward compatibility) - All Protected */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
          </Route>
          <Route
            path="/bookings"
            element={
              <ProtectedRoute>
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
            <Route index element={<Bookings />} />
          </Route>
          <Route
            path="/feedback"
            element={
              <ProtectedRoute>
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
            <Route index element={<FeedbackPage />} />
          </Route>
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
            <Route index element={<ReportsPage settings={settings} />} />
          </Route>
          <Route
            path="/rooms"
            element={
              <ProtectedRoute>
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
            <Route index element={<Rooms />} />
          </Route>
          <Route
            path="/staff"
            element={
              <ProtectedRoute>
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
            <Route index element={<Staff />} />
          </Route>
          <Route
            path="/toiletry"
            element={
              <ProtectedRoute>
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
            <Route index element={<Toiletry />} />
          </Route>
          <Route
            path="/users"
            element={
              <ProtectedRoute roles="admin">
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
            <Route index element={<UserManagement />} />
          </Route>
          <Route
            path="/settings"
            element={
              <ProtectedRoute roles="admin">
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
            <Route index element={<Settings settings={settings} onUpdate={fetchSettings} />} />
          </Route>
          <Route
            path="/backup-restore"
            element={
              <ProtectedRoute roles={["admin", "staff"]}>
                <Layout settings={settings} />
              </ProtectedRoute>
            }
          >
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
