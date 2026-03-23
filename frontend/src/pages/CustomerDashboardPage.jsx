import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { getMyAppointments, createAppointment } from "../api/auth.js";

export default function CustomerDashboardPage() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();

  const [appointments, setAppointments] = useState([]);
  const [loadingAppointments, setLoadingAppointments] = useState(true);
  const [appointmentsError, setAppointmentsError] = useState("");

  const [serviceId, setServiceId] = useState("");
  const [startTime, setStartTime] = useState("");
  const [notes, setNotes] = useState("");
  const [bookingMessage, setBookingMessage] = useState("");
  const [bookingError, setBookingError] = useState("");

  async function loadAppointments() {
    if (!token) {
      setLoadingAppointments(false);
      return;
    }

    try {
      const data = await getMyAppointments(token);
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

  async function handleBooking(e) {
    e.preventDefault();
    setBookingError("");
    setBookingMessage("");

    try {
      await createAppointment(token, {
        service_id: Number(serviceId),
        start_time: new Date(startTime).toISOString(),
        notes: notes || null,
      });

      setBookingMessage("Appointment booked successfully!");
      setServiceId("");
      setStartTime("");
      setNotes("");

      setLoadingAppointments(true);
      await loadAppointments();
    } catch (err) {
      setBookingError(err.message);
    }
  }

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className="page">
      <h2>Customer Dashboard</h2>
      <p>Welcome, {user?.full_name}</p>
      <p>Email: {user?.email}</p>
      <p>Username: {user?.username}</p>
      <p>Role: {user?.role}</p>

      <hr />

      <h3>Book Appointment</h3>

      <form onSubmit={handleBooking} className="form">
        <input
          placeholder="Service ID"
          value={serviceId}
          onChange={(e) => setServiceId(e.target.value)}
          required
        />

        <input
          type="datetime-local"
          value={startTime}
          onChange={(e) => setStartTime(e.target.value)}
          required
        />

        <input
          placeholder="Notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />

        <button type="submit">Book</button>
      </form>

      {bookingMessage && <p>{bookingMessage}</p>}
      {bookingError && <p className="error">{bookingError}</p>}

      <hr />

      <h3>My Appointments</h3>

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