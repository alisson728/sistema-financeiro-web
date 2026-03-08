# Gestão Financeira Pessoal — versão pronta para web

Este pacote já está ajustado para:

- rodar localmente no Windows
- publicar rápido no Render
- usar PostgreSQL em produção
- manter SQLite local para teste opcional
- servir frontend + backend no mesmo domínio

## Estrutura

```text
financeiro_pessoal/
├─ backend/
│  ├─ __init__.py
│  ├─ app.py
│  ├─ db.py
│  ├─ reminders.py
│  ├─ utils.py
│  ├─ whatsapp.py
│  └─ requirements.txt
├─ frontend/
├─ render.yaml
├─ .env.example
├─ .gitignore
├─ start_render_local.bat
└─ README.md
```

## Rodar localmente no Windows

### Opção rápida

Use:

```text
start_render_local.bat
```

### Opção manual

```bat
py -m pip install -r backend\requirements.txt
py -m backend.app
```

Abra no navegador:

```text
http://127.0.0.1:5000
```

## Banco de dados

### Local
Se a variável `DATABASE_URL` não estiver definida, o sistema usa:

```text
backend/financeiro.db
```

### Produção no Render
No Render, o sistema já foi preparado para usar PostgreSQL via variável `DATABASE_URL`.

## Deploy rápido no Render

O Render recomenda Flask com Gunicorn em um Web Service, e também suporta Postgres gerenciado e Blueprints via `render.yaml`. citeturn1search1turn0search0turn2view0

### Caminho mais fácil

1. Crie um repositório no GitHub.
2. Envie todos os arquivos deste projeto para o repositório.
3. No Render, vá em **Blueprints**.
4. Clique em **New Blueprint Instance**.
5. Conecte o seu repositório.
6. O Render vai ler o arquivo `render.yaml` e montar:
   - 1 web service
   - 1 banco PostgreSQL
7. Clique em **Apply**.

O `render.yaml` já está configurado com:
- build: `pip install -r backend/requirements.txt`
- start: `gunicorn --workers 1 backend.app:app`
- health check: `/api/health`
- banco Postgres conectado por `DATABASE_URL`

Render também documenta que serviços podem consumir a URL interna do Postgres por variável de ambiente, e que Blueprints são a forma de definir web service + database no mesmo deploy. citeturn0search0turn2view0

## Deploy manual no Render

Se não quiser usar Blueprint:

1. Crie o banco Postgres no Render.
2. Copie a connection string interna.
3. Crie um Web Service Python.
4. Use:

```text
Build Command: pip install -r backend/requirements.txt
Start Command: gunicorn --workers 1 backend.app:app
```

5. Crie a variável de ambiente:

```text
DATABASE_URL=<sua connection string do postgres>
```

## Domínio gratuito para teste

Para testar rápido, a própria URL do Render já funciona:

```text
https://seu-app.onrender.com
```

Você pode usar essa URL antes de pensar em domínio personalizado.

## WhatsApp

A parte de configuração continua pronta no painel do sistema.
Você só precisa preencher:

- Phone Number ID
- Access Token
- API Version
- Template Name
- Template Language
- Telefone destino

## Observações importantes

- Em produção, prefira PostgreSQL.
- SQLite foi mantido apenas para facilitar teste local.
- O frontend agora usa `/api`, então funciona no mesmo domínio sem depender de `127.0.0.1`.
- O backend sobe em `0.0.0.0` quando executado diretamente, facilitando deploy.

## Próximo passo para celular

Depois que validar na web, o melhor caminho é transformar esse sistema em:

- PWA instalável
- e depois APK Android

A base web já está pronta para isso.
