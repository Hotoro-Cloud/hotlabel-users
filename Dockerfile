FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Make the DB readiness script executable
RUN chmod +x /app/scripts/ensure_db_ready.py

# Create entrypoint script
RUN echo '#!/bin/bash\n\
# Run database initialization script\n\
python /app/scripts/ensure_db_ready.py\n\
\n\
# Start the application\n\
exec "$@"' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
