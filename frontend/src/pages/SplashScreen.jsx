import { useNavigate } from "react-router-dom";
import { 
  Plus, 
  SignIn, 
  SignOut, 
  ChartBar, 
  X 
} from "@phosphor-icons/react";
import { useEffect, useState } from "react";

export default function SplashScreen() {
  const navigate = useNavigate();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setLoaded(true);
  }, []);

  const buttons = [
    {
      id: "new-booking",
      label: "NEW BOOKING",
      icon: <Plus size={32} weight="bold" />,
      color: "#00FF41",
      angle: -90,
      action: () => navigate("/bookings?action=new"),
    },
    {
      id: "check-out",
      label: "CHECK OUT",
      icon: <SignOut size={32} weight="bold" />,
      color: "#FF9500",
      angle: -18,
      action: () => navigate("/bookings"),
    },
    {
      id: "dashboard",
      label: "DASHBOARD",
      icon: <ChartBar size={32} weight="bold" />,
      color: "#BF5AF2",
      angle: 54,
      action: () => navigate("/"),
    },
    {
      id: "cancel",
      label: "CANCEL",
      icon: <X size={32} weight="bold" />,
      color: "#FF3B30",
      angle: 126,
      action: () => navigate("/bookings"),
    },
    {
      id: "check-in",
      label: "CHECK IN",
      icon: <SignIn size={32} weight="bold" />,
      color: "#00F0FF",
      angle: 198,
      action: () => navigate("/bookings"),
    },
  ];

  return (
    <div className="relative w-full min-h-screen overflow-hidden bg-[#04080F]" data-testid="splash-screen">
      {/* Background Image with Heavy Overlay */}
      <div 
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage: "url('https://images.unsplash.com/photo-1639313521811-fdfb1c040ddb?w=1080&q=80')",
          filter: "blur(8px)",
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-[#04080F]/95 via-[#08111E]/85 to-[#04080F]/95 backdrop-blur-xl" />

      {/* Tactical Grid Overlay */}
      <div 
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `
            repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(0, 255, 65, 0.2) 40px),
            repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(0, 255, 65, 0.2) 40px)
          `,
        }}
      />

      {/* HUD Corner Elements */}
      <div className="absolute top-4 left-4 text-[#1B93A4] text-xs font-mono opacity-60">
        <div>[SYS.READY]</div>
        <div className="mt-1">LAT: 28.6139° N</div>
        <div>LON: 77.2090° E</div>
      </div>

      <div className="absolute top-4 right-4 text-[#1B93A4] text-xs font-mono opacity-60 text-right">
        <div>[SECURE.NET]</div>
        <div className="mt-1">STATUS: ACTIVE</div>
        <div className="flex items-center gap-1 justify-end mt-1">
          <div className="w-2 h-2 bg-[#00FF41] rounded-full animate-pulse" />
          <span>ONLINE</span>
        </div>
      </div>

      <div className="absolute bottom-4 left-4 text-[#1B93A4] text-xs font-mono opacity-60">
        <div className="flex gap-1">
          {[40, 60, 35, 80, 45, 70].map((h, i) => (
            <div key={i} className="w-1 bg-[#00FF41]" style={{ height: `${h}%` }} />
          ))}
        </div>
        <div className="mt-1">SIGNAL: 98%</div>
      </div>

      <div className="absolute bottom-4 right-4 text-[#1B93A4] text-xs font-mono opacity-60 text-right">
        <div>v2.0.4-TACTICAL</div>
        <div className="mt-1">2026.04.03</div>
      </div>

      {/* Main Content Container */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen p-8">
        {/* Header */}
        <div className={`text-center mb-12 transition-all duration-1000 ${loaded ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
          <h1 
            className="text-5xl md:text-6xl font-bold tracking-widest text-white mb-3"
            style={{
              fontFamily: "'Chakra Petch', sans-serif",
              textShadow: "0 0 20px rgba(0, 255, 65, 0.8), 0 0 40px rgba(0, 255, 65, 0.4)",
            }}
          >
            E-ARMS
          </h1>
          <p 
            className="text-sm md:text-base tracking-[0.3em] text-white/70 uppercase"
            style={{ fontFamily: "'Share Tech Mono', monospace" }}
          >
            ECSAG Automated Room Management System
          </p>
        </div>

        {/* Command Center Radial Menu */}
        <div className="relative w-full max-w-lg aspect-square flex items-center justify-center">
          {/* Central Hub */}
          <div 
            className={`absolute w-32 h-32 md:w-48 md:h-48 rounded-full border-2 flex flex-col items-center justify-center transition-all duration-1000 delay-300 ${loaded ? 'opacity-100 scale-100' : 'opacity-0 scale-50'}`}
            style={{
              borderColor: "#00FF41",
              background: "radial-gradient(circle, rgba(0,255,65,0.1) 0%, transparent 70%)",
              boxShadow: "inset 0 0 30px rgba(0,255,65,0.4), 0 0 30px rgba(0,255,65,0.3)",
            }}
          >
            {/* Radar Sweep Animation */}
            <div 
              className="absolute inset-0 rounded-full"
              style={{
                background: "conic-gradient(from 0deg, transparent 70%, rgba(0, 255, 65, 0.6) 100%)",
                animation: "radar-sweep 4s linear infinite",
              }}
            />
            
            {/* Hub Content */}
            <div className="relative z-10 text-center">
              <div 
                className="text-lg md:text-2xl font-bold text-white tracking-wider"
                style={{ fontFamily: "'Chakra Petch', sans-serif" }}
              >
                E-ARMS
              </div>
              <div 
                className="text-[8px] md:text-xs text-[#00FF41] mt-1 tracking-widest"
                style={{ fontFamily: "'Share Tech Mono', monospace" }}
              >
                COMMAND
              </div>
            </div>
          </div>

          {/* Radial Buttons */}
          {buttons.map((btn, index) => {
            const radius = 180; // Distance from center
            const angleRad = (btn.angle * Math.PI) / 180;
            const x = Math.cos(angleRad) * radius;
            const y = Math.sin(angleRad) * radius;

            return (
              <button
                key={btn.id}
                onClick={btn.action}
                data-testid={`btn-${btn.id}`}
                className={`absolute w-24 h-24 md:w-32 md:h-32 flex flex-col items-center justify-center gap-2 
                  backdrop-blur-md bg-white/5 border transition-all duration-300
                  hover:scale-110 hover:bg-white/10 cursor-pointer group
                  ${loaded ? 'opacity-100 translate-x-0 translate-y-0' : 'opacity-0'}
                `}
                style={{
                  left: `calc(50% + ${x}px)`,
                  top: `calc(50% + ${y}px)`,
                  transform: "translate(-50%, -50%)",
                  clipPath: "polygon(20% 0%, 80% 0%, 100% 100%, 0% 100%)",
                  borderColor: `${btn.color}40`,
                  transitionDelay: `${(index + 1) * 150}ms`,
                  boxShadow: `0 0 20px ${btn.color}20`,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = btn.color;
                  e.currentTarget.style.boxShadow = `0 0 30px ${btn.color}, inset 0 0 20px ${btn.color}40`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = `${btn.color}40`;
                  e.currentTarget.style.boxShadow = `0 0 20px ${btn.color}20`;
                }}
              >
                <div 
                  className="transition-all duration-300"
                  style={{ color: btn.color, filter: `drop-shadow(0 0 8px ${btn.color})` }}
                >
                  {btn.icon}
                </div>
                <div 
                  className="text-[10px] md:text-xs font-bold tracking-wider"
                  style={{ 
                    color: btn.color,
                    fontFamily: "'Chakra Petch', sans-serif",
                    textShadow: `0 0 10px ${btn.color}80`,
                  }}
                >
                  {btn.label}
                </div>
              </button>
            );
          })}
        </div>

        {/* Bottom Instruction */}
        <div 
          className={`mt-16 text-center text-xs text-white/50 tracking-widest transition-all duration-1000 delay-1000 ${loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
          style={{ fontFamily: "'Share Tech Mono', monospace" }}
        >
          [ SELECT COMMAND MODULE TO PROCEED ]
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;700&family=Share+Tech+Mono&display=swap');

        @keyframes radar-sweep {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
