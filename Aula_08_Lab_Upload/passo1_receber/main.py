"""
Passo 1 — receber o arquivo, sem nuvem nenhuma.

Antes de falar com o Azure, vale entender o que o FastAPI entrega quando
alguém envia um arquivo. Esta versão não guarda nada: ela só olha o que
chegou e devolve a descrição.

Para rodar:
    fastapi dev main.py

Depois abra http://127.0.0.1:8000/docs e use o botão de escolher arquivo
no endpoint POST /upload-teste.
"""

from fastapi import FastAPI, File, UploadFile

app = FastAPI(title="Passo 1 — recebendo arquivos")


@app.post("/upload-teste")
async def upload_teste(arquivo: UploadFile = File(...)):
    """
    `UploadFile` não é uma string com o conteúdo.

    É um objeto que envolve um arquivo temporário: o FastAPI vai gravando
    o que chega em disco em vez de segurar tudo na memória. É por isso que
    `arquivo.read()` é uma corrotina — precisa de `await`.

    Repare também que `filename` e `content_type` vêm do cliente. São
    informação, não garantia: quem está do outro lado escolhe os dois.
    """
    conteudo = await arquivo.read()

    return {
        "nome_original": arquivo.filename,
        "content_type": arquivo.content_type,
        "tamanho_bytes": len(conteudo),
        "tamanho_kb": round(len(conteudo) / 1024, 1),
    }
