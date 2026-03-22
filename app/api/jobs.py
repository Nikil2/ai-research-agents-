"""
Research Job endpoints — core API for creating and tracking research jobs.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from database.schemas import CreateJobRequest, JobCreatedResponse, JobStatusResponse
from database.crud import create_job, get_job, get_jobs_by_user, update_job_status
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/", response_model=JobCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_research_job(job_request: CreateJobRequest, user_id: str = None):
    """
    Create a new research job.
    
    Params:
    - topic: The research topic (e.g., "AI in healthcare 2025")
    - depth: Research depth — "quick", "detailed", or "deep_dive"
    
    Returns: Job ID + status
    
    NOTE: In production, user_id would come from JWT token.
    For now, passed as header for testing.
    """
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user_id required (add to header or JWT)"
        )
    
    try:
        # Convert user_id string to UUID
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format"
        )
    
    # Create job in database
    try:
        new_job = create_job(
            user_id=str(user_uuid),
            topic=job_request.topic,
            depth=job_request.depth
        )
        
        return JobCreatedResponse(
            job_id=new_job["id"],
            topic=new_job["topic"],
            depth=new_job["depth"],
            status="pending",
            message="Research job created. Poll /api/jobs/{job_id} for status updates."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Poll the status of a research job.
    
    Returns: Job status (pending/running/completed/failed) + progress
    
    Used by UI to show real-time progress while agents are working.
    """
    
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job_id format"
        )
    
    try:
        job = get_job(str(job_uuid))
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """
    Server-Sent Events (SSE) stream for real-time job progress.
    
    Returns: Continuous stream of status updates as agents work.
    
    TODO: Implement full SSE when agents are running (Day 2).
    For now, returns a placeholder response.
    """
    
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job_id format"
        )
    
    try:
        job = get_job(str(job_uuid))
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Placeholder: Return a simple event stream
        async def event_generator():
            yield f'data: {{"status": "streaming", "job_id": "{job_id}"}}\n\n'
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{user_id}")
async def get_user_jobs(user_id: str):
    """
    Get all research jobs for a specific user.
    
    Returns: List of job summaries (not full details).
    """
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format"
        )
    
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
