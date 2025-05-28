#main.py
from fastapi import FastAPI, Request, Response
from core.database import engine, Base, SessionLocal
from contextlib import asynccontextmanager
from services.root_user import create_root_user
import sys
from routers import auth, user
# Import all models to ensure they're registered with Base
from routers import chat as chat_router
from models.seed import seed_data
from fastapi.middleware.cors import CORSMiddleware
import uvicorn



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables unconditionally
    try:
        Base.metadata.create_all(bind=engine)
        seed_data()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")
        sys.exit(1)
    
    # Initialize root user
    db = SessionLocal()
    try:
        create_root_user(db)
    except Exception as e:
        print(f"Error creating root user: {e}")
    finally:
        db.close()
    yield



app = FastAPI(
    title="Syngenta Doc Processor",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

origins = [
    "http://localhost",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    allow_credentials=True,
    allow_methods=["*"],    # Allows all HTTP methods: GET, POST, PUT, etc.
    allow_headers=["*"],    # Allows all headers
)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the DataCoGlobal API!"}

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(chat_router.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)