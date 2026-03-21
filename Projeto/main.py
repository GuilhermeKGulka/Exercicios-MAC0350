from fastapi import FastAPI, Request, Depends, HTTPException, status, Cookie, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Annotated
import time, datetime, logging

app = FastAPI()

# Monta a pasta "static" na rota "/static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Sintaxe recomendada: diretório como primeiro argumento posicional
templates = Jinja2Templates(directory="templates")

# Configuração básica de log para aparecer no terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

class User(BaseModel):
    username: str
    name: str | None = None
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

usuarios_db = [
    {"username": "jooaa", "name": "Joao", "password" : "2"},
    {"username": "maiia", "password" : "1"},
]

'''@app.middleware("http")
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
    
    return response'''

@app.get("/")
def pagina_inicial(request: Request):
    return templates.TemplateResponse(
        request=request, name="Home.html", context={"username": request.cookies.get("session_username")}
    )

@app.get("/register")
def pagina_cadastro(request: Request):
    return templates.TemplateResponse(
        request=request, name="Register.html"
    )

@app.post("/createuser")
def criar_usuario(usuario: User):
    if usuario.name is None:
        usuario.name = usuario.username
    usuarios_db.append(usuario.dict())
    return {"username": usuario.username}

@app.post("/login")
async def login(loginRequest: LoginRequest, response: Response):
    print("logando")

    usuario_encontrado = None
    for u in usuarios_db:
        if u["username"] == loginRequest.username:
            usuario_encontrado = u
            break

    if not usuario_encontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
        
    if usuario_encontrado["password"] != loginRequest.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta"
        )
    
    response.set_cookie(key="session_username", value=loginRequest.username)
    return {"message": "Logado com sucesso"}