#!/usr/bin/env python3
"""
Script to ensure the database is ready for the user profiling service.
This script:
1. Checks connection to the PostgreSQL database
2. Creates the database if it doesn't exist
3. Ensures Alembic migration files are properly set up
4. Runs alembic migrations
"""

import os
import sys
import time
import logging
import subprocess
import shutil
from sqlalchemy import create_engine, exc, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get database URL from environment
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/hotlabel_users")
MAX_RETRIES = 10
RETRY_DELAY = 5  # seconds

def get_postgres_base_url():
    """Extract the base URL without database name."""
    parts = DB_URL.split("/")
    base_url = "/".join(parts[:-1]) + "/postgres"
    return base_url

def check_database_connection():
    """Check if we can connect to the database."""
    for attempt in range(MAX_RETRIES):
        try:
            engine = create_engine(DB_URL)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Successfully connected to the database.")
                return True
        except exc.OperationalError as e:
            logger.warning(f"Database connection attempt {attempt+1}/{MAX_RETRIES} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Failed to connect to the database after several attempts.")
                return False

def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    try:
        # Connect to the postgres database to check if our target database exists
        base_url = get_postgres_base_url()
        engine = create_engine(base_url)
        
        # Extract the database name from the URL
        db_name = DB_URL.split("/")[-1]
        
        with engine.connect() as conn:
            # Check if the database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if not result.fetchone():
                # If it doesn't exist, create it
                # We need to commit outside of a transaction
                conn.execute(text("commit"))
                logger.info(f"Creating database '{db_name}'...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.info(f"Database '{db_name}' created successfully.")
            else:
                logger.info(f"Database '{db_name}' already exists.")
        return True
    except Exception as e:
        logger.error(f"Failed to create database: {str(e)}")
        return False

def ensure_alembic_setup():
    """Ensure Alembic files are properly set up."""
    migrations_dir = "migrations"
    env_py_path = os.path.join(migrations_dir, "env.py")
    script_py_mako_path = os.path.join(migrations_dir, "script.py.mako")
    versions_dir = os.path.join(migrations_dir, "versions")
    
    # Check if directories exist
    if not os.path.exists(migrations_dir):
        logger.info(f"Creating migrations directory at {migrations_dir}")
        os.makedirs(migrations_dir, exist_ok=True)
    
    if not os.path.exists(versions_dir):
        logger.info(f"Creating versions directory at {versions_dir}")
        os.makedirs(versions_dir, exist_ok=True)
    
    # Check if required files exist
    alembic_files_exist = os.path.exists(env_py_path) and os.path.exists(script_py_mako_path)
    if not alembic_files_exist:
        logger.error("Required Alembic files are missing. Database migrations cannot be run.")
        logger.error("Please ensure env.py and script.py.mako exist in the migrations directory.")
        logger.error("Checking if files exist in the app directory...")
        
        # Try to find env.py and script.py.mako elsewhere
        for root, dirs, files in os.walk("/app"):
            if "env.py" in files and "script.py.mako" in files:
                src_dir = root
                logger.info(f"Found Alembic files in {src_dir}, copying to {migrations_dir}")
                
                # Copy the files to the migrations directory
                if not os.path.exists(env_py_path) and os.path.exists(os.path.join(src_dir, "env.py")):
                    shutil.copy(os.path.join(src_dir, "env.py"), env_py_path)
                    logger.info(f"Copied env.py to {env_py_path}")
                
                if not os.path.exists(script_py_mako_path) and os.path.exists(os.path.join(src_dir, "script.py.mako")):
                    shutil.copy(os.path.join(src_dir, "script.py.mako"), script_py_mako_path)
                    logger.info(f"Copied script.py.mako to {script_py_mako_path}")
                
                return os.path.exists(env_py_path) and os.path.exists(script_py_mako_path)
        
        # If we couldn't find the files, create them
        logger.info("Could not find existing Alembic files, initializing new ones...")
        try:
            subprocess.run(["alembic", "init", migrations_dir], check=True)
            logger.info("Alembic initialization completed successfully.")
            
            # Update the alembic.ini file with our database URL
            with open("alembic.ini", "r") as f:
                alembic_ini = f.read()
            
            # Replace the default sqlalchemy.url with our DB_URL
            alembic_ini = alembic_ini.replace("sqlalchemy.url = driver://user:pass@localhost/dbname", 
                                             f"sqlalchemy.url = {DB_URL}")
            
            with open("alembic.ini", "w") as f:
                f.write(alembic_ini)
            
            logger.info("Updated alembic.ini with our database URL.")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to initialize Alembic: {str(e)}")
            return False
    
    return True

def run_migrations():
    """Run alembic migrations."""
    try:
        logger.info("Running database migrations...")
        # Check if alembic.ini exists, if not create it
        if not os.path.exists("alembic.ini"):
            logger.info("Creating alembic.ini...")
            with open("alembic.ini", "w") as f:
                f.write(f"""[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = {DB_URL}

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""")
        
        # First make sure our alembic setup is correct
        if not ensure_alembic_setup():
            logger.error("Alembic setup is incomplete. Cannot run migrations.")
            return False
        
        # Check if there are any migration files in the versions directory
        versions_dir = os.path.join("migrations", "versions")
        migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py')]
        
        if not migration_files:
            logger.warning("No migration files found in versions directory.")
            # Try to generate a migration based on current models
            try:
                logger.info("Attempting to create initial migration...")
                # Ensure models are imported
                subprocess.run(["python", "-c", "from app.models import *; print('Models imported successfully')"], check=True)
                subprocess.run(["alembic", "revision", "--autogenerate", "-m", "initial_schema"], check=True)
                logger.info("Initial migration created successfully.")
            except subprocess.SubprocessError as e:
                logger.error(f"Failed to create initial migration: {str(e)}")
                return False
        
        # Run migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("Database migrations completed successfully.")
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"Migration failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {str(e)}")
        return False

def main():
    """Main function to ensure database is ready."""
    logger.info("Ensuring database is ready...")
    
    # First, try to create the database if it doesn't exist
    if not create_database_if_not_exists():
        logger.error("Failed to create or validate database.")
        sys.exit(1)
    
    # Then, check if we can connect to it
    if not check_database_connection():
        logger.error("Could not connect to the database.")
        sys.exit(1)
    
    # Finally, run migrations
    if not run_migrations():
        logger.error("Database migrations failed.")
        sys.exit(1)
    
    logger.info("Database is ready.")
    sys.exit(0)

if __name__ == "__main__":
    main()
