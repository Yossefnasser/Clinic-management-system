# Printing subsystem

Overview
- The app enqueues print jobs when appointments are checked-in or when a user requests reprint.
- A small local print agent (recommended) polls the server for pending print jobs, prints them to a local USB ESC/POS printer, and marks jobs done.

DB model
- `PrintJob` (app.models)
  - `id` (auto)
  - `appointment` (FK -> Appointment)
  - `status` ("pending" or "done")
  - `created_at` (timestamp)

Endpoints
1. `GET /print-jobs/pending/`
   - Returns the oldest pending job or `null`.
   - Response shape: `{ "job": { id, appointment_id, display_number, ticket_number, clinic_name, doctor_name, appointment_date, appointment_time, patient_name, patient_phone, service_price, created_at }}`
   - `display_number`: uses `appointment.ticket_number` when assigned (preferred) otherwise falls back to `PrintJob.id`.
   - `appointment_time` is returned as `HH:MM` string or empty string if not set.

2. `POST /print-jobs/<id>/complete/` or POST JSON `{ "job_id": 123 }`
   - Marks a job status as `done`.
   - The URL route is CSRF-exempt to ease local agent usage; the print display UI sends CSRF token when running in-browser.

3. `GET /print-display/`
   - Browser-based print display UI that polls `print-jobs/pending`, shows the ticket, calls `window.print()` and marks job complete.

Server-side behavior
- `Appointment.ticket_number` (nullable) stores the per-doctor-per-day ticket number.
- On check-in: the server computes and assigns `ticket_number` atomically as (count of existing non-null ticket_number for same doctor & date) + 1, saves appointment, then creates a `PrintJob` with `status='pending'`.
- On reprint: if `ticket_number` is missing it assigns one using the same logic, then creates a `PrintJob`.
- Appointments created but not checked-in will not enqueued for printing until checked-in.

Local print-agent (recommended)
- Pattern:
  1. Poll `GET /print-jobs/pending/` (every ~2–5s).
  2. If `job` present, call local `TicketPrinter.print_appointment_ticket(...)` with job data.
  3. After successful printing, POST `/print-jobs/<job_id>/complete/`.
- The agent can be a small Python script using `requests` and the same `TicketPrinter` class from the project (or a copy).

Example local agent (pseudo):
```py
import time, requests
from app.printer import TicketPrinter

POLL = 'https://your-host/print-jobs/pending/'
COMPLETE = 'https://your-host/print-jobs/{id}/complete/'

printer = TicketPrinter(printer_type='usb', usb_vendor_id='0x04b8', usb_product_id='0x0202')

while True:
    r = requests.get(POLL)
    job = r.json().get('job')
    if job:
        # print using local printer
        printer.print_appointment_ticket_from_job(job)
        requests.post(COMPLETE.format(id=job['id']))
    time.sleep(3)
```

Ticket content
- The ticket contains:
  - Large ticket number (the `ticket_number` if assigned)
  - Clinic and doctor
  - Appointment date & time
  - Patient name and phone
  - Printed timestamp

Notes & next steps
- If you want real-time pushes instead of polling, we can add a WebSocket endpoint (channels) but polling is simpler and reliable for local agents.
- I can add a small example local agent script (`scripts/print_agent.py`) and a DRF endpoint to list multiple pending jobs if needed.
