import { apiGet, apiPatch, apiPost } from "../api.js";

function withAuthHeaders(token, headers = {}) {
  if (!token) {
    return headers;
  }

  return {
    ...headers,
    Authorization: `Bearer ${token}`,
  };
}

export async function signupCustomer(payload) {
  return apiPost("/api/auth/signup/customer", payload);
}

export async function loginCustomer(payload) {
  return apiPost("/api/auth/login/customer", payload);
}

export async function loginOwner(payload) {
  return apiPost("/api/auth/login/owner", payload);
}

export async function getMe(token) {
  return apiGet("/api/auth/me", {
    headers: withAuthHeaders(token),
  });
}

export async function getMyAppointments(token) {
  return apiGet("/api/appointments/me/list", {
    headers: withAuthHeaders(token),
  });
}

export async function getAllAppointmentsForOwner(token) {
  return apiGet("/api/appointments/owner/all", {
    headers: withAuthHeaders(token),
  });
}

export async function createAppointment(token, payload) {
  return apiPost("/api/appointments/me", payload, {
    headers: withAuthHeaders(token),
  });
}

export async function getServices() {
  return apiGet("/api/services");
}

export async function getServiceAvailability(serviceId, bookingDate, token) {
  const params = new URLSearchParams({
    service_id: String(serviceId),
    booking_date: bookingDate,
  });

  return apiGet(`/api/appointments/availability?${params.toString()}`, {
    headers: withAuthHeaders(token),
  });
}

export async function updateAppointmentStatus(token, appointmentId, status) {
  return apiPatch(`/api/appointments/owner/${appointmentId}/status`, { status }, {
    headers: withAuthHeaders(token),
  });
}

export async function forgotPassword(payload) {
  return apiPost("/api/auth/forgot-password", payload);
}

export async function forgotUsername(payload) {
  return apiPost("/api/auth/forgot-username", payload);
}

export async function logoutUser() {
  return apiPost("/api/auth/logout", {});
}

export async function resetPassword(payload) {
  return apiPost("/api/auth/reset-password", payload);
}
