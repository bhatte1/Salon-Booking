import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import {
  getAllAppointmentsForOwner,
  updateAppointmentStatus,
} from "../api/auth.js";

export default function OwnerDashboardPage() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();

  const [appointments, setAppointments] = useState([]);
  const [loadingAppointments, setLoadingAppointments] = useState(true);
  const [appointmentsError, setAppointmentsError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [statusError, setStatusError] = useState("");

  async function loadAppointments() {
    if (!token) {
      setLoadingAppointments(false);
      return;
    }

    try {
      const data = await getAllAppointmentsForOwner(token);
      setAppointments(data);
    } catch (err) {
      setAppointmentsError(err.message);
    } finally {
      setLoadingAppointments(false);
    }
  }

  useEffect(() => {
    loadAppointments();
  }, [token]);

  async function handleStatusUpdate(appointmentId, newStatus) {
    setStatusMessage("");
    setStatusError("");

    try {
      await updateAppointmentStatus(token, appointmentId, newStatus);
      setStatusMessage(`Appointment #${appointmentId} updated to ${newStatus}`);
      await loadAppointments();
    } catch (err) {
      setStatusError(err.message);
    }
  }

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className="page">
      <h2>Owner Dashboard</h2>
      <p>Welcome, {user?.full_name}</p>
      <p>Email: {user?.email}</p>
      <p>Username: {user?.username}</p>
      <p>Role: {user?.role}</p>

      <hr />

      <h3>All Appointments</h3>

      {statusMessage && <p>{statusMessage}</p>}
      {statusError && <p className="error">{statusError}</p>}

      {loadingAppointments && <p>Loading appointments...</p>}
      {appointmentsError && <p className="error">{appointmentsError}</p>}

      {!loadingAppointments && !appointmentsError && appointments.length === 0 && (
        <p>No appointments found.</p>
      )}

      {!loadingAppointments && !appointmentsError && appointments.length > 0 && (
        <ul>
          {appointments.map((appt) => (
            <li key={appt.id} style={{ marginBottom: "16px" }}>
              <strong>Appointment #{appt.id}</strong>
              <br />
              Customer: {appt.customer_name}
              <br />
              Email: {appt.customer_email}
              <br />
              Service ID: {appt.service_id}
              <br />
              Start Time: {appt.start_time}
              <br />
              Notes: {appt.notes || "None"}
              <br />
              Status: <strong>{appt.status}</strong>
              <br />
              <div style={{ marginTop: "8px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
                <button onClick={() => handleStatusUpdate(appt.id, "confirmed")}>
                  Confirm
                </button>
                <button onClick={() => handleStatusUpdate(appt.id, "completed")}>
                  Complete
                </button>
                <button onClick={() => handleStatusUpdate(appt.id, "cancelled")}>
                  Cancel
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <br />
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
}