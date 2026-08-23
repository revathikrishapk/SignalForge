import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

router = APIRouter(prefix="/api/research", tags=["research"])

class ResearchRequest(BaseModel):
    topic: str
    depth: str = "standard"

def fetch_arxiv_sources(topic: str, max_results: int = 5):
    query_url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(topic)}&max_results={max_results}"
    try:
        req = urllib.request.Request(query_url, headers={'User-Agent': 'SignalForge/1.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        
        sources = []
        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', namespace).text.strip().replace('\n', ' ')
            published = entry.find('atom:published', namespace).text[:10]
            url = entry.find('atom:id', namespace).text.strip()
            
            sources.append({
                "title": title,
                "snippet": summary[:250] + "...",
                "url": url,
                "date": published
            })
        return sources
    except Exception as e:
        print(f"arXiv Fetch Error: {e}")
        return []

@router.post("/")
async def analyze_topic(req: ResearchRequest):
    try:
        # 1. Retrieve sources from arXiv
        sources = fetch_arxiv_sources(req.topic)
        
        # 2. Format grounding context
        context_str = "\n".join([
            f"[{i+1}] Title: {s['title']}\nSnippet: {s['snippet']}\nURL: {s['url']}\n"
            for i, s in enumerate(sources)
        ])
        
        # Plain string avoids all f-string escaping crashes
        prompt = (
            "Synthesize the research topic using ONLY the provided sources where relevant.\n"
            f"Topic: {req.topic}\n\n"
            "Retrieved Sources:\n"
            f"{context_str if context_str else 'No academic papers found. Synthesize based on domain knowledge.'}\n\n"
            "Instructions:\n"
            "- Include inline citations like [1], [2] in executive_summary and key_insights where facts align with sources.\n"
            "- Return valid JSON matching this schema:\n"
            "{\n"
            '  "executive_summary": "Summary string with citations [1]",\n'
            '  "key_insights": [{"title": "Title", "summary": "Detailed summary with citations [1]", "impact_score": 8}],\n'
            '  "market_signals": ["Signal string [2]"],\n'
            '  "recommended_actions": ["Action string"]\n'
            "}"
        )
        
        # 3. Call Gemini using modern SDK client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        parsed = json.loads(response.text)
        # 4. Attach sources array to payload
        parsed["sources"] = sources
        
        return parsed
    except Exception as e:
        print(f"Error analyzing topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))