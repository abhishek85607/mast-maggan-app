# stage 1 : Builder stage 

FROM python:3.10-slim AS builder 
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
	gcc libc-dev && \
	rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# stage 2 : Runner stage 

FROM python:3.10-slim AS runner

WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY --from=builder /root/.local /home/appuser/.local  
COPY --chown=appuser:appuser . .
ENV PATH=/home/appuser/.local/bin:$PATH 
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
	 
