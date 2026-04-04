from fastapi import FastAPI, Request, Depends, HTTPException, status, Response, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Annotated, Optional
import logging, random, datetime, re
from sqlmodel import Session, select, col
from sqlalchemy import func
from models import engine, get_session, create_db_and_tables
from models import Usuario, Animal, Favorito  # ← SQLModel models
from models import UsuarioAuth
from utils.img_api import api_img_search

app = FastAPI()

# Criar tabelas ao iniciar
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    logger.info("✅ Banco de dados inicializado")

# Monta a pasta "static" na rota "/static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Sintaxe recomendada: diretório como primeiro argumento posicional
templates = Jinja2Templates(directory="templates")

# Configuração básica de log para aparecer no terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

# ========== FUNCOES ==========

def aplicar_filtros_busca_animais(statement, q: str):
    if not q:
        return statement
    
    termos = q.split()
    for termo in termos:
        if ":" in termo:
            remover = termo.startswith("-")
            limpo = termo[1:] if remover else termo
            campo, valor = limpo.split(":", 1)
            
            # Mapeia o campo digitado para o atributo do modelo
            attr = getattr(Animal, campo.lower(), None)
            if attr:
                if remover:
                    statement = statement.where(col(attr) != valor)
                else:
                    statement = statement.where(col(attr) == valor)
        else:
            # Busca textual simples nos nomes
            statement = statement.where(
                col(Animal.nome_popular).contains(termo)
            )
    return statement

# ========== DEPENDÊNCIAS ==========

async def get_current_user(request: Request, session: Session = Depends(get_session)) -> Optional[dict]:
    """Obtém usuário atual do cookie"""
    username = request.cookies.get("session_username")
    logger.debug(f"Cookie session_username: {username}")
    
    if username:
        statement = select(Usuario).where(Usuario.username == username)
        usuario = session.exec(statement).first()
        return usuario
    
    return None

async def require_logged_out(request: Request, current_user: Optional[Usuario] = Depends(get_current_user)):
    """Redireciona se usuário estiver logado"""
    if current_user:
        logger.info(f"Usuário {current_user.username} tentou acessar rota protegida - REDIRECIONANDO")
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/"}
        )
    return None

