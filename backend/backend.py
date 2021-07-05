import json

import database
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

DB = database.Database()


@app.get("/get_arb")
async def get_arb_from_redis():
    return DB.grab_json()

@app.get("/get_legit")
async def get_legit_arb():
    return DB.get_legit_arbs()

@app.get("/get_scam")
async def get_legit_arb():
    return DB.get_scam_arbs()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

