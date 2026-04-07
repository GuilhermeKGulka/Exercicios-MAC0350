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

@app.get("/perfil")
def ver_perfil(request: Request, logado: bool = True):
    user = {"nome": "Rodrigo", "admin": True} if logado else None
    return templates.TemplateResponse(
        request=request, name="perfil.html", context={"user": user}
    )

@app.get("/postagens")
def listar_posts(request: Request):
    db_posts = ["FastAPI com Jinja2", "Arquitetura REST", "HATEOAS na prática"]
    return templates.TemplateResponse(
        request=request, name="blog.html", context={"posts": db_posts}
    )

@app.get("/home")
def listar_posts(request: Request):
    return templates.TemplateResponse(
        request=request, name="form.html"
    )

class Usuario(BaseModel):
    nome: str
    bio: str

@app.post("/usuarios")
def criar_usuario(user: Usuario):
    users_db.append(user.dict())
    print(users_db)
    return {"usuario": user.nome}

# 1. Rota para "Logar" (Define o Cookie)
@app.post("/login")
def login(username: str, response: Response):
    # Buscamos o usuário usando um laço simples
    usuario_encontrado = None
    for u in users_db:
        if u["username"] == username:
            usuario_encontrado = u
            break
    
    if not usuario_encontrado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # O servidor diz ao navegador: "Guarde esse nome no cookie 'session_user'"
    response.set_cookie(key="session_user", value=username)
    return {"message": "Logado com sucesso"}
    
# 2. A Dependência: Lendo o Cookie
def get_active_user(session_user: Annotated[str | None, Cookie()] = None):
    # O FastAPI busca automaticamente um cookie chamado 'session_user'
    if not session_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso negado: você não está logado."
        )
    
    user = next((u for u in users_db if u["username"] == session_user), None)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão inválida")
    
    return user

# 3. Rota Protegida
@app.get("/profile")
def show_profile(request: Request, user: dict = Depends(get_active_user)):
    return templates.TemplateResponse(
        request=request, 
        name="profile.html", 
        context={"username": user["username"], "bio": user["bio"]}
    )
    