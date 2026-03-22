from .connection import get_connection
import uuid
import psycopg2
from datetime import datetime

def create_user(email: str, username: str, password_hash: str):
    """Create a new user in the database."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (email, username, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, email, username, is_active, last_login_at, created_at;
            """, (email, username, password_hash))
            new_user = cursor.fetchone()
            conn.commit()
            return new_user
    except psycopg2.IntegrityError as e:
        conn.rollback()
        raise Exception(f"User with this email or username already exists.")
    finally:
        conn.close()

def get_user_by_email(email: str):
    """Retrieve a user by their email."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, email, username, password_hash, is_active, last_login_at, created_at
                FROM users
                WHERE email = %s;
            """, (email,))
            return cursor.fetchone()
    finally:
        conn.close()


# ──────────────────────────────────────────────
# RESEARCH JOB CRUD OPERATIONS
# ──────────────────────────────────────────────

def create_job(user_id: str, topic: str, depth: str):
    """Create a new research job."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO research_jobs (user_id, topic, depth, status)
                VALUES (%s, %s, %s, 'pending')
                RETURNING id, user_id, topic, depth, status, error_message, failed_agent, started_at, completed_at, created_at;
            """, (user_id, topic, depth))
            new_job = cursor.fetchone()
            conn.commit()
            return new_job
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to create job: {str(e)}")
    finally:
        conn.close()


def get_job(job_id: str):
    """Retrieve a research job by ID."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, topic, depth, status, error_message, failed_agent, started_at, completed_at, created_at
                FROM research_jobs
                WHERE id = %s;
            """, (job_id,))
            return cursor.fetchone()
    finally:
        conn.close()


def get_jobs_by_user(user_id: str):
    """Retrieve all research jobs for a specific user."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, topic, depth, status, error_message, failed_agent, started_at, completed_at, created_at
                FROM research_jobs
                WHERE user_id = %s
                ORDER BY created_at DESC;
            """, (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()


def update_job_status(job_id: str, status: str, error_message: str = None, failed_agent: str = None):
    """Update the status of a research job."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if status == "running" and error_message is None:
                # Set started_at when transitioning to running
                cursor.execute("""
                    UPDATE research_jobs
                    SET status = %s, started_at = NOW()
                    WHERE id = %s;
                """, (status, job_id))
            elif status == "completed" and error_message is None:
                # Set completed_at when transitioning to completed
                cursor.execute("""
                    UPDATE research_jobs
                    SET status = %s, completed_at = NOW()
                    WHERE id = %s;
                """, (status, job_id))
            else:
                # For failed status, set both error message and failed_agent
                cursor.execute("""
                    UPDATE research_jobs
                    SET status = %s, error_message = %s, failed_agent = %s, completed_at = NOW()
                    WHERE id = %s;
                """, (status, error_message, failed_agent, job_id))
            
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to update job status: {str(e)}")
    finally:
        conn.close()


# ──────────────────────────────────────────────
# AGENT OUTPUT & REPORT STORAGE
# ──────────────────────────────────────────────

def save_agent_output(job_id: str, agent_name: str, agent_output: str, stage: int = None):
    """Save the output from an agent to the database."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO agent_outputs (job_id, agent_name, output, stage, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id, job_id, agent_name, output, stage, created_at;
            """, (job_id, agent_name, agent_output, stage))
            result = cursor.fetchone()
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to save agent output: {str(e)}")
    finally:
        conn.close()


def save_report(job_id: str, report_content: str, report_path: str = None):
    """Save the final report to the database."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO reports (job_id, content, report_path, created_at)
                VALUES (%s, %s, %s, NOW())
                RETURNING id, job_id, content, report_path, created_at;
            """, (job_id, report_content, report_path))
            result = cursor.fetchone()
            conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to save report: {str(e)}")
    finally:
        conn.close()

