import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# --- Configuration ---
# IMPORTANT: Replace the database URL below with your actual connection string.
# Example: postgresql+psycopg2://user:password@localhost:5432/policy_db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db") 

# --- Database Setup ---
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SQLAlchemy Model ---
class Policy(Base):
    __tablename__ = "policies"
    
    # Primary Key - Policy ID
    id = Column(Integer, primary_key=True, index=True)
    # Policy Fields
    app_name = Column(String, index=True, nullable=False)
    protocol = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    action = Column(String, nullable=False) # e.g., ALLOW, DENY, LOG

# Create all tables (only runs if using SQLite or if tables don't exist)
Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---

class PolicyBase(BaseModel):
    app_name: str = Field(..., example="Google Chrome")
    protocol: str = Field(..., example="TCP")
    port: int = Field(..., example=443)
    action: str = Field(..., example="ALLOW")

class PolicyCreate(PolicyBase):
    pass # Same as base for simplicity

class PolicyUpdate(PolicyBase):
    app_name: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    action: Optional[str] = None

class PolicyRead(PolicyBase):
    id: int

    class Config:
        orm_mode = True

# --- FastAPI App Initialization ---
app = FastAPI(title="Policy Management API", version="1.0.0")

# Basic CORS setup to allow the React dashboard to connect during development
from fastapi.middleware.cors import CORSMiddleware

# ✅ Allow all frontend development ports (Vite sometimes switches ports)
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# --- RESTful Endpoints (CRUD) ---

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Policy Management API is running"}

@app.post("/api/v1/policies/", response_model=PolicyRead, status_code=201, tags=["Policies"])
def create_policy(policy: PolicyCreate, db: Session = Depends(get_db)):
    """Create a new policy record."""
    db_policy = Policy(**policy.dict())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy

@app.get("/api/v1/policies/", response_model=List[PolicyRead], tags=["Policies"])
def list_policies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve a list of all policies."""
    policies = db.query(Policy).offset(skip).limit(limit).all()
    return policies

@app.get("/api/v1/policies/{policy_id}", response_model=PolicyRead, tags=["Policies"])
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    """Retrieve a single policy by ID."""
    db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if db_policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return db_policy

@app.put("/api/v1/policies/{policy_id}", response_model=PolicyRead, tags=["Policies"])
def update_policy(policy_id: int, policy: PolicyUpdate, db: Session = Depends(get_db)):
    """Update an existing policy."""
    db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if db_policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    update_data = policy.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_policy, key, value)
        
    db.commit()
    db.refresh(db_policy)
    return db_policy

@app.delete("/api/v1/policies/{policy_id}", status_code=204, tags=["Policies"])
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    """Delete a policy by ID."""
    db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if db_policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    db.delete(db_policy)
    db.commit()
    return {"ok": True}

@app.get("/api/v1/policies/sync", response_model=List[PolicyRead], tags=["Endpoints"])
def sync_policies(db: Session = Depends(get_db)):
    """Endpoint used by endpoint agents to retrieve the current full policy list."""
    return db.query(Policy).all()

# Example startup event to add default data if using SQLite
@app.on_event("startup")
def add_initial_data():
    if DATABASE_URL.startswith("sqlite:///./test.db"):
        db = SessionLocal()
        if db.query(Policy).count() == 0:
            print("Adding initial policies to database...")
            initial_policies = [
                Policy(app_name="Google Chrome", protocol="TCP", port=443, action="ALLOW"),
                Policy(app_name="Git Client", protocol="TCP", port=22, action="ALLOW"),
                Policy(app_name="Unknown Process", protocol="UDP", port=5353, action="DENY"),
            ]
            db.add_all(initial_policies)
            db.commit()
        db.close()