"""
main.py — a mesma API de eventos, agora com upload de cartaz.

Laboratório da Aula 08 — IBM4028, Projeto em Ciência de Dados IV.

O que mudou em relação à Aula 06:

    - uma rota nova, POST /eventos/{id}/cartaz
    - a validação do arquivo, antes de qualquer coisa sair da máquina
    - a URL do blob gravada na coluna cartaz_url

O que NÃO mudou: nenhuma das rotas antigas. Quem já consumia a API
continua funcionando sem saber que existe cartaz.

Para rodar:
    fastapi dev main.py
"""

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import storage
from database import Base, engine, get_db
from schemas import EventoCreate, EventoResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Eventos do Campus",
    description="Laboratório da Aula 08 — agora com upload de arquivos",
    version="3.0.0",
)

ORIGENS_PERMITIDAS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://salmon-cliff-0be62d50f.5.azurestaticapps.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Content-type aceito -> extensão que o blob vai receber.
#
# Trabalhar com uma lista do que É aceito (allow list) e não do que é
# proibido: lista de proibidos sempre tem um item que você esqueceu.
EXTENSAO_POR_TIPO = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

TAMANHO_MAXIMO_BYTES = 2 * 1024 * 1024  # 2 MB


@app.get("/")
async def raiz():
    return {"mensagem": "API de Eventos do Campus", "docs": "/docs"}


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    total = db.query(models.Evento).count()
    return {"status": "ok", "banco": "conectado", "eventos_cadastrados": total}


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
    Recebe a imagem, grava no Blob Storage e guarda a URL no evento.

    A ordem das verificações não é acidental. Cada uma delas é mais barata
    que a seguinte, e a mais cara de todas — mandar bytes pela rede — só
    acontece depois que tudo o mais passou:

        1. o evento existe?
        2. o tipo do arquivo é aceito?
        3. o tamanho cabe?
        4. só então o upload

    Repare que a rota devolve o evento inteiro, não a URL solta. Assim o
    cliente recebe o estado atualizado do recurso em uma resposta só.
    """
    evento = db.query(models.Evento).filter(models.Evento.id == evento_id).first()

    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evento {evento_id} não encontrado",
        )

    # 415 Unsupported Media Type é o status certo aqui: o pedido está bem
    # formado, o tipo do conteúdo é que não serve.
    if arquivo.content_type not in EXTENSAO_POR_TIPO:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Tipo {arquivo.content_type!r} não aceito. "
                f"Envie um dos seguintes: {', '.join(EXTENSAO_POR_TIPO)}"
            ),
        )

    conteudo = await arquivo.read()

    if len(conteudo) > TAMANHO_MAXIMO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo com {len(conteudo)} bytes; o limite é {TAMANHO_MAXIMO_BYTES}.",
        )

    url = storage.enviar_arquivo(
        nome_do_blob=storage.nome_do_cartaz(evento_id, EXTENSAO_POR_TIPO[arquivo.content_type]),
        conteudo=conteudo,
        content_type=arquivo.content_type,
    )

    # O blob já está gravado. Se este commit falhar, sobra um blob que
    # ninguém referencia — o "blob órfão" que discutimos na Aula 07.
    # Resolver isso de verdade exige uma rotina de limpeza; aqui ficamos
    # com o problema à vista, de propósito.
    evento.cartaz_url = url
    db.commit()
    db.refresh(evento)

    return evento


@app.delete("/eventos/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_evento(evento_id: int, db: Session = Depends(get_db)):
    """
    Apaga o evento — e deixa o blob para trás.

    É o mesmo problema do órfão, pelo outro lado: o registro some e o
    arquivo continua ocupando espaço (e sendo cobrado) para sempre. Vale
    perguntar em aula: apagar o blob aqui resolveria? E se o DELETE falhar
    depois de o blob já ter sido apagado?
    """
    evento = db.query(models.Evento).filter(models.Evento.id == evento_id).first()

    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evento {evento_id} não encontrado",
        )

    db.delete(evento)
    db.commit()