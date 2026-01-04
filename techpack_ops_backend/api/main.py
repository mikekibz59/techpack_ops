from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Techpack Ops API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000", "http://localhost:5179"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def health_check():
    return {"status": "healthy"}

