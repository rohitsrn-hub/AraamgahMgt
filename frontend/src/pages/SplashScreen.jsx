import { useNavigate } from "react-router-dom";
import { 
  CalendarCheck, 
  SignIn, 
  ArrowsLeftRight, 
  SquaresFour, 
  XCircle 
} from "@phosphor-icons/react";
import { useEffect, useState } from "react";

export default function SplashScreen() {
  const navigate = useNavigate();
  const [loaded, setLoaded] = useState(false);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    setLoaded(true);
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date) => {
    return date.toTimeString().slice(0, 8);
  };

  const panels = [
    {
      id: "new-booking",
      label: "New Booking",
      icon: <CalendarCheck size={48} weight="fill" />,
      color: "#00FF41",
      position: "top",
      action: () => navigate("/bookings?action=new"),
    },
    {
      id: "check-in",
      label: "Check In",
      icon: <SignIn size={48} weight="fill" />,
      color: "#0EA5E9",
      position: "left",
      action: () => navigate("/bookings"),
    },
    {
      id: "check-out",
      label: "Check Out",
      icon: <ArrowsLeftRight size={48} weight="fill" />,
      color: "#F97316",
      position: "right",
      action: () => navigate("/bookings"),
    },
    {
      id: "cancel",
      label: "Cancel Booking",
      icon: <XCircle size={48} weight="fill" />,
      color: "#EF4444",
      position: "bottom-left",
      action: () => navigate("/bookings"),
    },
    {
      id: "dashboard",
      label: "Dashboard",
      icon: <SquaresFour size={48} weight="fill" />,
      color: "#A855F7",
      position: "bottom-right",
      action: () => navigate("/"),
    },
  ];

  return (
    <div className="relative w-full min-h-screen overflow-hidden bg-[#0a1628]" data-testid="splash-screen">
      {/* Complex HUD Background */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-40"
        style={{
          backgroundImage: "url('https://images.unsplash.com/photo-1639313521811-fdfb1c040ddb?w=1080&q=80')",
        }}
      />
      
      {/* Animated HUD Overlay */}
      <div className="absolute inset-0">
        {/* Grid Lines */}
        <div 
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `
              repeating-linear-gradient(0deg, transparent, transparent 49px, rgba(0, 255, 65, 0.3) 50px),
              repeating-linear-gradient(90deg, transparent, transparent 49px, rgba(0, 255, 65, 0.3) 50px)
            `,
          }}
        />
        
        {/* Data Elements - Left Side */}
        <div className="absolute left-4 top-1/4 space-y-2 text-xs font-mono text-[#00FF41] opacity-60">
          <div className="flex gap-2">
            {[30, 45, 60, 35, 50, 40].map((h, i) => (
              <div key={i} className="w-1 bg-[#00FF41]" style={{ height: `${h}px` }} />
            ))}
          </div>
          <div>[DATA STREAM]</div>
          <div className="text-[10px]">7064 6075 4910 7459</div>
        </div>

        {/* Signal Indicator - Bottom Left */}
        <div className="absolute left-4 bottom-20 text-xs font-mono">
          <div className="text-[#00FF41] mb-1">[100% SIGNAL]</div>
          <div className="text-[#00FF41] opacity-80">ONLINE</div>
        </div>

        {/* Coordinates - Top Right */}
        <div className="absolute right-4 top-20 text-right text-xs font-mono text-[#00FF41] opacity-70">
          <div className="text-[10px] mb-1">{formatTime(time)}</div>
          <div className="text-[10px]">32.1610IN 81.2425W</div>
        </div>

        {/* Data Grid - Bottom Right */}
        <div className="absolute right-4 bottom-20 text-xs font-mono text-[#00FF41] opacity-50">
          <div className="grid grid-cols-4 gap-1">
            {Array(16).fill(0).map((_, i) => (
              <div key={i} className="w-2 h-2 border border-[#00FF41]" />
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4">
        {/* Header */}
        <div className={`text-center mb-8 transition-all duration-1000 ${loaded ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
          <h1 
            className="text-4xl md:text-5xl font-bold tracking-wider text-white mb-2"
            style={{
              fontFamily: "'Rajdhani', sans-serif",
              textShadow: "0 0 20px rgba(255, 255, 255, 0.5)",
            }}
          >
            E-ARMS
          </h1>
          <p 
            className="text-xs md:text-sm tracking-widest text-[#00FF41] uppercase opacity-80"
            style={{ fontFamily: "'Rajdhani', sans-serif" }}
          >
            ECSAG Automated Room Management System
          </p>
        </div>

        {/* Hexagonal Control Panel */}
        <div className={`relative transition-all duration-1000 delay-300 ${loaded ? 'opacity-100 scale-100' : 'opacity-0 scale-50'}`}>
          {/* Outer Metallic Frame */}
          <div 
            className="relative w-[90vw] max-w-[500px] aspect-square"
            style={{
              filter: "drop-shadow(0 0 40px rgba(0, 255, 65, 0.3))",
            }}
          >
            {/* Main Hexagonal Structure */}
            <svg 
              viewBox="0 0 500 500" 
              className="w-full h-full"
              style={{
                filter: "drop-shadow(0 10px 30px rgba(0, 0, 0, 0.8))",
              }}
            >
              <defs>
                {/* Gradients for metallic effect */}
                <linearGradient id="metalGold" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#FFD700" />
                  <stop offset="50%" stopColor="#B8860B" />
                  <stop offset="100%" stopColor="#FFD700" />
                </linearGradient>
                
                <linearGradient id="darkMetal" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#2a3f5f" />
                  <stop offset="50%" stopColor="#1a2332" />
                  <stop offset="100%" stopColor="#2a3f5f" />
                </linearGradient>

                {/* Panel gradients */}
                <radialGradient id="greenGlow" cx="50%" cy="50%">
                  <stop offset="0%" stopColor="#00FF41" stopOpacity="1" />
                  <stop offset="100%" stopColor="#00AA2C" stopOpacity="1" />
                </radialGradient>
                <radialGradient id="blueGlow" cx="50%" cy="50%">
                  <stop offset="0%" stopColor="#0EA5E9" stopOpacity="1" />
                  <stop offset="100%" stopColor="#0369A1" stopOpacity="1" />
                </radialGradient>
                <radialGradient id="orangeGlow" cx="50%" cy="50%">
                  <stop offset="0%" stopColor="#F97316" stopOpacity="1" />
                  <stop offset="100%" stopColor="#C2410C" stopOpacity="1" />
                </radialGradient>
                <radialGradient id="redGlow" cx="50%" cy="50%">
                  <stop offset="0%" stopColor="#EF4444" stopOpacity="1" />
                  <stop offset="100%" stopColor="#B91C1C" stopOpacity="1" />
                </radialGradient>
                <radialGradient id="purpleGlow" cx="50%" cy="50%">
                  <stop offset="0%" stopColor="#A855F7" stopOpacity="1" />
                  <stop offset="100%" stopColor="#7E22CE" stopOpacity="1" />
                </radialGradient>
              </defs>

              {/* Outer Gold Frame (Hexagon) */}
              <polygon 
                points="250,20 450,135 450,365 250,480 50,365 50,135"
                fill="url(#metalGold)"
                stroke="#FFD700"
                strokeWidth="3"
              />
              
              {/* Inner Dark Border */}
              <polygon 
                points="250,35 435,142 435,358 250,465 65,358 65,142"
                fill="url(#darkMetal)"
                stroke="#1a2332"
                strokeWidth="2"
              />

              {/* Decorative Screws/Bolts */}
              {[
                [250, 20], [450, 135], [450, 365], [250, 480], [50, 365], [50, 135]
              ].map((pos, i) => (
                <g key={i}>
                  <circle cx={pos[0]} cy={pos[1]} r="8" fill="#FFD700" />
                  <circle cx={pos[0]} cy={pos[1]} r="4" fill="#1a2332" />
                </g>
              ))}

              {/* Top Panel - New Booking (Green) */}
              <polygon 
                points="250,80 350,130 310,185 190,185 150,130"
                fill="url(#greenGlow)"
                stroke="#00FF41"
                strokeWidth="2"
                className="cursor-pointer transition-all hover:opacity-80"
                onClick={() => panels[0].action()}
                style={{ filter: "drop-shadow(0 0 15px #00FF41)" }}
              />

              {/* Left Panel - Check In (Blue) */}
              <polygon 
                points="100,180 190,185 190,250 190,315 100,320"
                fill="url(#blueGlow)"
                stroke="#0EA5E9"
                strokeWidth="2"
                className="cursor-pointer transition-all hover:opacity-80"
                onClick={() => panels[1].action()}
                style={{ filter: "drop-shadow(0 0 15px #0EA5E9)" }}
              />

              {/* Right Panel - Check Out (Orange) */}
              <polygon 
                points="400,180 310,185 310,250 310,315 400,320"
                fill="url(#orangeGlow)"
                stroke="#F97316"
                strokeWidth="2"
                className="cursor-pointer transition-all hover:opacity-80"
                onClick={() => panels[2].action()}
                style={{ filter: "drop-shadow(0 0 15px #F97316)" }}
              />

              {/* Bottom Left Panel - Cancel (Red) */}
              <polygon 
                points="150,370 190,315 250,340 210,400"
                fill="url(#redGlow)"
                stroke="#EF4444"
                strokeWidth="2"
                className="cursor-pointer transition-all hover:opacity-80"
                onClick={() => panels[3].action()}
                style={{ filter: "drop-shadow(0 0 15px #EF4444)" }}
              />

              {/* Bottom Right Panel - Dashboard (Purple) */}
              <polygon 
                points="350,370 310,315 250,340 290,400"
                fill="url(#purpleGlow)"
                stroke="#A855F7"
                strokeWidth="2"
                className="cursor-pointer transition-all hover:opacity-80"
                onClick={() => panels[4].action()}
                style={{ filter: "drop-shadow(0 0 15px #A855F7)" }}
              />

              {/* Center Circle */}
              <circle 
                cx="250" 
                cy="250" 
                r="80" 
                fill="rgba(10, 22, 40, 0.95)"
                stroke="#00FF41"
                strokeWidth="3"
                style={{ filter: "drop-shadow(0 0 20px #00FF41)" }}
              />
              <circle 
                cx="250" 
                cy="250" 
                r="75" 
                fill="none"
                stroke="#00FF41"
                strokeWidth="1"
                opacity="0.3"
              />
            </svg>

            {/* Icons and Labels - Positioned Absolutely */}
            <div className="absolute inset-0">
              {/* Top - New Booking */}
              <div 
                className="absolute left-1/2 top-[12%] -translate-x-1/2 flex flex-col items-center cursor-pointer"
                onClick={() => panels[0].action()}
              >
                <div className="text-white mb-1">{panels[0].icon}</div>
                <div className="text-white text-sm md:text-base font-semibold" style={{ fontFamily: "'Rajdhani', sans-serif" }}>
                  {panels[0].label}
                </div>
              </div>

              {/* Left - Check In */}
              <div 
                className="absolute left-[10%] top-1/2 -translate-y-1/2 flex flex-col items-center cursor-pointer"
                onClick={() => panels[1].action()}
              >
                <div className="text-white mb-1">{panels[1].icon}</div>
                <div className="text-white text-sm md:text-base font-semibold" style={{ fontFamily: "'Rajdhani', sans-serif" }}>
                  {panels[1].label}
                </div>
              </div>

              {/* Right - Check Out */}
              <div 
                className="absolute right-[10%] top-1/2 -translate-y-1/2 flex flex-col items-center cursor-pointer"
                onClick={() => panels[2].action()}
              >
                <div className="text-white mb-1">{panels[2].icon}</div>
                <div className="text-white text-sm md:text-base font-semibold" style={{ fontFamily: "'Rajdhani', sans-serif" }}>
                  {panels[2].label}
                </div>
              </div>

              {/* Bottom Left - Cancel */}
              <div 
                className="absolute left-[20%] bottom-[15%] flex flex-col items-center cursor-pointer"
                onClick={() => panels[3].action()}
              >
                <div className="text-white mb-1">{panels[3].icon}</div>
                <div className="text-white text-sm md:text-base font-semibold" style={{ fontFamily: "'Rajdhani', sans-serif" }}>
                  {panels[3].label}
                </div>
              </div>

              {/* Bottom Right - Dashboard */}
              <div 
                className="absolute right-[20%] bottom-[15%] flex flex-col items-center cursor-pointer"
                onClick={() => panels[4].action()}
              >
                <div className="text-white mb-1">{panels[4].icon}</div>
                <div className="text-white text-sm md:text-base font-semibold" style={{ fontFamily: "'Rajdhani', sans-serif" }}>
                  {panels[4].label}
                </div>
              </div>

              {/* Center Hub Content */}
              <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
                <div 
                  className="text-xl md:text-2xl font-bold text-white mb-1"
                  style={{ 
                    fontFamily: "'Rajdhani', sans-serif",
                    textShadow: "0 0 10px rgba(0, 255, 65, 0.8)",
                  }}
                >
                  E-ARMS
                </div>
                <div 
                  className="text-[8px] md:text-[10px] text-[#00FF41] leading-tight px-4"
                  style={{ fontFamily: "'Rajdhani', sans-serif" }}
                >
                  AUTOMATED ROOM<br/>MANAGEMENT SYSTEM
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&display=swap');
      `}</style>
    </div>
  );
}
