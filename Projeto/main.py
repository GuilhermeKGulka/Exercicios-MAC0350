from fastapi import FastAPI, Request, Depends, HTTPException, status, Cookie, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
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

# ~~~~~~~~~~~~~~~~~~~~~ DEPENDENCIAS ~~~~~~~~~~~~~~~~~~~~~

async def get_current_user(request: Request) -> Optional[str]:
    username = request.cookies.get("session_username")
    logger.debug(f"Cookie session_username: {username}")
    return request.cookies.get("session_username")

async def require_logged_out(request: Request):
    username = await get_current_user(request)
    
    if username:
        logger.info(f"Usuário {username} tentou acessar rota protegida - REDIRECIONANDO")
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/"}
        )
    
    return None

# ~~~~~~~~~~~~~~~~~~~~~~~ ROTAS ~~~~~~~~~~~~~~~~~~~~~~~~~~

@app.get("/")
def pagina_inicial(request: Request):
    return templates.TemplateResponse(
        request=request, name="Home.html", context={"username": request.cookies.get("session_username")}
    )

@app.get("/register")
def pagina_cadastro(request: Request, _: None = Depends(require_logged_out)):
    return templates.TemplateResponse(
        request=request, name="Register.html", context={"username": request.cookies.get("session_username")}
    )

@app.post("/createuser")
def criar_usuario(usuario: User):
    if usuario.name is None:
        usuario.name = usuario.username
    usuarios_db.append(usuario.dict())
    return {"username": usuario.username}

@app.post("/login")
async def login(loginRequest: LoginRequest, response: Response):
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
    
    response = RedirectResponse(url="/", status_code=303)

    response.set_cookie(
        key="session_username", 
        value=loginRequest.username
    )

    return response

@app.post("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_username")

    return response