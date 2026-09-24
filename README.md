# Codex da Cachoeira
Codex.Kw1
Aplicação web desenvolvida com Django.

## Pré-requisitos

- Python 3.12 ou superior
- PostgreSQL em execução na porta `5432`
- Banco de dados `codex_db`
- Usuário `postgres` com senha `postgres`

As configurações atuais do banco estão em `codex/codex/settings.py`.

## Como rodar no Windows

No PowerShell, a partir da raiz do projeto:

```powershell
cd codex
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r ..\requirements.txt
python manage.py migrate
python manage.py runserver
```

Abra http://127.0.0.1:8000/ no navegador.

Caso o PowerShell bloqueie a ativação do ambiente virtual, execute uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Como rodar no macOS ou Linux

Na raiz do projeto:

```bash
cd codex
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r ../requirements.txt
python manage.py migrate
python manage.py runserver
```

Abra http://127.0.0.1:8000/ no navegador.

## Comandos úteis

Com o ambiente virtual ativado e dentro da pasta `codex`:

```bash
python manage.py createsuperuser
python manage.py test
python manage.py makemigrations
python manage.py migrate
```
