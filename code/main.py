from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers.faculty_major_router import router as faculty_major_router
from routers.student_register_router import router as student_register_router
from routers.activity_router import router as activity_router
from routers.user_router import router as user_router
from routers.admin_auth_router import router as admin_auth_router
from routers.student_auth_router import router as student_auth_router
from routers.upload_router import router as upload_router
from routers.student_activity_router import router as student_activity
from routers.admin_dashboard import router as admin_dashboard
from routers.position_router import router as position_router
from service.student_router_v2 import router as student_router_v2

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
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "http://192.168.1.36:5173",
    "http://192.168.1.33:5173",
    "http://192.168.1.34:5173",
    "https://config.rbac-front.pages.dev",
    "https://deve.rbac-front.pages.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(faculty_major_router)
app.include_router(student_register_router)
app.include_router(activity_router)
app.include_router(user_router)
app.include_router(admin_auth_router)
app.include_router(student_auth_router)
app.include_router(upload_router)
app.include_router(student_activity)
app.include_router(admin_dashboard)
app.include_router(position_router)
app.include_router(student_router_v2)



@app.get("/")
def root():
    return {"message": "RBAC API running"}


@app.get("/health")
def health():
    return {"status": "ok"}