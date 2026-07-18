import os

# Port binding
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Timeout config: LLM requests can take longer than the default 30s.
# We increase it to 120s to prevent Gunicorn from killing active generation workers.
timeout = 120

# Worker count (Render free tier works best with 2 workers)
workers = 2
