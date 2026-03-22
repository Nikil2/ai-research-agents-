"""
Research Job endpoints — core API for creating and tracking research jobs.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Header
from fastapi.responses import StreamingResponse
from database.schemas import CreateJobRequest, JobCreatedResponse, JobStatusResponse, ReportResponse
from database.crud import create_job, get_job, get_jobs_by_user, update_job_status
from app.core.progress import progress_manager
from app.crew.crew_runner import run_job
import uuid

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/", response_model=JobCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_research_job(
    job_request: CreateJobRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Header(default=None)
):
    """
    Create a new research job and start background processing.
    
    Accepts:
    - topic: Research topic (required)
    - depth: "quick", "detailed", or "deep_dive"
    - user_id: Passed via header from auth system
    
    The crew will run in the background. Poll GET /api/jobs/{job_id} for updates.
    """
    
    # Require user_id from authenticated request
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user_id header is required. Must be logged in."
        )
    
    # Validate UUID format
    try:
        user_id = str(uuid.UUID(user_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format. Must be a valid UUID."
        )
    
    try:
        # Create job in database
        new_job = create_job(user_id=user_id, topic=job_request.topic, depth=job_request.depth)
        job_id = new_job["id"]
        
        # Start background task (non-blocking)
        background_tasks.add_task(run_job, str(job_id), job_request.topic, job_request.depth)
        
        return JobCreatedResponse(
            job_id=job_id,
            topic=new_job["topic"],
            depth=new_job["depth"],
            status="pending",
            message="Research job created. Poll GET /api/jobs/{job_id} for status updates."
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Poll the status of a research job.
    
    Returns:
    - Job status: pending | running | completed | failed
    - Progress information and timestamps
    
    Used by UI to show real-time status while agents are working.
    """
    
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format")
    
    try:
        job = get_job(str(job_uuid))
        
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
        return JobStatusResponse(
            id=job["id"],
            user_id=job["user_id"],
            topic=job["topic"],
            depth=job["depth"],
            status=job["status"],
            error_message=job.get("error_message"),
            failed_agent=job.get("failed_agent"),
            started_at=job.get("started_at"),
            completed_at=job.get("completed_at"),
            created_at=job["created_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """
    Server-Sent Events (SSE) stream for real-time job progress.
    
    Returns:
    - Continuous stream of status updates as agents work
    - Events include: progress %, current stage, messages
    - Stream ends when job completes or fails
    
    Used by Streamlit UI to show live progress bar and status.
    """
    
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format")
    
    try:
        job = get_job(str(job_uuid))
        
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
        async def event_generator():
            """Generate SSE events from progress manager."""
            async for event in progress_manager.subscribe(job_id):
                yield f"data: {event}\n\n"
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_jobs(user_id: str):
    """
    Get all research jobs for a specific user.
    
    Returns:
    - List of job summaries (not full details)
    - Ordered by creation date (newest first)
    """
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user_id format")
    
    try:
        jobs = get_jobs_by_user(str(user_uuid))
        return {
            "user_id": user_id,
            "jobs": [
                JobStatusResponse(
                    id=job["id"],
                    user_id=job["user_id"],
                    topic=job["topic"],
                    depth=job["depth"],
                    status=job["status"],
                    error_message=job.get("error_message"),
                    failed_agent=job.get("failed_agent"),
                    started_at=job.get("started_at"),
                    completed_at=job.get("completed_at"),
                    created_at=job["created_at"]
                )
                for job in jobs
            ],
            "total": len(jobs)
        }
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/reports/{job_id}", response_model=ReportResponse)
async def get_report(job_id: str):
    """
    Fetch a completed research report.
    
    Returns:
    - Full report content in Markdown format
    - Metadata (title, word count, sources, etc.)
    
    Available after job status is 'completed'.
    """
    
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format")
    
    try:
        from database.connection import get_connection
        
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, job_id, user_id, title, content_markdown, file_path, word_count, source_count, is_public, created_at
                FROM reports
                WHERE job_id = %s;
            """, (str(job_uuid),))
            report = cursor.fetchone()
        conn.close()
        
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        
        return ReportResponse(
            id=report["id"],
            job_id=report["job_id"],
            user_id=report["user_id"],
            title=report["title"],
            content_markdown=report["content_markdown"],
            file_path=report["file_path"],
            word_count=report["word_count"],
            source_count=report["source_count"],
            is_public=report["is_public"],
            created_at=report["created_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

