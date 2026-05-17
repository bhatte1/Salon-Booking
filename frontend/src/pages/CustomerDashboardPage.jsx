import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import {
  getMyAppointments,
  createAppointment,
  getServices,
  getServiceAvailability,
} from "../api/auth.js";

const SERVICE_IMAGE_FALLBACK =
  "https://images.unsplash.com/photo-1556228578-567ba127e37f?auto=format&fit=crop&w=900&q=80";

function getServiceImage(serviceName) {
  const key = serviceName.toLowerCase();

  if (key.includes("haircut")) {
    return "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?auto=format&fit=crop&w=900&q=80";
  }
  if (key.includes("color")) {
    return "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80";
  }
  if (key.includes("facial")) {
    return "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=900&q=80";
  }
  if (key.includes("massage")) {
    return "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=900&q=80";
  }

  return SERVICE_IMAGE_FALLBACK;
}

export default function CustomerDashboardPage() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const bookingMonthInputRef = useRef(null);
  const bookingDateInputRef = useRef(null);

  const [appointments, setAppointments] = useState([]);
  const [loadingAppointments, setLoadingAppointments] = useState(true);
  const [appointmentsError, setAppointmentsError] = useState("");

  const [services, setServices] = useState([]);
  const [servicesError, setServicesError] = useState("");

  const [selectedServiceIds, setSelectedServiceIds] = useState([]);
  const [bookingDate, setBookingDate] = useState(() => getTomorrowDate());
  const [selectedSlot, setSelectedSlot] = useState("");
  const [availabilitySlots, setAvailabilitySlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [slotsError, setSlotsError] = useState("");
  const [notes, setNotes] = useState("");
  const [bookingMessage, setBookingMessage] = useState("");
  const [bookingError, setBookingError] = useState("");

  const activeServiceId = selectedServiceIds[selectedServiceIds.length - 1] || "";
  const activeService = services.find((service) => String(service.id) === activeServiceId);
  const selectedServices = services.filter((service) =>
    selectedServiceIds.includes(String(service.id))
  );

  function formatSlotLabel(slot) {
    const [hourText, minuteText] = slot.split(":");
    const hour = Number(hourText);
    const suffix = hour >= 12 ? "PM" : "AM";
    const hour12 = hour % 12 === 0 ? 12 : hour % 12;
    return `${hour12}:${minuteText} ${suffix}`;
  }

  function getTomorrowDate() {
    return offsetLocalDate(1);
  }

  function getTodayDate() {
    return offsetLocalDate(0);
  }

  function offsetLocalDate(daysOffset) {
    const dt = new Date();
    dt.setHours(0, 0, 0, 0);
    dt.setDate(dt.getDate() + daysOffset);
    const year = dt.getFullYear();
    const month = String(dt.getMonth() + 1).padStart(2, "0");
    const day = String(dt.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function shiftBookingDate(daysDelta) {
    if (!bookingDate) return;
    const dt = new Date(`${bookingDate}T00:00:00`);
    dt.setDate(dt.getDate() + daysDelta);

    const today = new Date(`${getTodayDate()}T00:00:00`);
    if (dt < today) return;

    const year = dt.getFullYear();
    const month = String(dt.getMonth() + 1).padStart(2, "0");
    const day = String(dt.getDate()).padStart(2, "0");
    setBookingDate(`${year}-${month}-${day}`);
  }

  function changeBookingMonth(monthValue) {
    if (!monthValue) return;
    const currentDay = bookingDate?.split("-")[2] || "01";
    const next = new Date(`${monthValue}-${currentDay}T00:00:00`);
    if (Number.isNaN(next.getTime())) {
      return;
    }

    const today = new Date(`${getTodayDate()}T00:00:00`);
    if (next < today) {
      setBookingDate(getTodayDate());
      return;
    }

    const year = next.getFullYear();
    const month = String(next.getMonth() + 1).padStart(2, "0");
    const day = String(next.getDate()).padStart(2, "0");
    setBookingDate(`${year}-${month}-${day}`);
  }

  function toggleServiceSelection(serviceId) {
    setSelectedSlot("");
    setSelectedServiceIds((currentIds) =>
      currentIds.includes(serviceId)
        ? currentIds.filter((currentId) => currentId !== serviceId)
        : [...currentIds, serviceId]
    );
  }

  function openPicker(inputRef) {
    if (!inputRef?.current) return;
    inputRef.current.focus();
    if (typeof inputRef.current.showPicker === "function") {
      inputRef.current.showPicker();
    }
  }

  async function loadAppointments() {
    try {
      const data = await getMyAppointments(token || undefined);
      setAppointments(data);
    } catch (err) {
      setAppointmentsError(err.message);
    } finally {
      setLoadingAppointments(false);
    }
  }

  async function loadServices() {
    try {
      const data = await getServices();
      setServices(data);
    } catch (err) {
      setServicesError(err.message);
    }
  }

  useEffect(() => {
    loadAppointments();
    loadServices();
  }, [token]);

  useEffect(() => {
    async function loadAvailability() {
      if (!activeServiceId || !bookingDate) {
        setAvailabilitySlots([]);
        setSelectedSlot("");
        return;
      }

      setSlotsLoading(true);
      setSlotsError("");

      try {
        const data = await getServiceAvailability(
          Number(activeServiceId),
          bookingDate,
          token || undefined
        );
        setAvailabilitySlots(data.slots || []);
        setSelectedSlot("");
      } catch (err) {
        setSlotsError(err.message);
        setAvailabilitySlots([]);
        setSelectedSlot("");
      } finally {
        setSlotsLoading(false);
      }
    }

    loadAvailability();
  }, [activeServiceId, bookingDate, token]);

  async function handleBooking(e) {
    e.preventDefault();
    setBookingError("");
    setBookingMessage("");

    if (!activeServiceId) {
      setBookingError("Please select at least one service.");
      return;
    }

    if (!bookingDate || !selectedSlot) {
      setBookingError("Please select an available date and time slot.");
      return;
    }

    try {
      const startTime = `${bookingDate}T${selectedSlot}:00`;
      await createAppointment(token || undefined, {
        service_id: Number(activeServiceId),
        start_time: startTime,
        notes: notes || null,
      });

      setBookingMessage("Appointment booked successfully!");
      setSelectedSlot("");
      setNotes("");

      setLoadingAppointments(true);
      await loadAppointments();
      const availability = await getServiceAvailability(
        Number(activeServiceId),
        bookingDate,
        token || undefined
      );
      setAvailabilitySlots(availability.slots || []);
    } catch (err) {
      setBookingError(err.message);
    }
  }

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <div className="dashboardShell">
      <div className="dashboardPage">
        <div className="customerHero">
          <div className="customerHeroContent">
            <div className="customerAvatar">{user?.full_name?.[0] || "C"}</div>
            <div>
              <h2 className="customerWelcome">Customer Dashboard</h2>
              <p className="customerMeta">Welcome, {user?.full_name}</p>
              <p className="customerMeta">Member profile: {user?.username}</p>
              <p className="customerMeta">{user?.email}</p>
            </div>
          </div>
          <button type="button" className="customerLogoutBtn" onClick={handleLogout}>
            Logout
          </button>
        </div>

        <div className="dashboardGrid">
          <section className="dashboardPanel">
            <h3 className="dashboardSectionTitle">Book Appointment</h3>
            <p className="sectionLead">
              Choose your service, then pick an available slot between 8:00 AM and 7:00 PM.
            </p>

            {services.length > 0 && (
              <div className="serviceGrid">
                {services.map((service) => (
                  <button
                    key={service.id}
                    type="button"
                    aria-label={`Select ${service.name}`}
                    className={`serviceCard ${
                      selectedServiceIds.includes(String(service.id)) ? "active" : ""
                    }`}
                    onClick={() => toggleServiceSelection(String(service.id))}
                  >
                    <img
                      src={getServiceImage(service.name)}
                      alt={service.name}
                      className="serviceImage"
                    />
                    <div className="serviceBody">
                      <p className="serviceTitle">{service.name}</p>
                      <p className="serviceSub">
                        ${(service.price_cents / 100).toFixed(2)} | {service.duration_minutes} min
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            )}

            <form onSubmit={handleBooking} className="form">
              <div className="dateQuickActions">
                <button
                  type="button"
                  className="dateNavBtn"
                  onClick={() => setBookingDate(getTodayDate())}
                >
                  Today
                </button>
                <button
                  type="button"
                  className="dateNavBtn"
                  onClick={() => setBookingDate(getTomorrowDate())}
                >
                  Tomorrow
                </button>
              </div>

              <input
                ref={bookingMonthInputRef}
                className="compactDateInput compactMonthInput"
                aria-label="Appointment month"
                type="month"
                value={bookingDate.slice(0, 7)}
                min={getTodayDate().slice(0, 7)}
                onChange={(e) => changeBookingMonth(e.target.value)}
                onClick={() => openPicker(bookingMonthInputRef)}
              />

              <div className="datePickerRow">
                <button
                  type="button"
                  className="dateNavBtn"
                  aria-label="Previous day"
                  onClick={() => shiftBookingDate(-1)}
                >
                  Previous
                </button>

                <input
                  ref={bookingDateInputRef}
                  className="compactDateInput"
                  aria-label="Appointment date"
                  type="date"
                  value={bookingDate}
                  min={getTodayDate()}
                  onChange={(e) => setBookingDate(e.target.value)}
                  onClick={() => openPicker(bookingDateInputRef)}
                  required
                />

                <button
                  type="button"
                  className="dateNavBtn"
                  aria-label="Next day"
                  onClick={() => shiftBookingDate(1)}
                >
                  Next
                </button>
              </div>

              {slotsLoading && <p>Loading available slots...</p>}
              {slotsError && <p className="error">{slotsError}</p>}

              {!slotsLoading && activeServiceId && availabilitySlots.length === 0 && (
                <p className="error">No slots available for this day. Try another date.</p>
              )}

              {!slotsLoading && availabilitySlots.length > 0 && !selectedSlot && (
                <div className="slotGrid" role="group" aria-label="Available time slots">
                  {availabilitySlots.map((slot) => (
                    <button
                      key={slot.start_time}
                      type="button"
                      className={`timeSlotBtn ${selectedSlot === slot.start_time ? "active" : ""}`}
                      onClick={() => setSelectedSlot(slot.start_time)}
                      disabled={!slot.available}
                      aria-label={`Select ${formatSlotLabel(slot.start_time)}`}
                    >
                      {formatSlotLabel(slot.start_time)}
                    </button>
                  ))}
                </div>
              )}

              {!slotsLoading && selectedSlot && (
                <div className="selectedTimePanel">
                  <p className="selectedTimeText">
                    Time selected: {formatSlotLabel(selectedSlot)}
                  </p>
                  <button
                    type="button"
                    className="selectedTimeEditBtn"
                    onClick={() => setSelectedSlot("")}
                  >
                    Edit time
                  </button>
                </div>
              )}

              <input
                placeholder="Notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />

              <button type="submit">Book</button>
            </form>

            {selectedServices.length > 0 && (
              <div className="selectedServicesPanel">
                <div className="selectedServicesHeader">
                  <p className="selectedServiceTitle">Selected Services</p>
                  <p className="selectedServiceSub">
                    Scheduling availability for: {activeService?.name}
                  </p>
                  {selectedSlot && (
                    <p className="selectedServiceSub">
                      Selected Time: {bookingDate} at {formatSlotLabel(selectedSlot)}
                    </p>
                  )}
                </div>

                <div className="selectedServicesList">
                  {selectedServices.map((service) => (
                    <div key={service.id} className="selectedServicePanel">
                      <img
                        src={getServiceImage(service.name)}
                        alt={service.name}
                        className="selectedServiceImage"
                      />
                      <div className="selectedServiceContent">
                        <p className="selectedServiceName">{service.name}</p>
                        <p className="selectedServiceSub">
                          ${(service.price_cents / 100).toFixed(2)} | {service.duration_minutes} min
                        </p>
                        {String(service.id) === activeServiceId && (
                          <p className="selectedServiceBadge">Active scheduling service</p>
                        )}
                      </div>
                      <button
                        type="button"
                        className="selectedServiceRemoveBtn"
                        onClick={() => toggleServiceSelection(String(service.id))}
                        aria-label={`Remove ${service.name}`}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {bookingMessage && <p>{bookingMessage}</p>}
            {bookingError && <p className="error">{bookingError}</p>}
            {servicesError && <p className="error">{servicesError}</p>}
          </section>

          <section className="dashboardPanel">
            <h3 className="dashboardSectionTitle">My Appointments</h3>

            {loadingAppointments && <p>Loading appointments...</p>}
            {appointmentsError && <p className="error">{appointmentsError}</p>}

            {!loadingAppointments && !appointmentsError && appointments.length === 0 && (
              <p>No appointments found.</p>
            )}

            {!loadingAppointments && !appointmentsError && appointments.length > 0 && (
              <ul className="appointmentsList">
                {appointments.map((appt) => (
                  <li key={appt.id} className="appointmentCard">
                    <strong>Appointment #{appt.id}</strong>
                    <br />
                    Service ID: {appt.service_id}
                    <br />
                    Start Time: {appt.start_time}
                    <br />
                    Notes: {appt.notes || "None"}
                    <br />
                    Status: {appt.status}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
