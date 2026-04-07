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

# Configuração básica de log para aparecer no terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

class Usuario(BaseModel):
    nome: str
    senha: str
    bio: str

class UsuarioAuth(BaseModel):
    nome: str
    senha: str

# Nossa base de dados em memória
users_db = [
    {"username": "joão", "bio": "Professor de Python"},
    {"username": "maria", "bio": "Desenvolvedora Web"},
]

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 1. Código executado ANTES da rota
    start_time = time.perf_counter()
    
    # 2. A requisição viaja até a rota e volta como resposta
    response = await call_next(request)
    
    # 3. Código executado DEPOIS da rota
    process_time = time.perf_counter() - start_time
    
    # Adicionamos um header customizado na resposta para o cliente ver
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(f"Rota: {request.url.path} | Tempo: {process_time:.4f}s")
    
    return response

@app.get("/")
def loginform(request: Request):
    return templates.TemplateResponse(
        request=request, name="form.html"
    )

@app.post("/users")
def criar_usuario(user: Usuario):
    users_db.append(user.dict())
    return {"usuario": user.nome}

@app.get("/login")
def loginform(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html"
    )

@app.post("/loginn")
def login(user: UsuarioAuth, response: Response):
    usuario_encontrado = None
    for u in users_db:
        if u["username"] == user.nome:
            usuario_encontrado = u
            break
    
    if not usuario_encontrado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user.senha != usuario_encontrado.senha:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    
    response.set_cookie(key="session_user", value=username)
    return {"message": "Logado com sucesso"}

def get_active_user(session_user: Annotated[str | None, Cookie()] = None):
    if not session_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso negado: você não está logado."
        )
    
    user = next((u for u in users_db if u["username"] == session_user), None)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão inválida")
    
    return user

@app.get("/home")
def show_profile(request: Request, user: dict = Depends(get_active_user)):
    return templates.TemplateResponse(
        request=request, 
        name="profile.html", 
        context={"user": user}
    )
    