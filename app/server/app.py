from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

# route for sensor data
from app.server.routes.data import router as DataRouter
from app.server.routes.sensors import router as SensorsRouter
from app.server.routes.FixedJobs import router as FixedJobsRouter
from app.server.routes.login import router as LoginRouter
from app.server.routes.userManagement import router as userMRouter


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(DataRouter, tags=["Data"], prefix="/data")
app.include_router(SensorsRouter, tags=["Sensors"], prefix="/sensors")
app.include_router(FixedJobsRouter, tags=["Fixed Jobs"], prefix="/fixedjobs")
app.include_router(LoginRouter, tags=["Login"], prefix="/login")
app.include_router(userMRouter, tags=["UserManagement"], prefix="/usermanagement")

# Mount the static directory
import os
abs_static_file_path = os.path.join(os.path.dirname(__file__), "../static/")
app.mount("/", StaticFiles(directory=abs_static_file_path), name="static")
