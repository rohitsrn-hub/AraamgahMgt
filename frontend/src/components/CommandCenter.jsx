import React from "react";
import { useNavigate } from "react-router-dom";
import "./CommandCenter.css";

const CommandCenter = () => {
  const navigate = useNavigate();

  return (
    <div className="cc-container">

      <div className="cc-title">
        <h1>SARAI</h1>
        <p>SHILLONG ARAMGAH ROOM AUTOMATION INTERFACE</p>
      </div>

      <div className="cc-core">

        <div className="cc-hub">
          <div>
            <h2>SARAI</h2>
            <span>Command Core</span>
          </div>
        </div>

        <div className="cc-btn green top" onClick={() => navigate('/app/bookings?action=new')}>
          <span>New Booking</span>
        </div>

        <div className="cc-btn blue left" onClick={() => navigate('/app/dashboard?action=checkin')}>
          <span>Check In</span>
        </div>

        <div className="cc-btn orange right" onClick={() => navigate('/app/dashboard?action=checkout')}>
          <span>Check Out</span>
        </div>

        <div className="cc-btn red bottom-left" onClick={() => navigate('/app/dashboard?action=cancel')}>
          <span>Cancel</span>
        </div>

        <div className="cc-btn purple bottom-right" onClick={() => navigate('/app/dashboard')}>
          <span>Dashboard</span>
        </div>

      </div>
    </div>
  );
};

export default CommandCenter;
