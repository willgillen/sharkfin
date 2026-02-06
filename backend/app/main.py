import logging
import sys

# Configure logging FIRST, before any other imports
# This ensures all loggers created during import get the correct configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,  # Explicitly use stdout
    force=True  # Force reconfiguration even if already configured
)

# Set specific loggers to DEBUG for import/payee debugging
logging.getLogger('app.services.payee_service').setLevel(logging.DEBUG)
logging.getLogger('app.api.v1.imports').setLevel(logging.DEBUG)

# Now import everything else
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, users, accounts, categories, transactions, budgets, reports, imports, rules, payees, settings, setup

app = FastAPI(
    title="Shark Fin API",
    description="Open-source financial planning and budgeting API",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routers
# Setup router - public, no auth required (only works when no users exist)
app.include_router(setup.router, prefix="/api/v1/setup", tags=["setup"])

app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["accounts"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["budgets"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(imports.router, prefix="/api/v1/imports", tags=["imports"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["rules"])
app.include_router(payees.router, prefix="/api/v1/payees", tags=["payees"])
app.include_router(settings.router, prefix="/api/v1", tags=["settings"])

@app.get("/")
async def root():
    return {"message": "Shark Fin API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