async def require_logged_in(current_user: Optional[Usuario] = Depends(get_current_user)) -> Usuario:
    """Exige que usuário esteja logado"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/"}
        )
    return current_user

# ========== ROTAS ==========

@app.get("/")
async def pagina_raiz(request: Request, current_user: Optional[Usuario] = Depends(get_current_user),session: Session = Depends(get_session)):
    context={
        "curr_user": current_user if current_user else None,
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="Home.html", 
            context=context
        )
    return templates.TemplateResponse(
        request=request,
        name="Layout.html",
        context={**context, "pagina":"/home"}
    )

@app.get("/home")
async def pagina_inicial(request: Request, current_user: Optional[Usuario] = Depends(get_current_user), session: Session = Depends(get_session)):
    animais = session.exec(select(Animal)).all()
    animal_do_dia = None

    if animais:
        hoje = datetime.date.today().strftime("%Y-%m-%d")
        random.seed(hoje)

        for _ in range(15):
            candidato = random.choice(animais)
            if await api_img_search(candidato, session):
                animal_do_dia = candidato
                break
        
    context = {
        "curr_user": current_user if current_user else None,
        "animal": animal_do_dia,
    }
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="Home.html",
            context=context
        )
    return templates.TemplateResponse(
        request=request,
        name="Layout.html",
        context={**context, "pagina":"/home"}
    )

@app.get("/login")
async def pagina_login(request: Request, _: None = Depends(require_logged_out)):
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="Login.html",
        )
    return templates.TemplateResponse(
        request=request,
        name="Layout.html",
        context={"pagina":"/login"}
    )

@app.get("/register")
async def pagina_cadastro(request: Request, _: None = Depends(require_logged_out)):
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="Register.html",
        )
    return templates.TemplateResponse(
        request=request,
        name="Layout.html",
        context={"pagina":"/register"}
    )

@app.post("/createuser")
async def cadastro(registerRequest: UsuarioAuth, session: Session = Depends(get_session)):
    #Checa se usuario existe
    statement = select(Usuario).where(Usuario.username == registerRequest.username)
    existing = session.exec(statement).first()
    
    if existing:
        return JSONResponse(
            status_code=400,
            content={"error": "Usuário já existe"}
        )

    novo_usuario = Usuario(
        username=registerRequest.username,
        name=registerRequest.name,
        password=registerRequest.password
    )
    
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    
    response = RedirectResponse(url="/login", status_code=303)
    return response

@app.post("/attemptLogin")
async def login(loginRequest: UsuarioAuth, response: Response = None, session: Session = Depends(get_session)):
    # Buscar usuário no banco
    statement = select(Usuario).where(Usuario.username == loginRequest.username)
    usuario = session.exec(statement).first()
    
    if not usuario:
        return JSONResponse(
            status_code=401,
            content={"error": "Usuário não encontrado"}
        )
    
    if usuario.password != loginRequest.password:
        return JSONResponse(
            status_code=401,
            content={"error": "Senha incorreta"}
        )
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_username",
        value=loginRequest.username,
        path="/"
    )

    return response

@app.post("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_username", path="/")
    return response

@app.get("/animais")
async def pagina_animais(request: Request, current_user: Optional[Usuario] = Depends(get_current_user)):
    context = {
        "request": request,
        "curr_user": current_user if current_user else None
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="Animais.html",
            context=context
        )
    return templates.TemplateResponse(
        request=request,
        name="Layout.html",
        context={**context, "pagina":"/animais"}
    )

@app.get("/animal/{id}")
async def pagina_animal(request: Request, id: int, current_user: Optional[Usuario] = Depends(get_current_user), session: Session = Depends(get_session)):
    if id == 0:
        id = session.exec(select(Animal.id).order_by(func.random()).limit(1)).first()
    
    animal = session.get(Animal, id)
    
    context = {
        "request": request,
        "curr_user": current_user if current_user else None,
        "id": id,
        "animal": animal
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="Animal.html",
            context=context
        )
    return templates.TemplateResponse(
        request=request,
        name="Layout.html",
        context={**context, "pagina":f"/animal/{id}"}
    )

@app.get("/usuarios")
async def pagina_usuarios(request: Request, current_user: Optional[Usuario] = Depends(get_current_user)):
    context = {
        "request": request,
        "curr_user": current_user if current_user else None
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="Usuarios.html",
            context=context
        )
    return templates.TemplateResponse(
        request=request,
        name="Layout.html",
        context={**context, "pagina":"/usuarios"}
    )

@app.get("/profile/{id}")
async def pagina_usuario(request: Request, id: int, current_user: Optional[Usuario] = Depends(get_current_user), session: Session = Depends(get_session)):
    user = session.get(Usuario, id)
    
    context = {
        "request": request,
        "curr_user": current_user if current_user else None,
        "id": id,
        "user": user
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="Profile.html",
            context=context
        )
    return templates.TemplateResponse(
        request=request,
        name="Layout.html",
        context={**context, "pagina":f"/profile/{id}"}
    )

@app.put("/api/atualizarNome", response_class=HTMLResponse)
def atualizar_aluno(change_name: Optional[str] = Form(...), curr_user: Optional[Usuario] = Depends(get_current_user), session: Session = Depends(get_session)):
    curr_user.name = change_name
    session.commit()
    session.refresh(curr_user)
    
    return HTMLResponse(content=f'''
        <h2 id="name" hx-swap-oob="true">{curr_user.name}</h2>
        
        <div id="alerta-temp" hx-swap-oob="true" class="alert-simples">
            "Seu nome foi atualizado!"
            <script>
                setTimeout(() => {{
                    const alerta = document.getElementById("alerta-temp");
                    if (alerta) alerta.classList.add("hidden");
                }}, 3000);
            </script>
        </div>
    ''')

@app.put("/api/atualizarFoto", response_class=HTMLResponse)
def atualizar_aluno(change_img_url: Optional[str] = Form(...), curr_user: Optional[Usuario] = Depends(get_current_user), session: Session = Depends(get_session)):
    curr_user.profile_img_url = change_img_url
    session.commit()
    session.refresh(curr_user)
    
    return HTMLResponse(content=f'''
        <img id="profile-img" src="{curr_user.profile_img_url} hx-swap-oob="true">
        
        <div id="alerta-temp" hx-swap-oob="true" class="alert-simples">
            "Foto de perfil atualizada!"
            <script>
                setTimeout(() => {{
                    const alerta = document.getElementById("alerta-temp");
                    if (alerta) alerta.classList.add("hidden");
                }}, 3000);
            </script>
        </div>
    ''')

@app.put("/api/favoritar/{id}")
async def favoritar_animal(id: int, session: Session = Depends(get_session), curr_user: Usuario = Depends(get_current_user)):
    # Busca se existe o favorito
    statement = select(Favorito).where(
        Favorito.usuario_id == curr_user.id, 
        Favorito.animal_id == id
    )
    favorito_existente = session.exec(statement).first()

    if favorito_existente:
        # REMOVE: Se existe, deletamos
        session.delete(favorito_existente)
        session.commit()
        foi_adicionado = False
        mensagem = "Removido dos favoritos"
    else:
        # ADD: Se não existe, criamos
        novo_favorito = Favorito(usuario_id=curr_user.id, animal_id=id)
        session.add(novo_favorito)
        session.commit()
        foi_adicionado = True
        mensagem = "Adicionado aos favoritos!"

    # Retorna HTML do coração e o alerta (OOB)
    # A classe 'active' define a cor vermelha no CSS
    active_class = "active" if foi_adicionado else ""
    
    return HTMLResponse(content=f'''
        <div class="heart {active_class}"></div>
        
        <div id="alerta-temp" hx-swap-oob="true" class="alert-simples">
            {mensagem}
            <script>
                setTimeout(() => {{
                    const alerta = document.getElementById("alerta-temp");
                    if (alerta) alerta.classList.add("hidden");
                }}, 3000);
            </script>
        </div>
    ''')

@app.get("/api/animais")
async def api_animais_scroll(request: Request, page: int = 1, q: str = "", session: Session = Depends(get_session)):
    limit = 20
    offset = (page - 1) * limit
    
    statement = select(Animal)
    statement = aplicar_filtros_busca_animais(statement, q)
    
    animais = session.exec(statement.offset(offset).limit(limit)).all()
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request, 
            name="partials/grid_animais.html", 
            context={"animais": animais, "page": page, "q": q}
        )
    return RedirectResponse(url="/animais", status_code=303)

@app.get("/api/animal/{id}/img")
async def get_animal_img(request: Request, id: int, current_user: Optional[Usuario] = Depends(get_current_user), session: Session = Depends(get_session)):
    animal = session.get(Animal, id)
    img_info = await api_img_search(animal, session)

    favoritado = False
    if current_user:
        statement = select(Favorito).where(
            Favorito.usuario_id == current_user.id, 
            Favorito.animal_id == id
        )
        if session.exec(statement).first():
            favoritado = True

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request, 
            name="partials/img_animal.html", 
            context={**img_info, "id": id, "favoritado": favoritado} if img_info else {"id": id, "favoritado": favoritado}
        )
    return RedirectResponse(url=f"/animal/{id}", status_code=303)
    
@app.get("/api/sugestoes")
async def api_sugestoes(request: Request, q: str = "", session: Session = Depends(get_session)):
    if not q : 
        return Response("") 
    
    filtros = q.split()
    termo = filtros[-1].lower() #filtro ainda em escrita, ex: -filo:cho

    remover = termo.startswith("-")
    termo_limpo = termo[1:] if remover else termo #remove o '-' se houver, ex: filo:cho
    
    sugestoes = []
    campos = ["filo:", "classe:", "ordem:", "familia:", "genero:", "nome_popular:", "nome_cientifico:"]

    # CASO 1: Usuario digitou o campo e quer o valor (ex: "filo:cho")
    if ":" in termo_limpo:
        campo, valor_parcial = termo_limpo.split(":", 1) # campo <- "filo" ; valor <- "cho"
        attr = getattr(Animal, campo, None)
        
        if attr:
            # Busca no banco valores únicos que começam com o que foi digitado
            query = select(attr).distinct().where(col(attr).startswith(valor_parcial)).limit(10)
            resultados = session.exec(query).all()
            for res in resultados:
                sugestoes.append(f"{'-' if remover else ''}{campo}:{res}")

    # CASO 2: Usuario ainda digitando o campo (ex: "fil")
    else:
        for p in campos:
            if p.startswith(termo_limpo):
                sugestoes.append(f"{'-' if remover else ''}{p}")

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request, 
            name="partials/sugestoes_list.html", 
            context={"sugestoes": sugestoes}
        )
    return RedirectResponse(url="/animais", status_code=303)

@app.get("/api/usuarios")
async def api_usuarios_scroll(request: Request, page: int = 1, q: str = "", session: Session = Depends(get_session)):
    limit = 20
    offset = (page - 1) * limit
    
    statement = select(Usuario).where(col(Usuario.name).contains(q))
    
    usuarios = session.exec(statement.offset(offset).limit(limit)).all()
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request, 
            name="partials/grid_usuarios.html", 
            context={"usuarios": usuarios, "page": page, "q": q}
        )
    return RedirectResponse(url="/usuarios", status_code=303)

@app.get("/api/usuarios/{id}/favoritos")
async def api_usuarios_scroll(id: int, request: Request, page: int = 1, session: Session = Depends(get_session)):
    limit = 20
    offset = (page - 1) * limit
    
    statement = select(Animal).join(Favorito).where(Favorito.usuario_id == id)
    animais_favoritos = session.exec(statement.offset(offset).limit(limit)).all()
    
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request, 
            name="partials/grid_animais_favoritos.html", 
            context={"favoritos": animais_favoritos, "page": page, "id": id}
        )
    return RedirectResponse(url=f"/profile/{id}", status_code=303)


