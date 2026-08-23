from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.research import router as research_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Engineering Lab API")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://signal-forge-omega-six.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Matches Vercel preview builds
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI Engineering Lab API running"}