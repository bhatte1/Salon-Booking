import { buildApiUrl } from "./baseUrl.js";

export async function signupCustomer(payload) {
  const res = await fetch(buildApiUrl("/api/auth/signup/customer"), {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Signup failed");
  }

  return res.json();
}

export async function loginCustomer(payload) {
  const res = await fetch(buildApiUrl("/api/auth/login/customer"), {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Customer login failed");
  }

  return res.json();
}

export async function loginOwner(payload) {
  const res = await fetch(buildApiUrl("/api/auth/login/owner"), {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Owner login failed");
  }

  return res.json();
}

export async function getMe(token) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(buildApiUrl("/api/auth/me"), {
    method: "GET",
    credentials: "include",
    headers,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch current user");
  }

  return res.json();
}

export async function getMyAppointments(token) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(buildApiUrl("/api/appointments/me/list"), {
    method: "GET",
    credentials: "include",
    headers,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch appointments");
  }

  return res.json();
}

export async function getAllAppointmentsForOwner(token) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(buildApiUrl("/api/appointments/owner/all"), {
    method: "GET",
    credentials: "include",
    headers,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch all appointments");
  }

  return res.json();
}

export async function createAppointment(token, payload) {
  const headers = {
    "Content-Type": "application/json",
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(buildApiUrl("/api/appointments/me"), {
    method: "POST",
    credentials: "include",
    headers,
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to create appointment");
  }

  return res.json();
}

export async function getServices() {
  const res = await fetch(buildApiUrl("/api/services"), {
    method: "GET",
    credentials: "include",
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch services");
  }

  return res.json();
}

export async function getServiceAvailability(serviceId, bookingDate, token) {
  const params = new URLSearchParams({
    service_id: String(serviceId),
    booking_date: bookingDate,
  });

  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(
    buildApiUrl(`/api/appointments/availability?${params.toString()}`),
    {
      method: "GET",
      credentials: "include",
      headers,
    }
  );

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch available slots");
  }

  return res.json();
}

export async function updateAppointmentStatus(token, appointmentId, status) {
  const headers = {
    "Content-Type": "application/json",
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(buildApiUrl(`/api/appointments/owner/${appointmentId}/status`), {
    method: "PATCH",
    credentials: "include",
    headers,
    body: JSON.stringify({ status }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to update appointment status");
  }

  return res.json();
}

export async function forgotPassword(payload) {
  const res = await fetch(buildApiUrl("/api/auth/forgot-password"), {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Forgot password failed");
  }

  return res.json();
}

export async function forgotUsername(payload) {
  const res = await fetch(buildApiUrl("/api/auth/forgot-username"), {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Forgot username failed");
  }

  return res.json();
}

export async function logoutUser() {
  const res = await fetch(buildApiUrl("/api/auth/logout"), {
    method: "POST",
    credentials: "include",
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Logout failed");
  }

  return res.json();
}

export async function resetPassword(payload) {
  const res = await fetch(buildApiUrl("/api/auth/reset-password"), {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Reset password failed");
  }

  return res.json();
}
