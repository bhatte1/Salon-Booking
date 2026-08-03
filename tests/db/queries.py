GET_USER_BY_USERNAME = """
SELECT
    id,
    full_name,
    email,
    username,
    hashed_password,
    role,
    is_active
FROM users
WHERE username = %s
"""


GET_SERVICE_BY_NAME = """
SELECT
    id,
    name,
    price_cents,
    duration_minutes
FROM services
WHERE name = %s
"""


GET_APPOINTMENT_BY_CUSTOMER_USERNAME = """
SELECT
    a.id,
    a.user_id,
    a.customer_name,
    a.customer_email,
    a.service_id,
    a.start_time,
    a.end_time,
    a.status,
    a.notes
FROM appointments a
JOIN users u ON u.id = a.user_id
WHERE u.username = %s
ORDER BY a.id DESC
LIMIT 1
"""


GET_APPOINTMENT_BY_ID = """
SELECT
    id,
    user_id,
    customer_name,
    customer_email,
    service_id,
    start_time,
    end_time,
    status,
    notes
FROM appointments
WHERE id = %s
"""


GET_APPOINTMENTS_WITH_USER_AND_SERVICE_JOIN = """
SELECT
    a.id AS appointment_id,
    a.user_id AS appointment_user_id,
    a.service_id AS appointment_service_id,
    a.status,
    a.notes,
    a.customer_name,
    a.customer_email,
    a.start_time,
    a.end_time,
    EXTRACT(EPOCH FROM (a.end_time - a.start_time)) / 60 AS appointment_duration_minutes,
    u.id AS user_id,
    u.full_name,
    u.username,
    u.email AS user_email,
    u.role,
    u.is_active,
    s.id AS service_id,
    s.name AS service_name,
    s.price_cents,
    s.duration_minutes
FROM appointments a
JOIN users u ON u.id = a.user_id
JOIN services s ON s.id = a.service_id
WHERE u.username = %s
ORDER BY a.id DESC
"""


GET_APPOINTMENT_WITH_USER_AND_SERVICE_JOIN_BY_ID = """
SELECT
    a.id AS appointment_id,
    a.user_id AS appointment_user_id,
    a.service_id AS appointment_service_id,
    a.status,
    a.notes,
    a.customer_name,
    a.customer_email,
    a.start_time,
    a.end_time,
    EXTRACT(EPOCH FROM (a.end_time - a.start_time)) / 60 AS appointment_duration_minutes,
    u.id AS user_id,
    u.full_name,
    u.username,
    u.email AS user_email,
    u.role,
    u.is_active,
    s.id AS service_id,
    s.name AS service_name,
    s.price_cents,
    s.duration_minutes
FROM appointments a
JOIN users u ON u.id = a.user_id
JOIN services s ON s.id = a.service_id
WHERE a.id = %s
"""
