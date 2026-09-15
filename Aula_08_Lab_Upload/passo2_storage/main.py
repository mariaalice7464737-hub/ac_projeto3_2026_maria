"""
Passo 2 — o arquivo sai da sua máquina e vai para o Blob Storage.

Ainda sem banco de dados: o objetivo aqui é ver a URL aparecer e conseguir
abrir o blob no portal do Azure. Persistir essa URL é o passo 3.

Antes de rodar, crie o arquivo .env ao lado deste, com:

    AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
    AZURE_STORAGE_CONTAINER=cartazes

Para rodar:
    fastapi dev main.py
"""

from fastapi import FastAPI, File, UploadFile

import storage

app = FastAPI(title="Passo 2 — enviando para o Blob Storage")


@app.post("/upload-teste")
async def upload_teste(arquivo: UploadFile = File(...)):
    conteudo = await arquivo.read()

    # Nome fixo só para este passo. No passo 3 ele passa a vir do id do
    # evento — nome de blob previsível é o que permite achar o arquivo
    # depois sem consultar o banco.
    url = storage.enviar_arquivo(
        nome_do_blob=f"teste/{arquivo.filename}",
        conteudo=conteudo,
        content_type=arquivo.content_type or "application/octet-stream",
    )

    return {"url": url, "tamanho_bytes": len(conteudo)}
