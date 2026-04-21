import os
import signal
import time

import redis
import redis.exceptions


# Connection
r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
)

running = True


def handle_shutdown(signum, frame):
    global running
    print("Shutdown signal received, finishing current job...")
    running = False


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


# Job processor
def process_job(job_id):
    r.hset(f"job:{job_id}", "status", "processing")
    print(f"Processing job {job_id}")
    time.sleep(2)
    r.hset(f"job:{job_id}", "status", "completed")
    print(f"Done: {job_id}")


# Main loop
print("Worker started. Waiting for jobs...")

while running:
    try:
        job = r.brpop("jobs", timeout=5)
        if job:
            _, job_id = job
            process_job(job_id.decode())
    except redis.exceptions.ConnectionError:
        print("Redis connection lost. Retrying in 5 seconds...")
        time.sleep(5)


print("Worker shut down cleanly.")
