import os
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from supabase import create_client, Client

router = APIRouter(prefix="/api/research", tags=["Research"])

# Initialize Supabase Client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Optional[Client] = (
    create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None
)


# ------------------------------------------------------------------
# Request & Response Schemas
# ------------------------------------------------------------------

class ResearchRequest(BaseModel):
    topic: str = Field(..., description="The research topic or keyword to analyze")
    depth: Optional[str] = Field("standard", description="Analysis depth: 'overview', 'standard', or 'deep'")

class ResearchInsight(BaseModel):
    title: str = Field(..., description="Key insight or finding title")
    summary: str = Field(..., description="Detailed narrative of the insight")
    impact_score: int = Field(..., description="Impact score from 1 (low) to 10 (critical)")

class SignalForgeResponse(BaseModel):
    topic: str = Field(..., description="Target topic requested")
    executive_summary: str = Field(..., description="High-level synthesis of findings")
    key_insights: List[ResearchInsight] = Field(..., description="List of key market or technical insights")
    market_signals: List[str] = Field(..., description="Observed trend signals or emerging patterns")
    recommended_actions: List[str] = Field(..., description="Strategic next steps or recommendations")


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.post("/", response_model=SignalForgeResponse)
async def generate_research(payload: ResearchRequest):
    """
    Generates structured intelligence using Gemini and persists it to Supabase.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY environment variable is missing."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert AI intelligence analyst for SignalForge.
    Perform a comprehensive research synthesis on: '{payload.topic}'.
    Analysis Depth: {payload.depth}.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SignalForgeResponse,
                temperature=0.3,
            )
        )

        raw_json = json.loads(response.text)
        result = SignalForgeResponse(**raw_json)

        # Persist result to Supabase if configured
        if supabase:
            try:
                supabase.table("research_runs").insert({
                    "topic": payload.topic,
                    "depth": payload.depth,
                    "executive_summary": result.executive_summary,
                    "key_insights": [i.model_dump() for i in result.key_insights],
                    "market_signals": result.market_signals,
                    "recommended_actions": result.recommended_actions,
                }).execute()
            except Exception as db_err:
                # Log database write error without failing the client response
                print(f"[Supabase Warning] Failed to log research run: {db_err}")

        return result

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to parse structured JSON from Gemini API response."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gemini Research Generation Error: {str(e)}"
        )


@router.get("/history")
async def get_research_history():
    """
    Retrieves past research runs from Supabase.
    """
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase is not configured on the backend."
        )
    
    try:
        data = supabase.table("research_runs").select("*").order("created_at", desc=True).limit(20).execute()
        return data.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database fetch error: {str(e)}"
        )