#!/usr/bin/env python3
import os
import subprocess
import sys
import time

def run_db_init():
    """Run the database initialization script."""
    print("Running database initialization...")
    subprocess.run([sys.executable, "scripts/ensure_db_ready.py"], check=True)
    print("Database initialization completed.")

def start_app():
    """Start the FastAPI application."""
    port = os.getenv("SERVICE_PORT", "8005")
    print(f"Starting application on port {port}...")
    subprocess.run([
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", port
    ], check=True)

if __name__ == "__main__":
    run_db_init()
    start_app() 