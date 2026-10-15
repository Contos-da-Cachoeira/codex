"""Complementa referências sem substituir textos personalizados pelo administrador."""
import json
from pathlib import Path

from django.db import migrations


FOCI = {
    'BARDO': 'Instrumento musical tocado; instrumentos de sopro são proibidos. Pelo Dom de Bardo, pode usar canto no lugar do instrumento.',
    'CLERIGO': 'Cajado, amuleto com símbolo da divindade ou livro sagrado.',
    'DRUIDA': 'Cajado, cristais ou amuletos ligados à natureza. Pelo Dom de Druida, também mato, flores ou folhas; galhos duros são proibidos.',
    'MAGO': 'Cajado, varinha ou grimório (livro de magia). Esferas são usadas conforme as regras de magia; não substituem a exigência do foco.',
    'PALADINO': 'Amuleto com símbolo da divindade. Pelo Dom de Paladino, o símbolo na frente do escudo permite usá-lo como foco.',
}
ITEMS = {
    'sangue-de-dragao': 'Após beber, grite DRAGÃO. Ganha 7 PV temporários, até o máximo de 10 PV, imunidade a desmembramento e BRUTAL em todos os golpes. O efeito dura 5 minutos ou até o fim do combate. Ao terminar, o usuário morre em 10 segundos. Apenas Água Primordial pode ressuscitá-lo.',
    'laco-da-verdade': 'Corda mágica: quem estiver preso não pode mentir, mas pode omitir. É um efeito mental. A habilidade é de uso único; depois de usada, resta uma corda comum.',
}


def reference(slug, name, summary, sections, category='cenario'):
    return {'category': category, 'slug': slug, 'name': name, 'visible': True,
            'data': {'categoria': 'Contos da Cachoeira' if category == 'cenario' else 'Manual LARP 3.3',
                     'resumo': summary, 'ordem': 10,
                     'secoes': [{'titulo': title, 'itens': items} for title, items in sections]}}


