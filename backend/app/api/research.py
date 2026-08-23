from datetime import datetime
import json
import os
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from google import genai
from google.genai import types
import httpx
from pydantic import BaseModel, Field
from upstash_redis.asyncio import Redis

router = APIRouter(prefix="/api/research", tags=["research"])

# Global Client Initializations
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Upstash Redis Async Client (automatically reads env vars)
redis_client = Redis.from_env()

CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24 hours


# --- 1. HELPER FUNCTIONS ---
def get_cache_key(topic: str, depth: str) -> str:
    """Normalizes the topic string into a consistent cache key."""
    cleaned_topic = topic.strip().lower()
    return f"research:{cleaned_topic}:{depth}"


def calculate_impact_score(
    sources: List[dict], summary_text: str, citation_count: int
) -> int:
    """Calculates a deterministic 1-10 Impact Score."""
    if not sources:
        return 5

    current_year = datetime.now().year
    ages = []
    for s in sources:
        try:
            pub_year = int(s.get("date", str(current_year))[:4])
            ages.append(max(0, current_year - pub_year))
        except ValueError:
            ages.append(2)

    avg_age = sum(ages) / len(ages) if ages else 2
    recency_score = max(0.0, 4.0 - (avg_age * 0.8))
    volume_score = min(3.0, len(sources) * 0.6)
    grounding_score = min(3.0, citation_count * 1.5)

    total_score = round(recency_score + volume_score + grounding_score)
    return max(1, min(10, int(total_score)))


# --- 2. SCHEMAS ---
class ResearchRequest(BaseModel):
    topic: str
    depth: str = "standard"


class InsightLLM(BaseModel):
    title: str = Field(description="Title of the research insight")
    summary: str = Field(
        description="Detailed summary of the insight with inline citations like [1]"
    )


class ResearchResponseLLM(BaseModel):
    executive_summary: str = Field(
        description="Overall summary of the research topic with inline citations like [1], [2]"
    )
    key_insights: List[InsightLLM]
    market_signals: List[str] = Field(
        description="Key market trends or signals extracted from research"
    )
    recommended_actions: List[str] = Field(
        description="Actionable steps or takeaways"
    )


# --- 3. ARXIV FETCHER ---
async def fetch_arxiv_sources(
    topic: str, max_results: int = 5
) -> List[dict]:
    query_url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(topic)}&max_results={max_results}"

    async with httpx.AsyncClient() as http_client:
        try:
            res = await http_client.get(
                query_url,
                headers={"User-Agent": "SignalForge/1.0"},
                timeout=10.0,
            )
            res.raise_for_status()

            root = ET.fromstring(res.text)
            namespace = {"atom": "http://www.w3.org/2005/Atom"}

            sources = []
            for entry in root.findall("atom:entry", namespace):
                title_elem = entry.find("atom:title", namespace)
                summary_elem = entry.find("atom:summary", namespace)
                published_elem = entry.find("atom:published", namespace)
                id_elem = entry.find("atom:id", namespace)

                title = (
                    title_elem.text.strip().replace("\n", " ")
                    if title_elem is not None
                    else "No Title"
                )
                summary = (
                    summary_elem.text.strip().replace("\n", " ")
                    if summary_elem is not None
                    else ""
                )
                published = (
                    published_elem.text[:10]
                    if published_elem is not None
                    else ""
                )
                url = (
                    id_elem.text.strip() if id_elem is not None else ""
                )

                sources.append(
                    {
                        "title": title,
                        "snippet": (
                            summary[:250] + "..."
                            if len(summary) > 250
                            else summary
                        ),
                        "url": url,
                        "date": published,
                    }
                )
            return sources
        except Exception as e:
            print(f"arXiv Fetch Error: {e}")
            return []


# --- 4. ENDPOINT WITH REDIS CACHING ---
@router.post("/")
async def analyze_topic(req: ResearchRequest):
    cache_key = get_cache_key(req.topic, req.depth)

    # --------------------------------------------------
    # CACHE CHECK: Read from Upstash Redis
    # --------------------------------------------------
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            print(f"⚡ [CACHE HIT] Returning cached response for '{cache_key}'")
            # Upstash automatically deserializes or returns string
            response_json = (
                json.loads(cached_data)
                if isinstance(cached_data, str)
                else cached_data
            )
            response_json["cached"] = True
            return response_json
    except Exception as e:
        print(f"⚠️ Redis read warning: {e}")  # Fail-safe: continue if Redis is down

    # --------------------------------------------------
    # CACHE MISS: Execute arXiv + Gemini Pipeline
    # --------------------------------------------------
    print(f"🐢 [CACHE MISS] Synthesizing topic '{req.topic}' via arXiv & Gemini")
    try:
        sources = await fetch_arxiv_sources(req.topic)

        context_str = "\n".join(
            [
                f"[{i+1}] Title: {s['title']}\nSnippet: {s['snippet']}\nURL: {s['url']}\nDate: {s['date']}\n"
                for i, s in enumerate(sources)
            ]
        )

        prompt = (
            "Synthesize the research topic using ONLY the provided sources where relevant.\n"
            f"Topic: {req.topic}\n\n"
            "Retrieved Sources:\n"
            f"{context_str if context_str else 'No academic papers found. Synthesize based on domain knowledge.'}\n\n"
            "Instructions:\n"
            "- Include inline citations like [1], [2] in executive_summary and key_insights where facts align with sources.\n"
        )

        response = await genai_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ResearchResponseLLM,
            ),
        )

        parsed_data = json.loads(response.text)

        formatted_insights = []
        for insight in parsed_data.get("key_insights", []):
            citation_count = insight["summary"].count("[")
            score = calculate_impact_score(
                sources, insight["summary"], citation_count
            )
            formatted_insights.append(
                {
                    "title": insight["title"],
                    "summary": insight["summary"],
                    "impact_score": score,
                }
            )

        final_response = {
            "executive_summary": parsed_data.get("executive_summary", ""),
            "key_insights": formatted_insights,
            "market_signals": parsed_data.get("market_signals", []),
            "recommended_actions": parsed_data.get("recommended_actions", []),
            "sources": sources,
            "cached": False,
        }

        # --------------------------------------------------
        # CACHE WRITE: Store in Upstash Redis
        # --------------------------------------------------
        try:
            await redis_client.set(
                cache_key, json.dumps(final_response), ex=CACHE_TTL
            )
            print(f"✅ [CACHE WRITE] Cached '{cache_key}' for {CACHE_TTL}s")
        except Exception as e:
            print(f"⚠️ Redis write warning: {e}")

        return final_response

    except Exception as e:
        print(f"Error analyzing topic: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process research request: {str(e)}",
        )