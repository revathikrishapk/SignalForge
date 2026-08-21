from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.research import router as research_router
from dotenv import load_dotenv
load_dotenv()
app = FastAPI(title="AI Engineering Lab API")

# Update origins to cover both localhost and 127.0.0.1 on all common dev ports
origins = [
    "http://localhost:3000",
    "https://*.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI Engineering Lab API running"}