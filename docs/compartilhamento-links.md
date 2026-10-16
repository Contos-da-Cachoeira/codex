# Prévias ao compartilhar links

As informações Open Graph e Twitter Card são entregues no HTML inicial das páginas públicas, sem depender de JavaScript ou de login do aplicativo que lê o link. O protocolo é descrito em <https://ogp.me/>.

## Imagens por página

- **Página inicial:** capa do Codex, com nome e símbolo, em PNG de 1200 × 630 pixels.
- **Detalhes da Wiki:** imagem enviada pelo editor; quando não há upload, utiliza a ilustração cadastrada no conteúdo. Sem imagem vinculada, a prévia contém apenas texto.
- **Guildas:** nome, lema e símbolo públicos. Descrições internas e notícias privadas não entram na prévia.
- **LARP público:** título, resumo da história e capa do evento. Eventos ocultos e suas telas de gerenciamento não geram metadados de compartilhamento.
- **Leitor de documento:** título, descrição e capa do próprio PDF.
- **Listas e índices públicos:** título e descrição, sem capa genérica.
- **Fichas de personagens, contas, inscrições e administração:** sem metadados de compartilhamento. As fichas continuam exigindo login e acesso do dono ou administrador; não foi criado cartão público.

As imagens usam URLs absolutas, respeitando o endereço atual e HTTPS encaminhado pelo proxy. A URL da página não inclui filtros ou parâmetros de consulta. Nenhuma consulta adicional ao banco é feita para gerar os metadados; eles usam o conteúdo já carregado pela página.

O símbolo também aparece como favicon PNG de 32 × 32 pixels e ícone de 180 × 180 pixels para atalhos de dispositivos Apple. Para refazer a capa e esses ícones a partir do SVG existente, execute `codex/.venv/Scripts/python.exe tools/prepare_share_image.py`, com Playwright e Chrome disponíveis. Ao trocar os arquivos, altere também suas versões de cache nos templates e em `core/social.py`.

## Publicação e conferência

Publique o código, execute `collectstatic` e recarregue o Django. Confira anonimamente o HTML da página e a URL indicada em `og:image`: ambos precisam estar acessíveis publicamente para o aplicativo buscar a imagem. `127.0.0.1` serve para validação local; o compartilhamento externo usa o domínio público. O aplicativo controla o formato final da prévia.

Os testes em `core/test_social_meta.py` cobrem a capa inicial, as seis categorias públicas da Wiki, prioridade de upload sobre imagem estática, conteúdo sem imagem, guildas, LARPs públicos/ocultos, páginas restritas, URLs HTTPS e dimensões reais dos PNGs.
