Works. Two files created:

- **`email_queue.py`** — `EmailQueue` with configurable workers, exponential-backoff retries, and job status tracking. Thread-safe, in-memory, no external dependencies.
- **`example.py`** — Shows enqueueing jobs, starting workers, checking status, and graceful shutdown.

Key assumptions (change if needed):
- **In-memory** — no Redis/RabbitMQ; state is lost on process exit
- **Threading** — workers are daemon threads; `stop()` waits up to 5s for clean exit
- **Retry** — exponential backoff (1s, 2s, 4s by default), max 3 attempts, then `FAILED`
- **Handler** — you pass your own `send_email` callable (SMTP, SendGrid, etc.)