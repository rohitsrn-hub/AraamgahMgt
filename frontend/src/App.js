import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";

// Pages
import SetupWizard from "@/pages/SetupWizard";
import CommandCenter from "@/components/CommandCenter";
import Dashboard from "@/pages/Dashboard";
import Bookings from "@/pages/Bookings";
import Rooms from "@/pages/Rooms";
import Staff from "@/pages/Staff";
import Toiletry from "@/pages/Toiletry";
import Settings from "@/pages/Settings";
import FeedbackPage from "@/pages/FeedbackPage";
import MonthlyReport from "@/pages/MonthlyReport";
import Layout from "@/components/Layout";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

function App() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    fetchSettings();
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
      <BrowserRouter>
        <Routes>
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
            <Route path="reports" element={<MonthlyReport settings={settings} />} />
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
            <Route index element={<MonthlyReport settings={settings} />} />
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
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
