# Salon booking chatbot

The customer assistant supports conversational booking through the existing React/FastAPI application. Bedrock extracts bounded booking details; deterministic backend code controls authentication, data retrieval, availability, confirmation and appointment creation. No Bedrock Agent infrastructure or model-generated SQL is used.

## Supported behavior

After customer login, open **Ask the salon assistant** or `/chat` and type:

> Book a haircut tomorrow at 11 AM

The assistant resolves the service from the catalog and today/tomorrow in `SALON_TIMEZONE`. Missing or ambiguous details prompt clarification; follow-ups such as “11 AM” update the current draft. Availability and prices come from PostgreSQL. Unavailable times produce up to six real alternatives on the requested date.

A confirmation shows the service, catalog price, duration, full date, time and timezone. No appointment exists until the customer clicks **Confirm booking**, or types an accepted confirmation phrase while that summary is displayed. Changed details invalidate the old confirmation. Successful booking returns an appointment ID and a **My Appointments** link.

Cancellation distinguishes an unconfirmed chat draft from an existing appointment:

- **Clear unconfirmed request** clears only the draft and creates no appointment.
- A cancellation request after booking identifies the appointment using committed confirmation receipts and explains that appointment cancellation is unsupported. It does not change appointment status.
- If both a draft and an existing appointment could be intended, the assistant asks which one the customer means.

An appointment with business status `pending` already exists and awaits salon confirmation. It is not an unconfirmed chat request.

## API contract

All chat endpoints require an authenticated, active customer account. The frontend supplies an `Authorization: Bearer <token>` header. Existing backend authentication also accepts its auth cookie. Owners cannot access customer chat. Conversation lookup is restricted to its authenticated owner.

### POST /api/chat

Request fields:

| Field | Type | Requirement |
|---|---|---|
| `request_id` | UUID | Required client-generated operation ID. Reuse for an exact retry. |
| `conversation_id` | UUID or null | Omit/null for a new message conversation; required for confirming/cancelling an existing discussion. |
| `action` | `message`, `confirm`, `cancel` | Defaults to `message`. |
| `message` | string | Up to 1,000 characters; nonblank for message actions. Defaults to empty for button actions. |
| `confirmation_id` | UUID or null | Required to confirm the currently displayed offer. |

Unknown request fields are rejected. Customer identity, price and duration are not accepted from the client.

Initial message:

```json
{
  "request_id": "11111111-1111-4111-8111-111111111111",
  "conversation_id": null,
  "action": "message",
  "message": "Book a haircut tomorrow at 11 AM"
}
```

Confirmation (IDs are those returned by the backend):

```json
{
  "request_id": "22222222-2222-4222-8222-222222222222",
  "conversation_id": "33333333-3333-4333-8333-333333333333",
  "action": "confirm",
  "confirmation_id": "44444444-4444-4444-8444-444444444444"
}
```

The response includes:

- `answer`: deterministic customer-facing response.
- `request_id`: server-generated observability ID, also in `X-Request-ID` on successful POST responses. This differs from the client's retry ID.
- `conversation_id`: persisted discussion ID.
- `history`: up to 40 `{role, text}` messages.
- `confirmation`: null or an offer with `id`, `service_id`, `service`, `price_cents`, `duration_minutes`, `date`, `time`, `timezone`, and offset-aware `start_utc`.
- `appointment_id`: created appointment ID, otherwise null.
- `timezone`: configured IANA salon timezone.
- `booking_path`: `/dashboard/customer#my-appointments`.

Free-text confirmation submitted as a normal message does not create an appointment. React turns an accepted confirmation phrase into `action=confirm` with the displayed offer ID.

### GET /api/chat/{conversation_id}

Restores the owner's `conversation_id`, `history`, pending `confirmation`, and `timezone`. Expired conversations cannot be restored. The UI stores only the conversation ID in sessionStorage under a customer-specific key; history and draft state live in PostgreSQL.

### Related booking endpoints

- `GET /api/appointments/booking-policy`: public opening/closing times and timezone.
- `GET /api/appointments/availability?service_id=1&booking_date=2027-01-07`: authenticated lookup for a **salon-local calendar date**. Each slot has local `start_time`, explicit UTC `start_utc` ending in `Z`, and `available`. The response also includes the timezone and opening/closing times.
- `POST /api/appointments/me`: existing authenticated manual booking path. Manual React booking submits the availability slot's `start_utc` directly.

Appointment responses serialize UTC `start_time` with a `Z` suffix and include `salon_timezone`. Dashboards format times in that zone and treat older timezone-less timestamps as UTC, never browser-local time.

### Errors

| Status | Meaning |
|---|---|
| 400 | Invalid action sequence or booking input. |
| 401 | Missing/invalid/expired authentication. |
| 403 | Account is inactive or not a customer. |
| 404 | Conversation is absent or belongs to another customer. |
| 409 | Confirmation is stale or its details changed. |
| 410 | Conversation expired or receipt limit reached. |
| 422 | Invalid request schema or blank message. |
| 429 | Process-local limit of 20 requests/customer/minute exceeded. |
| 503 | Model, configuration or database temporarily unavailable. |

A slot becoming unavailable during confirmation normally produces a successful chat response with alternatives and no appointment ID. Model/SQL failure details are not exposed. Bedrock failures preserve the previously committed draft; database errors roll back. Retry uncertain failures with the same request ID.

## Shared hours and timestamps

`app/services/booking_hours.py` defines 08:00–19:00 in the configured salon timezone, currently **America/New_York**. The entire service must finish by closing: a 30-minute service may start at 18:30; a 90-minute service at 17:30.

