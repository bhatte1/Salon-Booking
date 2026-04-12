const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function signupCustomer(payload) {
  const res = await fetch(`${API_BASE}/api/auth/signup/customer`, {
    method: "POST",
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
  const res = await fetch(`${API_BASE}/api/auth/login/customer`, {
    method: "POST",
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
  const res = await fetch(`${API_BASE}/api/auth/login/owner`, {
    method: "POST",
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
  const res = await fetch(`${API_BASE}/api/auth/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch current user");
  }

  return res.json();
}

export async function getMyAppointments(token) {
  const res = await fetch(`${API_BASE}/api/appointments/me/list`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch appointments");
  }

  return res.json();
}

export async function getAllAppointmentsForOwner(token) {
  const res = await fetch(`${API_BASE}/api/appointments/owner/all`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch all appointments");
  }

  return res.json();
}

export async function createAppointment(token, payload) {
  const res = await fetch(`${API_BASE}/api/appointments/me`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to create appointment");
  }

  return res.json();
}

export async function getServices() {
  const res = await fetch(`${API_BASE}/api/services`, {
    method: "GET",
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch services");
  }

  return res.json();
}

export async function updateAppointmentStatus(token, appointmentId, status) {
  const res = await fetch(`${API_BASE}/api/appointments/owner/${appointmentId}/status`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ status }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to update appointment status");
  }

  return res.json();
}

export async function forgotPassword(payload) {
  const res = await fetch(`${API_BASE}/api/auth/forgot-password`, {
    method: "POST",
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

export async function resetPassword(payload) {
  const res = await fetch(`${API_BASE}/api/auth/reset-password`, {
    method: "POST",
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