import React from "react";
import { useNavigate } from "react-router-dom";
import "./CommandCenter.css";

const CommandCenter = () => {
  const navigate = useNavigate();

  return (
    <div className="cc-container">

      <div className="cc-title">
        <h1>E-ARMS</h1>
        <p>ECSAG AUTOMATED ROOM MANAGEMENT SYSTEM</p>
      </div>

      <div className="cc-core">

        <div className="cc-hub">
          <div>
            <h2>E-ARMS</h2>
            <span>Command Core</span>
          </div>
        </div>

        <div className="cc-btn green top" onClick={() => navigate('/bookings?action=new')}>
          New Booking
        </div>

        <div className="cc-btn blue left" onClick={() => navigate('/bookings')}>
          Check In
        </div>

        <div className="cc-btn orange right" onClick={() => navigate('/bookings')}>
          Check Out
        </div>

        <div className="cc-btn red bottom-left" onClick={() => navigate('/bookings')}>
          Cancel
        </div>

        <div className="cc-btn purple bottom-right" onClick={() => navigate('/dashboard')}>
          Dashboard
        </div>

      </div>
    </div>
  );
};

export default CommandCenter;
