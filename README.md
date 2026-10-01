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

### Tunel SSH local para o banco

Para usar o PostgreSQL remoto por meio do alias SSH `kiwiki`, configure no `.env` local:

```dotenv
AUTO_SSH_DB_TUNNEL=True
SSH_DB_HOST=kiwiki
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
```

Com essa opção ativada, `python manage.py runserver` verifica a porta `5433`, abre o túnel SSH somente quando necessário e o encerra apenas se ele tiver sido criado por aquela execução. Com `AUTO_SSH_DB_TUNNEL=False` ou ausente, o `runserver` mantém o comportamento padrão do Django.

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

### Imagens compartilhadas com o servidor

Uploads usam o armazenamento padrão do Django. No servidor, os arquivos ficam
em `codex/media/`, publicado pelo Nginx em `/media/`. Para enviar imagens ao mesmo
diretório ao executar o site no computador, configure as variáveis
`DJANGO_MEDIA_SFTP_*` e a URL pública `DJANGO_MEDIA_URL` descritas em `.env.example`.
A conexão usa a chave SSH local; ela não deve ser copiada para o repositório.
O computador precisa conseguir acessar o servidor por SSH (incluindo a rede
Tailscale, quando usada). Reinicie o servidor local após alterar o `.env`.

Para copiar arquivos antigos, execute `python manage.py sync_media_to_storage`
para conferir e acrescente `--apply` para transferir. O comando verifica SHA-256,
preserva os arquivos locais e interrompe caso um caminho remoto tenha conteúdo
diferente. Não configure SFTP no próprio servidor de produção: ele já usa o disco
publicado pelo Nginx.

Referência: [armazenamento SFTP do django-storages](https://django-storages.readthedocs.io/en/latest/backends/sftp.html).

Com o ambiente virtual ativado e dentro da pasta `codex`:

```bash
python manage.py createsuperuser
python manage.py test
python manage.py makemigrations
python manage.py migrate
```
