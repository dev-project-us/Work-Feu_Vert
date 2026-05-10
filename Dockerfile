# ──────────────────────────────────────────────────────────────────────────────
# Feu Vert Annecy Dashboard — Dockerfile
# Base: python:3.12-slim  (Debian Bookworm, ~50 MB uncompressed)
#
# Teaching note:
#   We use a multi-stage-lite approach:
#     Stage 1 — install dependencies into a virtual env (no cache bleed)
#     Stage 2 — copy only the venv + app code into the final image
#   This keeps the final image lean and makes rebuilds faster when only
#   app code changes (dependencies layer is cached separately).
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: dependency builder ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools (needed for some pandas C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first — Docker layer cache will skip this step
# on subsequent builds if requirements.txt hasn't changed.
COPY requirements.txt .

# Install into an isolated venv so we can copy it cleanly
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip --quiet && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Create a non-root user for security (good practice on Proxmox VMs)
RUN useradd --create-home --shell /bin/bash fvapp

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY engine/     ./engine/
COPY app.py      ./app.py
COPY .streamlit/ ./.streamlit/

# Data directories — these are EMPTY in the image.
# They are populated via Docker volume mounts at runtime (see docker-compose.yml).
RUN mkdir -p \
        /app/resources/SUC \
        /app/resources/familles \
        /app/resources/Pneus \
        /app/resources/ratios\ prioritaires \
        /app/resources/suivi\ vendeur \
        /app/resources/defectuosite \
        /app/monthly_recap \
        /app/trimestres \
    && chown -R fvapp:fvapp /app

USER fvapp

# Activate venv
ENV PATH="/opt/venv/bin:$PATH"

# Streamlit listens on 8501 by default
EXPOSE 8501

# Health check — Streamlit returns 200 on its root path
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

ENTRYPOINT ["streamlit", "run", "app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.headless=true"]
