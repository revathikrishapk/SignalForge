from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.research import router as research_router

app = FastAPI(title="AI Engineering Lab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(research_router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI Engineering Lab API running"}