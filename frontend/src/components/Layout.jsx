import { Outlet, NavLink, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { 
  House, 
  CalendarCheck, 
  Bed, 
  Users, 
  Package, 
  Gear,
  List,
  Star,
  ChartBar,
  Database
} from "@phosphor-icons/react";
import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";

const navItems = [
  { path: "/app/dashboard", icon: House, label: "Dashboard" },
  { path: "/app/bookings", icon: CalendarCheck, label: "Bookings" },
  { path: "/app/rooms", icon: Bed, label: "Rooms" },
  { path: "/app/staff", icon: Users, label: "Staff" },
  { path: "/app/toiletry", icon: Package, label: "Toiletry" },
  { path: "/app/feedback", icon: Star, label: "Feedback", dynamic: true },
  { path: "/app/reports", icon: ChartBar, label: "Reports" },
  { path: "/app/backup-restore", icon: Database, label: "Backup & Restore" },
  { path: "/app/settings", icon: Gear, label: "Settings" },
];

const DEFAULT_FMN_1 = "https://images.unsplash.com/photo-1765555648802-53235276a40b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwyfHxzaGllbGQlMjBlbWJsZW18ZW58MHx8fHwxNzc1MDcwOTU4fDA&ixlib=rb-4.1.0&q=85&w=100";
const DEFAULT_FMN_2 = "https://images.unsplash.com/photo-1771456915291-58f0dee5b404?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwxfHxzaGllbGQlMjBlbWJsZW18ZW58MHx8fHwxNzc1MDcwOTU4fDA&ixlib=rb-4.1.0&q=85&w=100";

export default function Layout({ settings }) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [feedbackScore, setFeedbackScore] = useState(null);

  const fmnSign1 = settings?.fmn_sign_1_url || DEFAULT_FMN_1;
  const fmnSign2 = settings?.fmn_sign_2_url || DEFAULT_FMN_2;

  useEffect(() => {
    axios.get(`${API}/feedback/analysis`).then((res) => {
      setFeedbackScore(res.data?.average_score || 0);
    }).catch(() => {});
  }, []);

  const getFeedbackStyle = (score) => {
    if (!score || score === 0) return { color: "text-slate-600", bg: "" };
    if (score >= 4) return { color: "text-emerald-700", bg: "bg-emerald-50" };
    if (score >= 2.5) return { color: "text-orange-700", bg: "bg-orange-50" };
    return { color: "text-red-700", bg: "bg-red-50" };
  };

  const getFeedbackEmoji = (score) => {
    if (!score || score === 0) return "";
    if (score >= 4) return " 😊";
    if (score >= 2.5) return " 😐";
    return " 😢";
  };

  const NavContent = () => (
    <nav className="flex flex-col gap-2 p-4">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.path;
        const fbStyle = item.dynamic ? getFeedbackStyle(feedbackScore) : {};
        return (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={() => setMobileMenuOpen(false)}
            data-testid={`nav-${item.label.toLowerCase()}`}
            className={`nav-item ${isActive ? "active" : ""} ${item.dynamic && !isActive ? fbStyle.bg : ""}`}
          >
            <Icon size={22} weight={isActive ? "fill" : "regular"} />
            <span className={item.dynamic && !isActive ? fbStyle.color : ""}>
              {item.label}{item.dynamic ? getFeedbackEmoji(feedbackScore) : ""}
            </span>
          </NavLink>
        );
      })}
    </nav>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="earms-header" data-testid="main-header">
        <div className="h-full px-4 md:px-8 flex items-center justify-between">
          {/* Left - Mobile menu + Formation Sign 1 */}
          <div className="flex items-center gap-4">
            {/* Mobile menu button */}
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild className="lg:hidden">
                <Button variant="ghost" size="icon" data-testid="mobile-menu-btn">
                  <List size={24} />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-72 p-0">
                <div className="p-4 border-b">
                  <h2 className="font-bold text-lg text-slate-800">E-ARMS Menu</h2>
                </div>
                <NavContent />
              </SheetContent>
            </Sheet>
            
            <img 
              src={fmnSign1} 
              alt="Formation Sign 1" 
              className="h-12 w-12 md:h-14 md:w-14 object-contain rounded-lg"
              data-testid="fmn-sign-1"
            />
          </div>

          {/* Center - Title */}
          <div className="text-center flex-1 px-4">
            <h1 className="text-xl md:text-3xl lg:text-4xl font-extrabold text-slate-800 tracking-tight" style={{ fontFamily: 'Outfit, sans-serif' }}>
              E-ARMS
            </h1>
            <p className="text-xs md:text-sm text-slate-500 hidden sm:block font-medium">
              ECSAG Automated Room Management System
            </p>
          </div>

          {/* Right - Formation Sign 2 */}
          <div className="flex items-center">
            <img 
              src={fmnSign2} 
              alt="Formation Sign 2" 
              className="h-12 w-12 md:h-14 md:w-14 object-contain rounded-lg"
              data-testid="fmn-sign-2"
            />
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:block w-64 min-h-[calc(100vh-80px)] bg-white border-r border-slate-200" data-testid="desktop-sidebar">
          <NavContent />
        </aside>

        {/* Main Content */}
        <main className="flex-1 earms-main" data-testid="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
