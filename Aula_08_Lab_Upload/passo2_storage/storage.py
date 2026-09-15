"""
storage.py — a camada de armazenamento, isolada do resto.

É o mesmo raciocínio do database.py: quem chama não precisa saber que
existe Azure do outro lado. A rota pede "guarda este arquivo e me devolve
a URL" — e é só isso que este módulo expõe.

Se um dia a turma trocar Azure por S3 ou por disco local, só este arquivo
muda. O main.py continua igual.

Este arquivo já está pronto para o passo 3: `nome_do_cartaz` só será usada
lá, quando o blob passar a ser identificado pelo id do evento.
"""

import os

from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

# Lê o arquivo .env e coloca o conteúdo em variáveis de ambiente.
# No Azure não existe .env: as mesmas variáveis vêm das App Settings,
# e este load_dotenv() simplesmente não encontra nada para carregar.
load_dotenv()

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "cartazes")

_service_client: BlobServiceClient | None = None


def _container_client():
    """Cria o cliente na primeira chamada e reaproveita nas seguintes."""
    global _service_client

    if not CONNECTION_STRING:
        raise RuntimeError(
            "AZURE_STORAGE_CONNECTION_STRING não está definida. "
            "Local: coloque no .env. No Azure: em Environment variables."
        )

    if _service_client is None:
        _service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

    return _service_client.get_container_client(CONTAINER)


def nome_do_cartaz(evento_id: int, extensao: str) -> str:
    """
    Nome de blob previsível, derivado do id.

    A barra não cria pasta de verdade — o container tem um nível só. Ela é
    só parte do nome, e o portal usa isso para desenhar uma árvore. O ganho
    real é outro: sabendo o id, você sabe onde o arquivo está, sem consultar
    o banco.
    """
    return f"eventos/{evento_id}/cartaz{extensao}"


def enviar_arquivo(nome_do_blob: str, conteudo: bytes, content_type: str) -> str:
    """
    Grava o conteúdo no container e devolve a URL do blob.

    `overwrite=True` faz o segundo envio substituir o primeiro — trocar o
    cartaz é só enviar de novo, já que o nome do blob é o mesmo. Sem isso,
    o Azure recusa com 409 quando o blob já existe.

    `content_settings` é o que faz o navegador exibir a imagem em vez de
    baixá-la. Sem isso todo blob é servido como application/octet-stream.
    """
    blob_client = _container_client().get_blob_client(nome_do_blob)

    blob_client.upload_blob(
        conteudo,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type),
    )

    return blob_client.url