REFERENCES = [
    reference('historia-e-cachoeira', 'A Cachoeira e a história do mundo',
              'A origem da magia, a Guerra Santa e o tempo das guildas.', [
        ('A Sagrada Cachoeira', ['A magia chega ao mundo como um fluxo de energia de colisões entre dimensões. Proteger esse fluxo é central aos conflitos dos Contos da Cachoeira.']),
        ('Eras e organizações', ['Wukong derrotou e baniu os antigos deuses. O Makka-Kuh assumiu a proteção do mundo.',
          'A Queda da Cachoeira foi causada pela Sombra da Serpente e seguida pela restauração do fluxo e pela Guerra Santa.',
          'Após a guerra, as guildas atuam em parceria com a Ordem da Zona Neutra. Artistas da Revolução é a mais nova das seis guildas apresentadas no Manual 3.3.',
          'Makka-Kuh, Serpente e outras organizações descritas na seção Organizações do Passado são referências históricas, não escolhas automáticas de guilda atual.']),
        ('Fontes e lacunas', ['Cenário, páginas 1–5 e 18–23; Manual 3.3, páginas 5–10. A descrição da quarta era repete um trecho da terceira e a nona sessão aparece apenas como título no caderno. A comissão pode esclarecer esses acontecimentos.'])]),
    reference('divindades-do-cenario', 'Divindades do cenário',
              'Entidades veneradas e a relação religiosa de Clérigos e Paladinos.', [
        ('Entidades, não um panteão fechado', ['Após o banimento dos antigos deuses, entidades poderosas passaram a ser veneradas. Os exemplos do caderno não constituem uma lista exaustiva.',
          'Clérigos e Paladinos precisam venerar uma divindade do cenário; não podem ser ateus ou apenas devotos de uma filosofia. Divindades personalizadas exigem avaliação da comissão.']),
        ('Exemplos conhecidos', ['Sun Wukong, o Macaco Rei; Grande Corvo Ancestral; Solaris; Espírito da Memória.',
          'Mãe Elemental, também chamada Mãe Natureza; Lunna, a Velha Caçadora; Artista, a Tecelã dos Sonhos.',
          'Rainha da Morte, ligada à passagem das almas; Jhunni, a Dama do Caos, ligada a caos, oportunidades e ilusões.']),
        ('Referência', ['Cenário, páginas 11–14; Manual 3.3, páginas 12 e 15. A entidade venerada pela guilda não obriga automaticamente todos os seus membros a serem Clérigos ou Paladinos.'])]),
    reference('lugares-e-planos', 'Lugares e planos', 'Regiões do mundo e dimensões além dele.', [
        ('Regiões', ['Ravenlok reúne tribos guerreiras do norte e tem forte relação com o Círculo do Fogo.',
          'Pucklândia mantém tradições de necromancia e carrega as consequências da Guerra Santa.',
          'Te-fit é um arquipélago protegido pelo Véu da Neblina e pelos espíritos locais; a Floresta do Sol mantém relações com suas terras.',
          'A antiga Ufter foi destruída e tomada pela floresta, repleta de consequências de magia caótica.',
          'O Abismo de Hell ocupa a região devastada do antigo Templo da Cachoeira e abriga perigos e tesouros do passado.']),
        ('Outros planos', ['A Cidade de Prata é o refúgio extradimensional dos anjos.',
          'O Submundo recebe as almas dos mortos e é disputado pela Rainha da Morte e por Jhunni.',
          'O Abismo é um plano de demônios, onde Orochi habita. Não deve ser confundido com toda a região física do Abismo de Hell.',
          'Os reinos das fadas são dimensões de magia caótica, sonhos e natureza.']),
        ('Referência', ['Cenário, páginas 15–18. Origem narrativa não concede poderes adicionais à classe; características excepcionais dependem da comissão.'])]),
    reference('zona-neutra-e-pactos', 'Zona Neutra e pactos de guilda',
              'Descanso, asilo, vínculo mágico e consequências de deserção.', [
        ('Zona Neutra', ['É um espaço de descanso e comércio onde não são permitidas agressões, armas sacadas ou efeitos que profanem o asilo.',
          'Cada Zona tem um Guardião e regras locais. A comissão define sua aplicação durante a sessão.',
          'Há uma divergência sobre a Serpente: o Cenário p. 5 oferece proteção, mas seu pacto na p. 6 e o Manual p. 5 negam asilo aos fiéis de Orochi. Também há diferença sobre preferências do Guardião. Consulte a comissão antes de assumir uma exceção.']),
        ('Pacto de guilda', ['Entrar vincula o personagem ao Livro da Guilda e aos seus dogmas. Traição e deserção podem gerar marcas cumulativas.',
          'Uma saída segura requer autorização da guilda. Marcas, redenção e perdão são decisões interpretativas da comissão, e os benefícios do desertor cessam ao fim da sessão.',
          'Na Sociedade Zaori, apagar memórias é condição de saída autorizada. A marca por pecado ou traição é Cegueira egoísta; são situações distintas.',
          'A punição solar da Floresta tem descrições diferentes no Manual p. 8 e no Cenário p. 9; o efeito vigente deve ser confirmado pela comissão.']),
        ('Referência', ['Manual 3.3, páginas 5–10; Cenário, páginas 5–11.'])]),
    reference('combate-dano-e-equipamento', 'Combate, dano e equipamento',
              'Pontos de vida, desmembramentos e limites básicos de carga.', [
        ('Dano e segurança', ['Personagens comuns têm 3 PV. Braços e pernas sofrem 1 de dano; tronco sofre 2. Mãos segurando equipamentos e pés no chão não são áreas de dano.',
          'Golpes que atingem somente armadura não causam dano; frestas continuam vulneráveis. Brutal ignora armadura, mas não escudo.',
          'Golpes na cabeça, genitais e seios são proibidos. Um golpe que machuque pode incapacitar o personagem do atacante, conforme o manual.']),
        ('Condições de dano', ['Braço atingido não pode lutar, segurar foco ou conjurar. Uma perna atingida impede correr; duas impedem andar.',
          'Acerto no tronco exige segurá-lo com uma mão e impede correr. Após o combate, dano nas duas pernas pode ser trocado por dano no peito.']),
        ('Carga e uso', ['O limite inicial é de 3 equipamentos, armas ou escudos, com exceções por talentos. Arqueiros carregam até 10 flechas e quem sabe arremessar começa com uma arma de arremesso.',
          'Uma mão utiliza um equipamento ou um foco por vez. Em dual, uma arma precisa ser curta. Usar cajado é incompatível com escudo.',
          'Proficiências, armaduras e exceções dependem da classe e dos talentos ativos.']),
        ('Referência', ['Manual 3.3, páginas 2, 10–15 e 18–22.'])], 'regras'),
    reference('morte-descanso-e-veneno', 'Incapacitação, morte, descanso e veneno',
              'Quando contar a morte, como descansar e como lidar com envenenamento.', [
        ('Incapacitado não é morto', ['Ao chegar a 0 PV, agache ou sente, movendo-se apenas para evitar acidentes. Após o combate, conte lentamente até 300; sem cura, o personagem morre.',
          'Sementes dos Deuses, Toque da Cura e Milagres podem recuperar um incapacitado conforme suas regras.']),
        ('Ressurreição', ['Milagre devolve o morto com 1 PV e dano no tronco. Ele não pode correr, lutar ou conjurar e não recebe outras curas até descansar na Zona Neutra.',
          'Um descanso curto na Zona Neutra também ressuscita. O Guardião define consequências interpretativas cumulativas da morte.',
          'A morte causada por Sangue de Dragão é uma exceção: somente Água Primordial ressuscita.']),
        ('Descansos', ['Descanso curto: 5 minutos na Zona Neutra recuperam PV, condições de dano e veneno; pode ser repetido.',
          'Descanso longo: 30 minutos na Zona Neutra, uma vez por sessão; inclui descanso curto e recupera uso de habilidade especial. Talentos com regra própria seguem sua descrição.']),
        ('Veneno e imunidades', ['Uma dose aplicada na arma afeta o primeiro alvo acertado; anuncie VENENO. O alvo não pode correr e inicia a contagem de 300 após o combate.',
          'Sem antídoto ou Zona Neutra até o fim da contagem, o alvo morre. Curar PV não remove o veneno.',
          'Anuncie IMUNIDADE ao receber efeito ao qual é imune. Um efeito de uso único não é consumido quando utilizado contra um alvo imune.']),
        ('Referência', ['Manual 3.3, páginas 2–4 e 21.'])], 'regras'),
    reference('experiencia-moeda-e-missoes', 'XP, moeda, talentos e missões',
              'Recompensas de sessão, compras e a organização das missões.', [
        ('XP e talentos', ['Participar rende 15 XP; atuar como NPC rende 15 XP adicionais. Caracterização casual rende 10 XP e total rende 15 XP. Missões, funções e feitos memoráveis têm recompensas avaliadas pelo Mestre.',
          'Ajudar na arrumação faz parte da sessão; não ajudar pode reduzir o XP até zero. A comissão registra a recompensa final.',
          'Talentos exigem história e evolução, pertencem ao personagem e não migram para outro. No site, cada compra ativa ocupa uma das cinco vagas, inclusive repetições, conforme decisão do responsável.']),
        ('Dindins', ['1 DO equivale a 2 DP. Valores como 1,5 DO podem ser registrados; 0,5 DO representa uma moeda de prata.',
          'A sessão prevê 2 DO; NPCs recebem +3 DO por sessão de trabalho. Bardo e Ladino têm 2 DO adicionais como item inicial. Cada compra ativa de Recursos financeiros acrescenta 3 DO no início da sessão.',
          'Ao final, as riquezas são entregues à comissão para registro. Itens de sessão só podem ser usados naquela sessão.']),
        ('Missões', ['Uma estrela: tarefas recorrentes, abertas também a mercenários. Duas ou três estrelas: missões exclusivas de guildas, realizadas uma vez e sujeitas a fracasso. Quatro e cinco estrelas: desafios urgentes ou graves, abertos também a mercenários.',
          'Uma guilda pode assumir apenas uma missão exclusiva por vez. A soma de estrelas concluídas define prioridade na escolha.',
          'Guildas podem dividir a missão e negociar a recompensa com mediação da Zona Neutra; todas ficam vinculadas àquela missão. Mostre o cartaz a quem for auxiliá-la e comprove a conclusão ao Mestre.']),
        ('Referência', ['Manual 3.3, páginas 11, 13 e 17–20.'])], 'regras'),
]


