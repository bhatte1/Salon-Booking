import { useBookingPolicy } from "../hooks/useBookingPolicy.js";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost } from "../api.js";
import { useAuth } from "../context/auth-context.js";

export default function CustomerChatPage() {
  const { token, user } = useAuth();
  const { policy, policyError } = useBookingPolicy();
  const storageKey = `salon-chat-${user.id}`;
  const [conversationId, setConversationId] = useState(() => sessionStorage.getItem(storageKey));
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState("");
  const [confirmation, setConfirmation] = useState(null);
  const [timezone, setTimezone] = useState("");
  const [busy, setBusy] = useState(!!conversationId);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(null);
  const [expired, setExpired] = useState(false);
  const messagesRef = useRef(null);

  useEffect(() => {
    const saved = sessionStorage.getItem(storageKey);
    if (!saved) return;
    let cancelled = false;
    apiGet(`/api/chat/${saved}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(data => {
        if (cancelled) return;
        setMessages(data.history);
        setConfirmation(data.confirmation);
        setTimezone(data.timezone);
      }).catch(failure => {
        if (cancelled) return;
        setError(failure.status === 401 ? "Your login expired. Please log in again." : failure.message);
        setExpired([401,403,404,410].includes(failure.status));
      }).finally(() => { if (!cancelled) setBusy(false); });
    return () => { cancelled = true; };
  }, [storageKey, token]);

  useEffect(() => {
    const element = messagesRef.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [messages, busy]);

  function newConversation() {
    sessionStorage.removeItem(storageKey);
    setConversationId(null);
    setMessages([]);
    setConfirmation(null);
    setError("");
    setRetry(null);
    setExpired(false);
  }

  async function submit(payload) {
    if (busy) return;
    setBusy(true);
    setError("");
    setRetry(null);
    setConfirmation(null);
    try {
      const reply = await apiPost("/api/chat", payload, { headers: { Authorization: `Bearer ${token}` } });
      sessionStorage.setItem(storageKey, reply.conversation_id);
      setConversationId(reply.conversation_id);
      setMessages(reply.history);
      setConfirmation(reply.confirmation);
      setTimezone(reply.timezone);
      setMessage("");
    } catch (failure) {
      setError(failure.status === 401 ? "Your login expired. Please log in again." : failure.message);
      if ([401,403,404,410].includes(failure.status)) setExpired(true);
      else setRetry(payload);
    } finally {
      setBusy(false);
    }
  }

  function send(event) {
    event.preventDefault();
    if (!message.trim()) return;
    const confirms = confirmation && /^(yes|confirm|yes please|confirm booking)$/i.test(message.trim());
    submit({ message: message.trim(), conversation_id: conversationId, request_id: crypto.randomUUID(),
      action: confirms ? "confirm" : "message", ...(confirms ? { confirmation_id: confirmation.id } : {}) });
  }

  return (
    <div className="dashboardShell">
      <section className="dashboardPanel chatPage">
        <Link className="chatBackButton" to="/dashboard/customer">
          <span aria-hidden="true">← </span>Back to Customer Dashboard
        </Link>
        <h2>Salon booking assistant</h2>
        <p>Tell me what you’d like to book, for example “Book a haircut tomorrow at 11 AM”. I’ll check availability and ask you to confirm before booking.</p>
        <p>{timezone ? `Times are shown in ${timezone}. ` : ""}Questions are processed by AWS Bedrock. Avoid including personal information.</p>
        <p>{policy ? `Booking hours: ${policy.opening_time}–${policy.closing_time} (${policy.timezone}). Your service must finish by closing.` : policyError || "Loading booking hours…"}</p>
        <Link className="chatBookingLink" to="/dashboard/customer#my-appointments">My Appointments</Link>
        <div ref={messagesRef} className="chatMessages" role="log" aria-label="Conversation" aria-live="polite">
          {messages.length === 0 && <p>What service, date, and time would you like?</p>}
          {messages.map((item, index) => <div className="chatMessage" key={index}><strong>{item.role}</strong><p>{item.text}</p></div>)}
          {busy && <p role="status">Checking your booking…</p>}
        </div>
        {confirmation && <div className="chatConfirmation">
          <h3>Review your booking request — not booked yet</h3>
          <p>{confirmation.service} · ${(confirmation.price_cents / 100).toFixed(2)} · {confirmation.duration_minutes} minutes</p>
          <p>{confirmation.date} at {confirmation.time} ({confirmation.timezone})</p>
          <p>Your appointment is created only when you confirm. Availability is checked again then.</p>
          <button type="button" disabled={busy || expired} onClick={() => submit({ conversation_id: conversationId, request_id: crypto.randomUUID(), action: "confirm", confirmation_id: confirmation.id })}>Confirm booking</button>
        </div>}
        {error && <p role="alert">{error}</p>}
        {retry && <button type="button" disabled={busy} onClick={() => submit(retry)}>Retry same request</button>}
        {expired && <p><Link className="chatBookingLink" to="/login/customer">Log in again</Link> or start a new conversation if this discussion expired.</p>}
        <form onSubmit={send} className="form">
          <label>Your message<textarea value={message} maxLength={1000} onChange={e => setMessage(e.target.value)} required disabled={busy || expired} /></label>
          <button type="submit" disabled={busy || expired || !message.trim()}>Send</button>
        </form>
        <div className="chatControls">
          <button type="button" disabled={busy || expired || !conversationId} onClick={() => submit({ conversation_id: conversationId, request_id: crypto.randomUUID(), action: "cancel" })}>Clear unconfirmed request</button>
          <button type="button" disabled={busy} onClick={newConversation}>New conversation</button>
        </div>
      </section>
    </div>
  );
}
