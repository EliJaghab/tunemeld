"""Simple FastAPI test to verify Vercel deployment."""

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on Vercel!", "status": "success"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "framework": "FastAPI"}

# Vercel handler
handler = app