def review(apps, schema_editor):
    Entry = apps.get_model('wiki', 'WikiEntry')
    Purchase = apps.get_model('personagens', 'CompraTalento')
    alias = schema_editor.connection.alias
    originals = json.loads(Path(__file__).with_name('initial_content.json').read_text(encoding='utf-8'))
    old_items = {item['slug']: item['data'] for item in originals if item['category'] == 'itens'}
    original_talents = {item['data'].get('chave'): item['data'] for item in originals if item['category'] == 'talentos'}
    for entry in Entry.objects.using(alias).all():
        data = dict(entry.data)
        if entry.category == 'classes' and data.get('chave') in FOCI:
            data.setdefault('foco', FOCI[data['chave']])
        if entry.category == 'itens' and entry.slug in ITEMS and data.get('descricao') == old_items.get(entry.slug, {}).get('descricao'):
            data['descricao'] = ITEMS[entry.slug]
        if entry.category == 'talentos' and data.get('chave') in {'FEITICO_ANTIGO', 'FORMA_SELVAGEM'}:
            data['stackavel'] = True
        if data != entry.data:
            entry.data = data
            entry.save(using=alias, update_fields=['data'])
    catalog = {entry.data.get('chave') or f'WIKI_{entry.pk}': entry.as_content() if hasattr(entry, 'as_content') else {**entry.data, 'nome': entry.name}
               for entry in Entry.objects.using(alias).filter(category='talentos')}
    for purchase in Purchase.objects.using(alias).filter(regra_snapshot={}):
        purchase.regra_snapshot = {**original_talents.get(purchase.talento, {}), **catalog.get(purchase.talento, {}), 'custo_xp': purchase.custo_xp}
        purchase.save(using=alias, update_fields=['regra_snapshot'])
    for row in REFERENCES:
        Entry.objects.using(alias).get_or_create(category=row['category'], slug=row['slug'], defaults={k: v for k, v in row.items() if k not in {'category', 'slug'}})


class Migration(migrations.Migration):
    dependencies = [('wiki', '0003_alter_wikientry_category'), ('personagens', '0008_compratalento_escolhas_classe_and_more')]
    operations = [migrations.RunPython(review, migrations.RunPython.noop)]
