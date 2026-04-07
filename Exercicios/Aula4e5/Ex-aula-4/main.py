from fastapi import FastAPI, Request, Depends, HTTPException, status, Cookie, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Annotated
import time
import logging

app = FastAPI()

# Monta a pasta "static" na rota "/static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Sintaxe recomendada: diretório como primeiro argumento posicional
templates = Jinja2Templates(directory="templates")

users_db = []

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="main.html"
    )

@app.post("/users")
def create_user(user: dict):
    users_db.append(user)
    return user

@app.get("/users")
async def get_users(index: Optional[int] = None):
    if index is not None:
        return users_db[index]
    return users_db

@app.delete("/users")
async def delete_users():
    users_db.clear()
    return {"message": "deletados"}