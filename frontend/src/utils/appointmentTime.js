export function formatAppointmentTime(timestamp, salonTimezone) {
  if (!timestamp || !salonTimezone) return "Appointment time unavailable";
  // Compatibility with older APIs: timezone-less timestamps represent UTC storage.
  const utcTimestamp = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(timestamp)
    ? timestamp
    : `${timestamp}Z`;
  const instant = new Date(utcTimestamp);
  if (Number.isNaN(instant.getTime())) return "Appointment time unavailable";
  try {
    const formatted = new Intl.DateTimeFormat("en-US", {
      timeZone: salonTimezone,
      year: "numeric", month: "long", day: "numeric",
      hour: "numeric", minute: "2-digit", hour12: true,
      timeZoneName: "short",
    }).format(instant);
    return `${formatted} (${salonTimezone})`;
  } catch {
    return "Appointment timezone unavailable";
  }
}

export function salonDateOffset(timezone, daysOffset = 0, now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: timezone, year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(now);
  const values = Object.fromEntries(parts.map(part => [part.type, part.value]));
  const date = new Date(Date.UTC(Number(values.year), Number(values.month) - 1, Number(values.day) + daysOffset));
  return date.toISOString().slice(0, 10);
}
