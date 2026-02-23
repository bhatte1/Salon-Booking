import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { apiGet, apiPost } from "./api";

export default function App() {
  const [services, setServices] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const [form, setForm] = useState({
    customer_name: "",
    customer_email: "",
    service_id: "",
    start_time: "",
    notes: "",
  });

  async function refreshAll() {
    setErr("");
    setLoading(true);
    try {
      const [svc, appts] = await Promise.all([
        apiGet("/api/services"),
        apiGet("/api/appointments"),
      ]);
      setServices(svc);
      setAppointments(appts);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshAll();
  }, []);

  const serviceMap = useMemo(() => {
    const m = new Map();
    for (const s of services) m.set(s.id, s);
    return m;
  }, [services]);

async function seedServicesIfEmpty() {
  if (services.length > 0) return;

  const defaults = [
    { name: "Haircut", price_cents: 3000, duration_minutes: 30 },
    { name: "Beard Trim", price_cents: 1500, duration_minutes: 15 },
    { name: "Hair Color", price_cents: 9000, duration_minutes: 90 },
  ];

  try {
    for (const s of defaults) {
      try {
        await apiPost("/api/services", s);
      } catch (e) {
        // If service already exists (409), ignore it.
        if (String(e.message || e).includes("409")) continue;
        throw e;
      }
    }
    await refreshAll();
  } catch (e) {
    setErr(e.message || String(e));
  }
}

  useEffect(() => {
    seedServicesIfEmpty();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [services.length]);

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");

    // Basic client-side validation
    if (!form.service_id) return setErr("Please select a service.");
    if (!form.start_time) return setErr("Please pick a date/time.");

    const payload = {
      customer_name: form.customer_name.trim(),
      customer_email: form.customer_email.trim(),
      service_id: Number(form.service_id),
      // datetime-local returns "YYYY-MM-DDTHH:mm", we convert to ISO string
      start_time: new Date(form.start_time).toISOString(),
      notes: form.notes.trim() ? form.notes.trim() : null,
    };

    try {
      await apiPost("/api/appointments", payload);
      setForm({
        customer_name: "",
        customer_email: "",
        service_id: "",
        start_time: "",
        notes: "",
      });
      await refreshAll();
    } catch (e) {
      setErr(e.message || String(e));
    }
  }

  return (
    <div className="container">
      <header className="header">
        <h1>Salon Booking</h1>
      </header>

      {err ? <div className="error">{err}</div> : null}

      <div className="grid">
        <section className="card">
          <h2>Book an appointment</h2>

          {loading ? (
            <p>Loading…</p>
          ) : (
            <form onSubmit={onSubmit} className="form">
              <label>
                Name
                <input
                  value={form.customer_name}
                  onChange={(e) =>
                    setForm({ ...form, customer_name: e.target.value })
                  }
                  required
                />
              </label>

              <label>
                Email
                <input
                  type="email"
                  value={form.customer_email}
                  onChange={(e) =>
                    setForm({ ...form, customer_email: e.target.value })
                  }
                  required
                />
              </label>

              <label>
                Service
                <select
                  value={form.service_id}
                  onChange={(e) =>
                    setForm({ ...form, service_id: e.target.value })
                  }
                  required
                >
                  <option value="">Select…</option>
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} — ${(s.price_cents / 100).toFixed(2)} ({s.duration_minutes}m)
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Start time
                <input
                  type="datetime-local"
                  value={form.start_time}
                  onChange={(e) =>
                    setForm({ ...form, start_time: e.target.value })
                  }
                  required
                />
              </label>

              <label>
                Notes (optional)
                <input
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                />
              </label>

              <button type="submit">Book</button>
            </form>
          )}
        </section>

        <section className="card">
          <h2>Appointments</h2>
          {loading ? (
            <p>Loading…</p>
          ) : appointments.length === 0 ? (
            <p>No appointments yet.</p>
          ) : (
            <ul className="list">
              {appointments.map((a) => {
                const s = serviceMap.get(a.service_id);
                return (
                  <li key={a.id} className="listItem">
                    <div className="line1">
                      <b>{a.customer_name}</b> — {s ? s.name : `Service #${a.service_id}`}
                    </div>
                    <div className="line2">
                      {new Date(a.start_time).toLocaleString()} · {a.customer_email}
                      {a.notes ? ` · Notes: ${a.notes}` : ""}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}

          <div className="actions">
            <button type="button" onClick={refreshAll}>
              Refresh
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
