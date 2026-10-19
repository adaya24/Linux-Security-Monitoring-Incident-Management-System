from audit_api import router as audit_router
from fastapi import FastAPI
from process_monitor import get_processes
from security_api import router as security_router
from incident_api import router as incident_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title="Linux Security Monitor API",
    description="Process monitoring and security event API for Kali Linux",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)

@app.get("/")
def home():
    return {
        "message": "Linux Security Monitor API is running",
        "status": "online"
    }

@app.get("/processes")
def list_processes():
    return get_processes()


@app.get("/processes/{pid}")
def get_process(pid: int):
    for process in get_processes():
        if process["pid"] == pid:
            return process

    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Process not found")


app.include_router(security_router)
app.include_router(audit_router)
app.include_router(incident_router)
