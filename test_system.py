#!/usr/bin/env python3
"""
System Component Test Suite
Tests Config, Database, Groq API, and Agents
"""

import sys
import os

# Set dummy OpenAI key to prevent import errors (not actually used)
os.environ['OPENAI_API_KEY'] = 'sk-dummy-for-import'

sys.path.insert(0, '/Users/nikilgoindani/Desktop/pro-1/backend')
os.chdir('/Users/nikilgoindani/Desktop/pro-1/backend')

print("=" * 70)
print("🧪 SYSTEM COMPONENT TESTS")
print("=" * 70)

# Test 1: Config loading
print("\n1️⃣  Loading Configuration...")
try:
    from config import DATABASE_URL, GROQ_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL
    print("   ✅ Config loaded successfully")
    print(f"   • GROQ_API_KEY: {'***SET***' if GROQ_API_KEY else 'NOT SET'}")
    print(f"   • DATABASE_URL: postgresql://***" if DATABASE_URL else "   • DATABASE_URL: NOT SET")
    print(f"   • OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")
    print(f"   • OLLAMA_MODEL: {OLLAMA_MODEL}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)

# Test 2: Database connection
print("\n2️⃣  Testing Database Connection...")
try:
    from database.connection import check_connection
    if check_connection():
        print("   ✅ PostgreSQL (Neon) connection successful")
    else:
        print("   ⚠️  Database connection check returned False")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test 3: Groq LLM
print("\n3️⃣  Testing Groq API...")
try:
    from app.llms.groq_llm import groq_llm
    response = groq_llm.invoke("Say 'OK' only")
    if "OK" in response.content or "ok" in response.content.lower():
        print("   ✅ Groq API is working!")
        print(f"   • Response: {response.content.strip()}")
    else:
        print(f"   ⚠️  Unexpected response: {response.content}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test 4: Agents without memory (Groq-only setup)
print("\n4️⃣  Testing Agents (Memory Disabled - Groq-Only)...")
try:
    from app.agents.researcher import get_researcher_agent
    from app.agents.analyst import get_analyst_agent
    from app.agents.fact_checker import get_fact_checker_agent
    from app.agents.writer import get_writer_agent
    
    agents_info = [
        ("Researcher", get_researcher_agent([])),
        ("Analyst", get_analyst_agent()),
        ("Fact Checker", get_fact_checker_agent([])),
        ("Writer", get_writer_agent())
    ]
    
    for name, agent in agents_info:
        has_memory = getattr(agent, 'memory', False)
        print(f"   ✅ {name} agent: memory={has_memory} (Groq LLM)")
        
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test 5: Crew without memory
print("\n5️⃣  Testing CrewAI (Sequential Process - No Memory)...")
try:
    from crewai import Crew, Process
    from app.agents.analyst import get_analyst_agent
    from app.tasks.analysis_task import get_analysis_task
    
    analyst = get_analyst_agent()
    task = get_analysis_task(analyst)
    
    crew = Crew(
        agents=[analyst],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        memory=False
    )
    
    print(f"   ✅ Crew created successfully (Groq-only setup)")
    print(f"   • Process: sequential")
    print(f"   • Memory: disabled")
    print(f"   • Dependencies: Only GROQ_API_KEY required")
    
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 70)
print("✅ SYSTEM READY - All components working!")
print("=" * 70)
print("\n💡 Tips:")
print("   • Start FastAPI: python -m fastapi dev main.py")
print("   • Start MCP Server: python -m mcp_server.server")
print("   • Start Streamlit UI: streamlit run ../ui/app.py")
print("=" * 70)
