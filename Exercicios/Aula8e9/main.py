from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models import Aluno
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, create_engine, Session, select, col

@asynccontextmanager
async def initFunction(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=initFunction)

arquivo_sqlite = "HTMX2.db"
url_sqlite = f"sqlite:///{arquivo_sqlite}"

engine = create_engine(url_sqlite)

templates = Jinja2Templates(directory=["Templates", "Templates/Partials"])

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
@app.get("/busca", response_class=HTMLResponse)
def busca(request: Request):
    return templates.TemplateResponse(request, "index.html")

def buscar_alunos(busca: str, pagina: int = 1, lim: int = 10):
    with Session(engine) as session:
        query = (select(Aluno).where(col(Aluno.nome).contains(busca)).order_by(Aluno.nome).offset((pagina - 1) * lim).limit(lim))
        return session.exec(query).all()
    
@app.get("/lista", response_class=HTMLResponse)
def lista(request: Request, busca: str | None = '', pagina: int = 1):
    lim = 10
    alunos = buscar_alunos(busca, pagina, lim)
    return templates.TemplateResponse(request, "lista.html", {"alunos": alunos,"pagina": pagina,"busca": busca})
    
@app.get("/editarAlunos")
def novoAluno(request: Request):
    return templates.TemplateResponse(request, "options.html")

@app.post("/novoAluno", response_class=HTMLResponse)
def criar_aluno(nome: str = Form(...)):
    with Session(engine) as session:
        novo_aluno = Aluno(nome=nome)
        session.add(novo_aluno)
        session.commit()
        session.refresh(novo_aluno)
        return HTMLResponse(content=f"<p>O(a) aluno(a) {novo_aluno.nome} foi registrado(a)!</p>")

@app.put("/atualizaAluno", response_class=HTMLResponse)
def atualizar_aluno(id: int = Form(...), novoNome: str = Form(...)):
    with Session(engine) as session:
        query = select(Aluno).where(Aluno.id == id)
        aluno = session.exec(query).first()
        if (not aluno):
            raise HTTPException(404, "Aluno não encontrado")
        nomeAntigo = aluno.nome
        aluno.nome = novoNome
        session.commit()
        session.refresh(aluno)
        return HTMLResponse(content=f"<p>O(a) aluno(a) {nomeAntigo} foi atualizado(a) para {aluno.nome}!</p>")

