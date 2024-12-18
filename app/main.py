from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import users,job_post,application

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(job_post.router, prefix="/api/job_post", tags=["job_post"])
app.include_router(application.router, prefix="/api/application", tags=["application"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the DIHADI's API!"}
