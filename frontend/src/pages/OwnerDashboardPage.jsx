import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { getAllAppointmentsForOwner } from "../api/auth.js";

export default function OwnerDashboardPage() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();

  const [appointments, setAppointments] = useState([]);
  const [loadingAppointments, setLoadingAppointments] = useState(true);
  const [appointmentsError, setAppointmentsError] = useState("");

  useEffect(() => {
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

    loadAppointments();
  }, [token]);

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

      {loadingAppointments && <p>Loading appointments...</p>}
      {appointmentsError && <p className="error">{appointmentsError}</p>}

      {!loadingAppointments && !appointmentsError && appointments.length === 0 && (
        <p>No appointments found.</p>
      )}

      {!loadingAppointments && !appointmentsError && appointments.length > 0 && (
        <ul>
          {appointments.map((appt) => (
            <li key={appt.id}>
              <strong>Appointment #{appt.id}</strong><br />
              Customer: {appt.customer_name}<br />
              Email: {appt.customer_email}<br />
              Service ID: {appt.service_id}<br />
              Start Time: {appt.start_time}<br />
              Notes: {appt.notes || "None"}
            </li>
          ))}
        </ul>
      )}

      <br />
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
}