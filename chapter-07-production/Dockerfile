FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

# Install dependencies separately so Vercel can reuse this build layer
# when application code changes but requirements.txt does not.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Run the container as an unprivileged user.
RUN useradd --create-home --uid 10001 appuser

# Runtime modules and the inspected, curated RAG corpus are copied. Secrets,
# tests, PDFs, and local development files remain outside the image.
COPY --chown=appuser:appuser *.py ./
COPY --chown=appuser:appuser data ./data

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true --server.fileWatcherType=none --server.maxUploadSize=4 --browser.gatherUsageStats=false"]
