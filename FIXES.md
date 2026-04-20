# FIXES.md — Bug Registry

All bugs found in the starter repo, documented per the Stage 2 assessment rubric.

---

## Fix 1
- **File:** `api/main.py`
- **Line:** 9
- **Problem:** Redis default host was `"localhost"`. Inside a Docker container,
  localhost resolves to the container itself, not the Redis service. If the
  REDIS_HOST env var is absent the API cannot connect to Redis at all.
- **Fix:** Changed default from `"localhost"` to `"redis"` to match the
  Docker Compose service name resolvable on the internal network.

## Fix 2
- **File:** `api/main.py`
- **Line:** N/A (missing entirely)
- **Problem:** No `/health` endpoint existed. The Dockerfile HEALTHCHECK and
  docker-compose.yml `condition: service_healthy` both require this route.
  Without it Docker marks the container unhealthy and dependent services
  (worker, frontend) never start.
- **Fix:** Added `GET /health` route returning `{"status": "ok"}`.

## Fix 3
- **File:** `api/main.py`
- **Line:** 14
- **Problem:** Jobs pushed to Redis list key `"job"` (singular). The worker
  reads from `"jobs"` (plural). Jobs accumulated in `"jobs"` forever while
  the worker starved reading the permanently empty `"job"` key.
- **Fix:** Changed `r.lpush("job", job_id)` to `r.lpush("jobs", job_id)`.

## Fix 4
- **File:** `api/main.py`
- **Line:** 18
- **Problem:** When a job ID was not found, the API returned
  `{"error": "not found"}` with HTTP 200 OK. Clients could not distinguish
  this from a successful response. Polling logic and integration tests would
  silently pass on missing jobs.
- **Fix:** Replaced with `raise HTTPException(status_code=404, detail="Job not found")`.

## Fix 5
- **File:** `api/main.py`
- **Lines:** 17, 23
- **Problem:** No error handling around Redis calls. A ConnectionError produced
  an unhandled Python traceback in the HTTP response, exposing internals and
  returning a confusing 500.
- **Fix:** Wrapped all Redis calls in try/except RedisConnectionError,
  returning HTTP 503 with a clean message.

## Fix 6
- **File:** `worker/worker.py`
- **Line:** 4
- **Problem:** `signal` module imported but never used. Graceful shutdown was
  intended but not implemented. Docker sends SIGTERM on container stop;
  without a handler the process is force-killed after 10 seconds, losing
  any in-progress job.
- **Fix:** Implemented SIGTERM and SIGINT handlers setting `running = False`
  so the main loop exits cleanly after finishing the current job.

## Fix 7
- **File:** `worker/worker.py`
- **Line:** 11
- **Problem:** `while True` with no exit condition. No way to stop cleanly.
  Every container stop force-killed the process and risked corrupting
  in-progress job state.
- **Fix:** Replaced with `while running` checked against the shutdown flag.

## Fix 8
- **File:** `worker/worker.py`
- **Lines:** 12–15
- **Problem:** No try/except around Redis calls. A ConnectionError crashed
  the worker process permanently — no jobs processed until manual restart.
- **Fix:** Wrapped loop body in try/except with 5-second backoff retry.

## Fix 9
- **File:** `worker/worker.py`
- **Line:** 14
- **Problem:** Job status jumped from "queued" directly to "completed" with
  no intermediate state. If the worker crashed mid-job, status was
  permanently stuck at "queued" with no indication work had started.
- **Fix:** Added `r.hset(f"job:{job_id}", "status", "processing")` at the
  start of process_job.

## Fix 10
- **File:** `frontend/app.js`
- **Line:** 5
- **Problem:** API_URL defaulted to `http://localhost:8000`. Inside the
  frontend container, localhost is the container itself. All proxied API
  calls failed silently with ECONNREFUSED.
- **Fix:** Changed default to `http://api:8000`.

## Fix 11
- **File:** `frontend/app.js`
- **Lines:** 15, 22
- **Problem:** Both catch blocks returned HTTP 500 regardless of actual error.
  A 404 from the API and a 503 became identical 500s, hiding root cause.
- **Fix:** Forward actual status via `err.response?.status || 500` and
  message via `err.response?.data?.detail`.

## Fix 12
- **File:** `frontend/app.js`
- **Line:** 25
- **Problem:** Port hardcoded as 3000. Production services must read
  configuration from environment variables.
- **Fix:** Changed to `parseInt(process.env.PORT || "3000", 10)`.

## Fix 13
- **File:** `frontend/package.json`
- **Line:** N/A (missing field)
- **Problem:** No `"engines"` field. Dockerfile targets Node 20 but nothing
  enforced this — silent incompatibilities on older runtimes.
- **Fix:** Added `"engines": { "node": ">=20.0.0" }`.

## Fix 14
- **File:** `frontend/app.js`
- **Line:** N/A (missing entirely)
- **Problem:** No `/health` endpoint. HEALTHCHECK and service_healthy
  condition had nothing reliable to check against.
- **Fix:** Added `GET /health` returning `{"status":"ok"}`, placed before
  the static middleware so it is always reachable.

## Fix 15
- **File:** `views/index.html`
- **Lines:** 22, 29
- **Problem:** fetch() calls had no try/catch and no res.ok check. Server
  errors left the UI frozen. pollJob() continued with `status = undefined`
  in an infinite loop hammering the server.
- **Fix:** Wrapped both calls in try/catch with res.ok guard.

## Fix 16
- **File:** `views/index.html`
- **Lines:** 24, 43
- **Problem:** innerText used throughout. textContent is correct for plain
  text — innerText triggers layout reflow and leads to XSS habits.
- **Fix:** Replaced all innerText with textContent.

## Fix 17
- **File:** `views/index.html`
- **Line:** 31
- **Problem:** Poll loop only stopped on `status === 'completed'`. Any other
  terminal state caused infinite polling and unbounded server load.
- **Fix:** Introduced TERMINAL_STATES array and changed condition to
  TERMINAL_STATES.includes().

## Fix 18
- **File:** `views/index.html`
- **Line:** 32
- **Problem:** No maximum poll duration. A stuck job polled forever in the
  browser and would hang CI integration tests until the 6-hour runner limit.
- **Fix:** Added attempts counter with MAX_ATTEMPTS = 30 (60 seconds).

## Fix 19
- **File:** `views/index.html`
- **Line:** 22
- **Problem:** POST /submit sent no Content-Type header. Express json()
  middleware requires application/json to parse request bodies. Future job
  parameters would be silently ignored.
- **Fix:** Added Content-Type: application/json header and explicit body.
