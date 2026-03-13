from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, SessionLocal
from models import Base, User
from schemas import UserCreate, UserResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RBAC API",
    description="RBAC Activity Backend API",
    version="1.0.0"
)

origins = [
    "https://rbac-activity.com",
    "https://www.rbac-activity.com",
    "https://rbac-front.pages.dev",
    "https://api.rbac-activity.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "RBAC API running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    db_user = User(
        name=user.name,
        email=user.email,
        password=user.password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()