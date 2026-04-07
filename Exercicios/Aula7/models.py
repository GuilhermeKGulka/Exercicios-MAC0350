from typing import List 
# Este import será importante em algum lugar...
# Dica: Olhe as outras dicas : D


from sqlmodel import Field, Relationship, SQLModel

class Aluno(SQLModel, table=True):
    nusp: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    idade: int
    
    tarefas: List["Tarefa"] = Relationship(back_populates="aluno")

class Tarefa(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str
    duracao: int
    aluno_nusp: int = Field(foreign_key="aluno.nusp")

    aluno: Aluno = Relationship(back_populates="tarefas")
    # Dica numero 2: 
    # "tarefas" deve ser o nome do atributo 
    # que representa a relação no modelo Aluno