Timezone-aware local day bounds are converted to UTC for queries and validation. Chat rejects ambiguous/nonexistent local DST times. Appointments remain stored as UTC-naive instants. No historical timestamps are shifted. For example, 11 AM New York is 15:00 UTC in summer and 16:00 UTC in winter.

Both manual booking and chat creation use the same hour validator and appointment creation helper. Manual Today/Tomorrow uses the salon's date rather than the browser's date.

## State, transaction and retry guarantees

Migration `b17c0a000001` creates `chat_conversations` with user ownership, expiry, JSON draft, history and receipts. A conversation lasts 30 minutes, retains 40 messages and limits recorded receipts to 60 entries. Confirmation receipts also count toward that limit.

The backend locks each conversation row while processing changes. Creation acquires a service-wide PostgreSQL advisory transaction lock, then rechecks hours and overlap. Confirmation also locks and rereads the service's name, price and duration; changed details require review again.

The appointment and completed-confirmation receipt commit atomically. The same operation ID, repeated confirmations with new operation IDs, and parallel confirmation requests return the original appointment ID. Different overlapping start times are protected by the same service lock. A retry of the first message without a returned conversation ID can create another draft conversation, but cannot create an appointment without a valid explicit confirmation.

## Configuration and local startup

Backend requirements include Boto3. Configure backend-only variables in the ignored `backend/.env` or process environment:

```env
DATABASE_URL=postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@127.0.0.1:5434/YOUR_DATABASE
SECRET_KEY=replace_with_a_long_random_secret
SALON_TIMEZONE=America/New_York
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

The database URL and secret above are placeholders, not credentials. The model/profile must support Converse and be accessible in the chosen region/account. Boto3 uses AWS's credential provider chain; use your existing local profile/SSO or workload role. Do not put credentials into source code or frontend `VITE_*` variables. Optional `AWS_PROFILE` selects a local SDK profile.

Local PostgreSQL is currently configured on port 5434. Ensure it is running and the database URL matches its actual credentials. Local Docker configuration changes are separate from this chatbot commit; the committed Compose configuration may map a different port. Check the active port mapping rather than assuming it matches the example.

From the project root:

```bash
cd backend
python3 -m venv .venv  # only if the environment does not already exist
.venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, from the project root:

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

Set `VITE_API_BASE_URL=http://127.0.0.1:8000` in ignored `frontend/.env`. Log in as a customer and open `/chat`. No new AWS infrastructure or Agent is required. Existing HTTPS/CORS/model permissions must be verified separately before any future deployment.

## Implementation map

- `app/api/chat_routes.py`: authenticated HTTP routes and rate limiting.
- `app/schemas/chat.py`: bounded API contract.
- `app/models/chat_conversation.py`: durable user-owned state.
- `app/services/booking_chat.py`: Bedrock extraction and deterministic state machine.
- `app/services/customer_chat.py`: allowlisted catalog and availability access.
- `app/services/booking_hours.py`: salon timezone and shared business-hour policy.
- `app/api/appointment_routes.py`: shared creation, locking and availability.
- `frontend/src/pages/CustomerChatPage.jsx`: history, confirmation, cancellation explanation and stable retry requests.
- `frontend/src/hooks/useBookingPolicy.js`: shared UI policy loading.
- `frontend/src/utils/appointmentTime.js`: explicit UTC parsing, salon display and date offsets.

## Development verification

```bash
cd backend
.venv/bin/python -m pytest tests/test_customer_chat.py -q
CHAT_TEST_POSTGRES=1 .venv/bin/python -m pytest tests/test_customer_chat.py -q
# From frontend/:
npm run lint
npm run build
```

PostgreSQL checks create/remove isolated schemas using the configured database; the test principal needs schema-creation permission. They do not alter existing customers or appointments. SQLite skips the two PostgreSQL concurrency checks.

The current PostgreSQL suite has 41 checks covering details, ambiguity, access rules, availability, confirmation, duplicate prevention, concurrency, cancellation, serialization, DST, local-hour boundaries, duration limits and manual/chat agreement. Live synthetic Bedrock extraction and a synthetic end-to-end development booking were also verified; temporary records were removed. Browser checks verified salon-time display and UTC submission with a Tokyo browser timezone. Existing dependency deprecation warnings remain.

A local read-only audit found 14 of 30 existing appointments outside the new hours. The generated `reports/booking_hours_audit.md` remains local and is not included in the source commit. Existing appointments were not changed.

## Known limitations

- One service per appointment; no payments, staff-specific capacity or verified holiday policies.
- No cancellation/modification of existing appointments through the assistant.
- Bedrock interprets natural language probabilistically; schema validation does not guarantee perfect interpretation. Every proposal requires explicit customer review.
- Chat suggestions use the existing 30-minute grid; an explicitly requested time is checked directly against hours and overlap.
- Conversation history may contain customer-entered personal information and is sent to Bedrock with public catalog/draft context. Account profiles, credentials and database appointment records are not sent. Avoid entering personal information.
- Expired conversation rows are not automatically purged. Define retention before production; expiry currently blocks access but does not delete history.
- Rate limiting is process-local, not distributed.
- Idempotency is scoped to the conversation/confirmation, not arbitrary independent bookings. Unconfirmed conversations are not slot reservations.
- Existing overlap queries include cancelled appointments; this inherited behavior has not been changed here.
- The existing public appointment-creation endpoint remains outside the authenticated chatbot and is unchanged in access policy.

Request logs contain generated request ID, model ID, latency and tool name, not question text, credentials or customer profiles. No separate testing project was modified, and no push or deployment is part of this work.
