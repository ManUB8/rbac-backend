from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "https://rbac-activity.com",
    "https://www.rbac-activity.com",
    "https://rbac-front.pages.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "RBAC API running....."}

@app.get("/health")
def health():
    return {"status": "ok"}