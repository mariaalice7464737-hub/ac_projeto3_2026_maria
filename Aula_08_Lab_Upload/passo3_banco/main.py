"""
Passo 3 — o blob e o banco, ligados.

A rota nova recebe o arquivo, manda para o Blob Storage e grava a URL na
coluna `cartaz_url` do evento.

Ainda SEM validação: qualquer arquivo, de qualquer tamanho, é aceito.
Isso é de propósito — vale ver a API funcionando primeiro e depois
descobrir, testando, o que ela aceita que não deveria. A validação entra
no passo 4.

Se você já tinha um eventos.db da Aula 06, apague-o: o `create_all` cria
tabelas que não existem, mas não acrescenta coluna em tabela já criada.

Para rodar:
    fastapi dev main.py
"""

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import models
import storage
from database import Base, engine, get_db
from schemas import EventoCreate, EventoResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Passo 3 — blob + banco", version="3.0.0")


@app.get("/eventos", response_model=list[EventoResponse])
async def listar_eventos(db: Session = Depends(get_db)):
    return db.query(models.Evento).all()


@app.post(
    "/eventos",
    response_model=EventoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_evento(evento: EventoCreate, db: Session = Depends(get_db)):
    novo = models.Evento(**evento.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@app.get("/eventos/{evento_id}", response_model=EventoResponse)
async def buscar_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(models.Evento).filter(models.Evento.id == evento_id).first()

    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evento {evento_id} não encontrado",
        )

    return evento


@app.post("/eventos/{evento_id}/cartaz", response_model=EventoResponse)
async def enviar_cartaz(
    evento_id: int,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Três movimentos: confere o evento, envia o blob, guarda a URL.

    A extensão sai do nome que o cliente mandou. Isso funciona nos testes
    e é exatamente o tipo de confiança que o passo 4 vai tirar do código.
    """
    evento = db.query(models.Evento).filter(models.Evento.id == evento_id).first()

    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evento {evento_id} não encontrado",
        )

    conteudo = await arquivo.read()
    extensao = "." + (arquivo.filename or "arquivo.bin").rsplit(".", 1)[-1]

    url = storage.enviar_arquivo(
        nome_do_blob=storage.nome_do_cartaz(evento_id, extensao),
        conteudo=conteudo,
        content_type=arquivo.content_type or "application/octet-stream",
    )

    evento.cartaz_url = url
    db.commit()
    db.refresh(evento)

    return evento
