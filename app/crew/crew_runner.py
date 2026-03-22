"""
Crew Assembly and Runner — orchestrates the 4-agent research pipeline.
"""

import uuid
import os
import asyncio
from datetime import datetime, timezone
from crewai import Crew, Process
from database.crud import update_job_status, save_agent_output, save_report, get_job
from database.connection import get_connection
from app.core.progress import progress_manager
from app.agents.researcher import get_researcher_agent
from app.agents.analyst import get_analyst_agent
from app.agents.fact_checker import get_fact_checker_agent
from app.agents.writer import get_writer_agent
from app.tasks.research_task import get_research_task
from app.tasks.analysis_task import get_analysis_task
from app.tasks.factcheck_task import get_factcheck_task
from app.tasks.writing_task import get_writing_task


async def run_job(job_id: str, topic: str, depth: str) -> None:
    """
    Main job runner. Orchestrates the 4-agent research crew.
    Called as a background task from the FastAPI endpoint.
    """
    
    jid = uuid.UUID(job_id)
    
    try:
        # Mark job as running
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE research_jobs
                SET status = 'running', started_at = NOW()
                WHERE id = %s;
            """, (str(jid),))
            conn.commit()
        conn.close()
        
        await progress_manager.emit(job_id, "stage_changed",
            stage="starting", progress=0,
            message=f"🚀 Starting research on: {topic}")
        
        def schedule_emit(event_type: str, stage: str, progress: int, message: str) -> None:
            """Send SSE updates from sync callbacks without blocking."""
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(progress_manager.emit(
                    job_id, event_type, stage=stage, progress=progress, message=message
                ))
            except RuntimeError:
                asyncio.run(progress_manager.emit(
                    job_id, event_type, stage=stage, progress=progress, message=message
                ))

        def make_step_callback(stage: str, progress: int):
            def _callback(step_output):
                text = str(step_output).strip()
                if text:
                    schedule_emit("partial_output", stage, progress, text)
                return step_output
            return _callback

        # ── AGENT 1: Researcher ───────────────────────
        await progress_manager.emit(job_id, "stage_changed",
            stage="researcher", progress=10,
            message="🔍 Researcher agent searching the web...")
        
        try:
            # Get researcher agent (uses built-in crewai tools)
            researcher = get_researcher_agent(None)
            research_task = get_research_task(researcher, topic, depth)
            
            crew = Crew(
                agents=[researcher],
                tasks=[research_task],
                process=Process.sequential,
                verbose=True,
                step_callback=make_step_callback("researcher", 10)
            )
            
            research_output = crew.kickoff()
            
            research_output_str = str(research_output)
            
            # Save to DB
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO agent_outputs (job_id, agent_name, output_type, content, llm_used)
                    VALUES (%s, %s, %s, %s, %s);
                """, (str(jid), "researcher", "research", research_output_str, "groq/mixtral-8x7b"))
                conn.commit()
            conn.close()
            
            await progress_manager.emit(job_id, "progress",
                stage="researcher", progress=25,
                message="✅ Research complete. Sources collected.")
        
        except Exception as e:
            await progress_manager.emit(job_id, "failed",
                stage="researcher", progress=25,
                message=f"❌ Researcher failed: {str(e)}")
            raise
        
        # ── AGENT 2: Analyst ──────────────────────────
        await progress_manager.emit(job_id, "stage_changed",
            stage="analyst", progress=30,
            message="📊 Analyst extracting insights...")
        
        try:
            analyst = get_analyst_agent()
            analysis_task = get_analysis_task(analyst)
            
            crew = Crew(
                agents=[analyst],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=True,
                step_callback=make_step_callback("analyst", 30)
            )
            
            analysis_output = crew.kickoff(inputs={"research": research_output_str})
            analysis_output_str = str(analysis_output)
            
            # Save to DB
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO agent_outputs (job_id, agent_name, output_type, content, llm_used)
                    VALUES (%s, %s, %s, %s, %s);
                """, (str(jid), "analyst", "analysis", analysis_output_str, "groq/mixtral-8x7b"))
                conn.commit()
            conn.close()
            
            await progress_manager.emit(job_id, "progress",
                stage="analyst", progress=50,
                message="✅ Analysis complete.")
        
        except Exception as e:
            await progress_manager.emit(job_id, "failed",
                stage="analyst", progress=50,
                message=f"❌ Analyst failed: {str(e)}")
            raise
        
        # ── AGENT 3: Fact Checker ─────────────────────
        await progress_manager.emit(job_id, "stage_changed",
            stage="fact_checker", progress=55,
            message="🔍 Fact checker verifying claims...")
        
        try:
            # Get fact checker agent
            fact_checker = get_fact_checker_agent(None)
            factcheck_task = get_factcheck_task(fact_checker)
            
            crew = Crew(
                agents=[fact_checker],
                tasks=[factcheck_task],
                process=Process.sequential,
                verbose=True,
                step_callback=make_step_callback("fact_checker", 55)
            )
            
            factcheck_output = crew.kickoff(inputs={
                "research": research_output_str,
                "analysis": analysis_output_str
            })
            
            factcheck_output_str = str(factcheck_output)
            
            # Save to DB
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO agent_outputs (job_id, agent_name, output_type, content, llm_used)
                    VALUES (%s, %s, %s, %s, %s);
                """, (str(jid), "fact_checker", "fact_check", factcheck_output_str, "ollama/qwen2.5-coder"))
                conn.commit()
            conn.close()
            
            await progress_manager.emit(job_id, "progress",
                stage="fact_checker", progress=70,
                message="✅ Fact check complete.")
        
        except Exception as e:
            await progress_manager.emit(job_id, "failed",
                stage="fact_checker", progress=70,
                message=f"❌ Fact checker failed: {str(e)}")
            raise
        
        # ── AGENT 4: Writer ───────────────────────────
        await progress_manager.emit(job_id, "stage_changed",
            stage="writer", progress=75,
            message="✍️ Writer composing final report...")
        
        try:
            writer = get_writer_agent()
            writing_task = get_writing_task(writer, job_id)
            
            crew = Crew(
                agents=[writer],
                tasks=[writing_task],
                process=Process.sequential,
                verbose=True,
                step_callback=make_step_callback("writer", 75)
            )
            
            report_content = crew.kickoff(inputs={
                "research": research_output_str,
                "analysis": analysis_output_str,
                "factcheck": factcheck_output_str
            })
            
            report_content_str = str(report_content)
            
            # Save report to disk
            output_dir = os.getenv("OUTPUT_DIR", "/Users/nikilgoindani/Desktop/pro-1/backend/output/reports")
            os.makedirs(output_dir, exist_ok=True)
            file_path = f"{output_dir}/{job_id}.md"
            with open(file_path, "w") as f:
                f.write(report_content_str)
            
            # Fetch job to get user_id
            job_record = get_job(job_id)
            user_id = job_record.get("user_id") if job_record else None
            
            # Save report to DB
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO reports (job_id, user_id, title, content_markdown, file_path, word_count, source_count, is_public)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    str(jid),
                    user_id,
                    f"Research Report: {topic[:60]}",
                    report_content_str,
                    file_path,
                    len(report_content_str.split()),
                    6,  # Approximate source count
                    False
                ))
                # Mark job as completed
                cursor.execute("""
                    UPDATE research_jobs
                    SET status = 'completed', completed_at = NOW()
                    WHERE id = %s;
                """, (str(jid),))
                conn.commit()
            conn.close()
            
            await progress_manager.emit(job_id, "completed",
                stage="done", progress=100,
                message="🎉 Report ready! Download from dashboard.")
        
        except Exception as e:
            await progress_manager.emit(job_id, "failed",
                stage="writer", progress=75,
                message=f"❌ Writer failed: {str(e)}")
            raise
    
    except Exception as e:
        # Mark job as failed
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE research_jobs
                SET status = 'failed', error_message = %s, completed_at = NOW()
                WHERE id = %s;
            """, (str(e), str(jid)))
            conn.commit()
        conn.close()
        
        print(f"Job {job_id} failed: {str(e)}")
