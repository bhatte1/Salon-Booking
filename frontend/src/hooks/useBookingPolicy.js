import { useEffect, useState } from "react";
import { apiGet } from "../api.js";

export function useBookingPolicy() {
  const [policy, setPolicy] = useState(null);
  const [policyError, setPolicyError] = useState("");
  useEffect(() => {
    let cancelled = false;
    apiGet("/api/appointments/booking-policy")
      .then(data => { if (!cancelled) setPolicy(data); })
      .catch(() => { if (!cancelled) setPolicyError("Booking hours are unavailable. Please try again."); });
    return () => { cancelled = true; };
  }, []);
  return { policy, policyError };
}
