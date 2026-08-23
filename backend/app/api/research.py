import json
import os
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List

from fastapi import APIRouter, HTTPException
from google import genai
from google.genai import types
import httpx
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/research", tags=["research"])

# Global client reuse for efficiency
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# --- 1. PYDANTIC SCHEMAS ---
class ResearchRequest(BaseModel):
    topic: str
    depth: str = "standard"


class Insight(BaseModel):
    title: str = Field(description="Title of the research insight")
    summary: str = Field(
        description="Detailed summary of the insight with inline citations like [1]"
    )
    impact_score: int = Field(
        description="Impact score rating from 1 to 10", ge=1, le=10
    )


class ResearchResponse(BaseModel):
    executive_summary: str = Field(
        description="Overall summary of the research topic with inline citations"
    )
    key_insights: List[Insight]
    market_signals: List[str] = Field(
        description="Key market trends or signals extracted from research"
    )
    recommended_actions: List[str] = Field(
        description="Actionable steps or takeaways"
    )


class Source(BaseModel):
    title: str
    snippet: str
    url: str
    date: str


# --- 2. ASYNC ARXIV FETCHER ---
async def fetch_arxiv_sources(topic: str, max_results: int = 5) -> List[dict]:
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
                url = id_elem.text.strip() if id_elem is not None else ""

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


# --- 3. ENDPOINT ---
@router.post("/")
async def analyze_topic(req: ResearchRequest):
    try:
        # Step 1: Async retrieval from arXiv
        sources = await fetch_arxiv_sources(req.topic)

        # Step 2: Build context
        context_str = "\n".join(
            [
                f"[{i+1}] Title: {s['title']}\nSnippet: {s['snippet']}\nURL: {s['url']}\n"
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

        # Step 3: Call Gemini with structured response schema
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ResearchResponse,
            ),
        )

        parsed_data = json.loads(response.text)

        # Step 4: Combine LLM output with fetched sources
        parsed_data["sources"] = sources

        return parsed_data

    except Exception as e:
        print(f"Error analyzing topic: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process research request: {str(e)}"
        )