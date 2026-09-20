# Aula 08 — arquivos de referência do upload

Versão final do laboratório: a API da Aula 06, acrescida do envio de cartaz
para o Azure Blob Storage.

| Arquivo | O que é |
|---|---|
| `main.py` | A API, com a rota nova `POST /eventos/{id}/cartaz` |
| `storage.py` | A camada de armazenamento — o único arquivo que fala com o Azure |
| `models.py` | A tabela, agora com a coluna `cartaz_url` |
| `schemas.py` | O contrato: `cartaz_url` só aparece na resposta |
| `database.py` | Idêntico ao da Aula 06 |
| `requirements.txt` | O que o Azure instala durante o build |
| `.env.example` | Modelo do `.env` — copie, renomeie e preencha |
| `.gitignore` | Impede que `.venv`, `.env` e `*.db` subam para o repositório |
| `requests.http` | Testes com a extensão REST Client |

## Antes de rodar

```bash
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preencha a connection string da sua
Storage Account. O `.env` está no `.gitignore` — a chave dá acesso total à
conta e não entra no repositório em nenhuma hipótese.

Se você já tinha um `eventos.db` da Aula 06, apague-o. O `create_all` cria
tabelas que ainda não existem, mas não acrescenta coluna em tabela já
criada — sem apagar, a coluna `cartaz_url` nunca aparece.

```bash
fastapi dev main.py
```

## Na versão publicada

Em **Configuration → Environment variables** do App Service, crie:

| Nome | Valor |
|---|---|
| `AZURE_STORAGE_CONNECTION_STRING` | a connection string da conta |
| `AZURE_STORAGE_CONTAINER` | `cartazes` |

O `load_dotenv()` do `storage.py` não encontra `.env` no Azure e
simplesmente não faz nada — as variáveis já estão no ambiente.

## O que a rota faz, na ordem

1. o evento existe? → 404 se não
2. o `content-type` está na lista aceita? → 415 se não
3. o arquivo cabe no limite? → 413 se não
4. envia para o blob e grava a URL no evento

O container é privado: abrir a URL direto no navegador devolve erro. Para
ver a imagem, gere um SAS no portal (**Containers → o blob → Generate SAS**)
ou abra pelo próprio portal.
