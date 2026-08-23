import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

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
        # Step 1: Grounding via arXiv
        sources = fetch_arxiv_sources(req.topic)
        
        context_str = "\n".join([
            f"[{i+1}] Title: {s['title']}\nSnippet: {s['snippet']}\nURL: {s['url']}\n"
            for i, s in enumerate(sources)
        ])
        
        # Step 2: Gemini Synthesis with Grounding Instructions
        prompt = f"""
        Synthesize the research topic using ONLY the provided sources where relevant.
        Topic: {req.topic}
        
        Sources:
        {context_str if context_str else "No academic papers found. Synthesize based on domain knowledge."}
        
        Instructions:
        - Include inline citations like [1], [2] in executive_summary and key_insights where facts align with sources.
        - Return valid JSON matching this schema:
        {{
          "executive_summary": "...",
          "key_insights": [{"title": "...", "summary": "...", "impact_score": 8}],
          "market_signals": ["..."],
          "recommended_actions": ["..."]
        }}
        """
        
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        
        parsed = json.loads(response.text)
        parsed["sources"] = sources  # Pass retrieved sources back to UI
        
        return parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))