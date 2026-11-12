#!/usr/bin/env python3
"""Gera as páginas internas do site do Quarks (www.quarksedu.com.br) e o sitemap.xml.

    python3 scripts/gerar_paginas.py                 # lê ../quarks-gestao/bancodenotas
    python3 scripts/gerar_paginas.py --gestao CAMINHO

O que sai (cada uma é uma pasta com index.html, servida como /pasta/):
  - páginas dos serviços: preparatorio-pism, preparatorio-if-sudeste, acompanhamento-escolar, aula-particular,
    mentoria-de-estudos e aprovados (textos em SERVICOS, abaixo);
  - guia do PISM (pism/) e gabarito do PISM 2027 (gabarito-pism-2027/), com datas do Edital 10/2026 da Copese;
  - notas de corte do PISM (nota-de-corte-pism/ e uma página por curso) e do IF Sudeste MG
    (nota-de-corte-if-sudeste/), montadas do Banco de notas da gestão (bancodenotas/pism.json e if.json:
    só números agregados, sem nome de ninguém);
  - simulador-pism/ (o mesmo simulador da página inicial);
  - sitemap.xml (todas as páginas) e paginas.txt (as pastas que o publicar.yml envia).

Banco de notas novo (todo ano, quando sai o resultado do PISM III)? Rode de novo e faça commit do que mudou.
Página nova? Acrescente aqui; não edite os index.html gerados à mão (serão sobrescritos).
"""
import argparse, html, json, os, re, shutil, sys, datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.quarksedu.com.br"
HOJE = datetime.date.today().isoformat()
ZAP = "5532998057212"
AVALIAR = "https://g.page/r/CU071YWDNuDYEBM/review"   # link "Pedir avaliações" do Perfil da Empresa no Google (dono, 12/11/2026)
SIM_V = "25.14"   # mesmo ?v= do simulador na página inicial (index.html)
CSS = ["/site/site-20261019c.css", "/site/vitrine-20261019.css", "/site/paginas-20261112.css"]
JS_SITE = "/site/site-20261110.js"
# pastas de outros sistemas no public_html: nunca podem ser usadas por página do site
PROIBIDAS = {"familia", "lab", "labaluno", "labprof", "loja", "minhacasa", "portal", "prof", "quarks-backups", "sistema", "site", "privacidade", "termos"}

e = lambda s: html.escape(str(s), quote=True)
DEST = ' class="dest"'


def zap(txt):
    from urllib.parse import quote
    return f"https://wa.me/{ZAP}?text={quote(txt)}"


def br(n, casas=2):
    """número no jeito brasileiro: 1.040,25 (sem casas quando é inteiro)"""
    if n is None:
        return "—"
    n = float(n)
    if casas and abs(n - round(n)) > 1e-9:
        s = f"{n:,.{casas}f}"
    else:
        s = f"{round(n):,}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------------------------------------------
# moldura de todas as páginas
# ---------------------------------------------------------------------------------------------------------------
TOPO = """<header class="topo" data-sec="site.topo" data-sec-rot="Cabeçalho">
  <div class="wrap">
    <a class="marca" href="/" aria-label="Quarks, início"><img src="/site/img/logo-white-text.png" alt="Quarks" width="160" height="30"></a>
    <nav id="menu" aria-label="Principal">
      <a href="/#presencial" data-c="site.topo.t1">Presencial</a>
      <a href="/pism/">Guia do PISM</a>
      <a href="/nota-de-corte-pism/">Notas de corte</a>
      <a href="/aprovados/">Aprovados</a>
      <a href="/simulador-pism/">Simule</a>
      <a href="/#visite" data-c="site.topo.t5">Visite</a>
      <a class="entrar-m" href="https://portal.quarksedu.com.br/" data-c="site.topo.t6" data-c-href="site.topo.t6.link">Entrar no Portal Quarks</a>
    </nav>
    <div class="acoes">
      <a class="entrar" href="https://portal.quarksedu.com.br/" data-c="site.topo.t7" data-c-href="site.topo.t7.link">Entrar</a>
      <a class="loja-bt" href="https://loja.quarksedu.com.br/" data-c="site.topo.t8" data-c-href="site.topo.t8.link">Loja</a>
      <button class="hamb" type="button" aria-label="Abrir o menu" aria-expanded="false" aria-controls="menu"><i></i></button>
    </div>
  </div>
</header>"""

GUIAS = [("/preparatorio-pism/", "Preparatório PISM"), ("/preparatorio-if-sudeste/", "Preparatório IF Sudeste"),
         ("/acompanhamento-escolar/", "Acompanhamento Escolar"), ("/aula-particular/", "Aula particular"),
         ("/mentoria-de-estudos/", "Mentoria de estudos"), ("/pism/", "Guia do PISM 2027"),
         ("/gabarito-pism-2027/", "Gabarito do PISM 2027"), ("/nota-de-corte-pism/", "Notas de corte do PISM"),
         ("/nota-de-corte-if-sudeste/", "Notas de corte do IF Sudeste"), ("/simulador-pism/", "Simulador do PISM"),
         ("/aprovados/", "Aprovados")]


def faixa_guias():
    return '<div class="in r2-guias"><b>Guias e cursos</b>' + "".join(f'<a href="{u}">{e(t)}</a>' for u, t in GUIAS) + "</div>"


RODAPE = """<footer class="rod2" data-sec="site.rod" data-sec-rot="Rodapé">
  <div class="in">
    <div class="r2-marca"><img src="/site/img/logo-white-text.png" alt="Quarks" width="160" height="30" loading="lazy"><p data-c="site.rod.t1">Cursinho em Juiz de Fora para o PISM, o IF Sudeste e o reforço escolar. Aprender é conquistar.</p></div>
    <div class="r2-col"><b data-c="site.rod.t2">O Quarks</b><ul data-lista="site.rod.quarks"><li data-item><a href="/#presencial" data-f="f0" data-f-href="f0_link">Presencial</a></li><li data-item><a href="/#trilha" data-f="f0" data-f-href="f0_link">Trilha de estudos</a></li><li data-item><a href="/#aprovados" data-f="f0" data-f-href="f0_link">Aprovados</a></li><li data-item><a href="/#visite" data-f="f0" data-f-href="f0_link">Visite a unidade</a></li></ul></div>
    <div class="r2-col"><b data-c="site.rod.t3">Loja</b><ul data-lista="site.rod.loja"><li data-item><a href="https://loja.quarksedu.com.br/apostilas" data-f="f0" data-f-href="f0_link">Apostilas</a></li><li data-item><a href="https://loja.quarksedu.com.br/laboratorio" data-f="f0" data-f-href="f0_link">Laboratório</a></li><li data-item><a href="https://loja.quarksedu.com.br/aulas" data-f="f0" data-f-href="f0_link">Aulas online</a></li><li data-item><a href="https://portal.quarksedu.com.br/" data-f="f0" data-f-href="f0_link">Entrar no Portal</a></li></ul></div>
    <div class="r2-col"><b data-c="site.rod.t4">Fale com a gente</b><ul data-lista="site.rod.contato"><li data-item><a href="https://wa.me/5532998057212" target="_blank" rel="noopener" data-f="f0" data-f-href="f0_link">WhatsApp (32) 99805-7212</a></li><li data-item><a href="https://maps.google.com/?q=Av.%20Rui%20Barbosa%2C%201449%2C%20Juiz%20de%20Fora" target="_blank" rel="noopener" data-f="f0" data-f-href="f0_link">Av. Rui Barbosa, 1449, Santa Terezinha, Juiz de Fora</a></li><li data-item><a href="https://www.instagram.com/quarksedu" target="_blank" rel="noopener" data-f="f0" data-f-href="f0_link">@quarksedu</a></li><li data-item><a href="https://g.page/r/CU071YWDNuDYEBM/review" target="_blank" rel="noopener" data-f="f0" data-f-href="f0_link">★ Avalie o Quarks no Google</a></li></ul></div>
  </div>
  """ + faixa_guias() + """
  <div class="in r2-base"><span>© 2026 Quarks Edu · Juiz de Fora (MG)</span><span class="r2-leg"><a href="/privacidade/">Privacidade</a> · <a href="/termos/">Termos</a> · <a href="https://loja.quarksedu.com.br/">Loja do Quarks</a></span></div>
</footer>
<a class="whats" href="https://wa.me/5532998057212?text=Ol%C3%A1!%20Vim%20pelo%20site%20do%20Quarks." target="_blank" rel="noopener" aria-label="Falar com o Quarks no WhatsApp"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6a2.7 2.7 0 0 0 1.8-1.3 2.2 2.2 0 0 0 .2-1.3c-.1-.1-.3-.2-.5-.3Z"/></svg></a>"""

ORG = {"@id": f"{SITE}/#quarks"}
PAGINAS = []   # (caminho, prioridade)


def migalhas(itens):
    """itens: [(nome, caminho)]; o primeiro é sempre Início"""
    todos = [("Início", "/")] + itens
    li = "".join(f'<li><a href="{c}">{e(n)}</a></li>' if i < len(todos) - 1 else f'<li aria-current="page">{e(n)}</li>' for i, (n, c) in enumerate(todos))
    schema = {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + c} for i, (n, c) in enumerate(todos)]}
    return f'<ol class="pg-trilha">{li}</ol>', schema


def faq_html(perguntas):
    if not perguntas:
        return "", None
    corpo = "".join(f"<details><summary>{e(p)}</summary><p>{r}</p></details>" for p, r in perguntas)
    schema = {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": p, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", r)}} for p, r in perguntas]}
    return f'<section class="pg-bloco pg-faq"><h2>Perguntas frequentes</h2>{corpo}</section>', schema


def cta(titulo, texto, botao, msg, segundo=None):
    s = f'<a class="pg-bt2" href="{segundo[1]}">{e(segundo[0])}</a>' if segundo else ""
    return (f'<section class="pg-bloco pg-cta"><h2>{e(titulo)}</h2><p>{texto}</p><div class="pg-ctas">'
            f'<a class="btn am" href="{zap(msg)}" target="_blank" rel="noopener">{e(botao)}</a>{s}</div></section>')


def escrever(caminho, *, titulo, descricao, h1, lead, corpo, trilha, selo="", ctas="", numeros="", schemas=(), imagem="/site/img/sala-pism.webp",
             scripts="", prioridade="0.7", sec=None):
    pasta = caminho.strip("/")
    assert pasta.split("/")[0] not in PROIBIDAS, pasta
    mig, mig_schema = migalhas(trilha)
    url = f"{SITE}/{pasta}/"
    grafo = [mig_schema, {"@type": "WebPage", "@id": url, "url": url, "name": titulo, "description": descricao, "inLanguage": "pt-BR",
                          "isPartOf": {"@id": f"{SITE}/#site"}, "publisher": ORG, "dateModified": HOJE}] + [s for s in schemas if s]
    ld = json.dumps({"@context": "https://schema.org", "@graph": grafo}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    dc = (lambda k: f' data-c="site.{sec}.{k}"') if sec else (lambda k: "")
    secattr = f' data-sec="site.{sec}" data-sec-rot="{e(h1)}"' if sec else ""
    doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title{dc('meta.titulo')}>{e(titulo)}</title>
<meta name="description"{dc('meta.descricao')} content="{e(descricao)}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Quarks Edu">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{imagem}">
<meta name="theme-color" content="#5B37AE">
<link rel="icon" href="/site/img/favicon-96.png" sizes="96x96" type="image/png">
<link rel="apple-touch-icon" href="/site/img/apple-touch-icon.png">
<link rel="preload" href="/site/fontes/BricolageGrotesque-800.woff2" as="font" type="font/woff2" crossorigin>
{chr(10).join(f'<link rel="stylesheet" href="{c}">' for c in CSS)}
<script type="application/ld+json">{ld}</script>
</head>
<body class="mk d-g lj pg-site pg-interna">
{TOPO}
<main id="conteudo">
  <section class="pg-capa"{secattr}>
    <div class="pg-in">
      {mig}
      {f'<span class="pg-selo">{e(selo)}</span>' if selo else ''}
      <h1{dc('h1')}>{e(h1)}</h1>
      <p class="pg-lead"{dc('lead')}>{lead}</p>
      {ctas}
      {numeros}
    </div>
  </section>
  <div class="pg-in pg-corpo">
{corpo}
  </div>
</main>
{RODAPE}
<script src="{JS_SITE}"></script>
<script src="https://sistema.quarksedu.com.br/sinal.js" data-ramo="site" defer></script>
{scripts}
</body>
</html>
"""
    destino = os.path.join(RAIZ, pasta, "index.html")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(doc)
    PAGINAS.append((f"/{pasta}/", prioridade))


def bloco(titulo, conteudo, classe=""):
    return f'<section class="pg-bloco {classe}"><h2>{e(titulo)}</h2>{conteudo}</section>'


def botoes(principal, msg, segundo=None):
    s = f'<a class="pg-bt2" href="{segundo[1]}">{e(segundo[0])}</a>' if segundo else ""
    return f'<div class="pg-ctas"><a class="btn am" href="{zap(msg)}" target="_blank" rel="noopener">{e(principal)}</a>{s}</div>'


ENDERECO = "Av. Rui Barbosa, 1449, Santa Terezinha, Juiz de Fora (MG)"
HORARIO = "segunda a quinta, das 9h às 20h; sexta, das 9h às 19h; sábado, das 8h às 12h"
TRILHA_PASSOS = """<ol class="pg-passos">
<li><b>Diagnóstico.</b> Algumas questões por matéria mostram onde o aluno está, e a trilha começa no ponto certo.</li>
<li><b>Trilha do edital.</b> Os conteúdos da prova na ordem certa. A coordenação ajusta para cada aluno.</li>
<li><b>Videoaula e teoria.</b> Cada etapa tem a explicação em vídeo e a teoria escrita pelo Quarks.</li>
<li><b>Treino Quarks.</b> Exercícios do fácil ao nível de prova. A etapa só conclui com 10 questões certas.</li>
<li><b>Prova oficial.</b> Questões que caíram de verdade na prova, com a prova e o ano.</li>
<li><b>Revisão.</b> Cada erro vai para o caderno de erros, e o conteúdo volta em 1, 7 e 30 dias.</li>
</ol>"""
PAIS = """<ul>
<li><b>A semana numa frase:</b> como o filho está, com o selo Indo bem, Pede atenção ou Precisa de apoio.</li>
<li><b>Os sinais explicados:</b> presença, tarefas, simulados e estudo em casa, com o que cada número quer dizer e como ajudar.</li>
<li><b>A trilha até a prova:</b> quanto do edital já foi estudado, matéria por matéria.</li>
<li><b>A coordenação junto:</b> ela acompanha a mesma trilha e é avisada quando o aluno fica dias sem estudar.</li>
</ul>"""
VISITA = (f"<p>O Quarks fica na <b>{ENDERECO}</b>. Atendimento de {HORARIO}. "
          f'Agende uma visita pelo <a href="{zap("Olá! Quero agendar uma visita ao Quarks.")}" target="_blank" rel="noopener">WhatsApp (32) 99805-7212</a> '
          f'ou veja <a href="https://maps.google.com/?q=Av.%20Rui%20Barbosa%2C%201449%2C%20Juiz%20de%20Fora" target="_blank" rel="noopener">como chegar</a>. '
          f'Já estuda ou estudou no Quarks? <a href="{AVALIAR}" target="_blank" rel="noopener">Conte como foi no Google ★</a></p>')


def servico(nome, desc):
    return {"@type": "Service", "name": nome, "description": desc, "provider": ORG, "areaServed": {"@type": "City", "name": "Juiz de Fora"}}


def curso(nome, desc):
    return {"@type": "Course", "name": nome, "description": desc, "provider": ORG, "inLanguage": "pt-BR",
            "hasCourseInstance": {"@type": "CourseInstance", "courseMode": "onsite", "location": {"@type": "Place", "name": "Quarks Edu", "address": ENDERECO}}}


# ---------------------------------------------------------------------------------------------------------------
# páginas dos serviços
# ---------------------------------------------------------------------------------------------------------------
def paginas_servicos():
    # Preparatório PISM
    perguntas = [
        ("O Preparatório PISM do Quarks é presencial?", f"Sim. As aulas são presenciais, na {ENDERECO}, em turmas de até 10 alunos."),
        ("Para qual módulo do PISM é o preparatório?", "Para os três: PISM I (1º ano do ensino médio), PISM II (2º ano) e PISM III (3º ano). A trilha de estudos segue o conteúdo de cada módulo."),
        ("Quando é a prova do PISM 2027?", 'As provas de todos os módulos são em 05 e 06/12/2026, e os gabaritos saem em 07/12/2026, segundo o Edital 10/2026 da Copese/UFJF. Veja o <a href="/pism/">guia do PISM 2027</a>.'),
        ("Como sei quanto preciso tirar para o meu curso?", 'Veja a <a href="/nota-de-corte-pism/">nota de corte de cada curso da UFJF</a> e use o <a href="/simulador-pism/">simulador do PISM</a>, feitos com as notas oficiais da UFJF.'),
        ("Os pais acompanham o estudo?", "Sim. No portal das famílias os pais veem a presença, as tarefas, os simulados e a trilha, com cada número explicado."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (
        bloco("O PISM se ganha nos três anos", "<p>O PISM é o vestibular seriado da UFJF: uma prova por ano do ensino médio, e a nota final soma os três módulos, com peso maior a cada ano. "
              "Quem chega ao PISM III com o I e o II bem feitos entra na disputa do curso que quer. Por isso o Preparatório PISM do Quarks acompanha o aluno <b>o ano todo</b>, com foco no que mais cai na UFJF, e não só na véspera da prova.</p>"
              '<p>Turmas presenciais de <b>até 10 alunos</b>, apostila própria com o raio-X da prova, laboratório de simulações e a trilha do edital do PISM no Portal Quarks.</p>'
              '<div class="pg-foto"><img src="/site/img/curso-pism.webp" alt="Aluno do Preparatório PISM do Quarks" width="720" height="900" loading="lazy"></div>')
        + bloco("O que vem no Preparatório PISM", '<div class="pg-grade">'
                '<div class="pg-cartao"><b>Turmas pequenas</b><p>Até 10 alunos por turma, para o professor conhecer cada um e tirar dúvida na hora.</p></div>'
                '<div class="pg-cartao"><b>Apostila própria</b><p>Raio-X da prova, mapa de incidência, questões por nível e gabarito comentado, para o PISM I, II e III.</p></div>'
                '<div class="pg-cartao"><b>Trilha do edital</b><p>Os conteúdos do módulo na ordem certa, com videoaula, teoria, treino e questões oficiais.</p></div>'
                '<div class="pg-cartao"><b>Laboratório</b><p>Simulações de Física, Química, Matemática e Português por etapa do PISM.</p></div>'
                '<div class="pg-cartao"><b>Notas de verdade</b><p>O simulador e as notas de corte do Quarks usam as notas oficiais da UFJF desde 2019.</p></div>'
                '<div class="pg-cartao"><b>Família junto</b><p>Portal das famílias com presença, tarefas, simulados e a trilha.</p></div></div>')
        + bloco("A trilha de estudos, passo a passo", "<p>Vem junto com o Preparatório PISM. É montada pelo edital da prova e ajustada pela coordenação para cada aluno.</p>" + TRILHA_PASSOS)
        + bloco("Quanto o seu curso pede", '<p>Na ampla concorrência do PISM 2026, Medicina (integral) fechou em 1.040,25 pontos, Direito (integral) em 890 e Direito (noturno) em 806,75, de 1.300 possíveis. '
                'Veja <a href="/nota-de-corte-pism/">a nota de corte de todos os cursos de Juiz de Fora</a>, ano a ano e por grupo de cotas, ou faça a conta no <a href="/simulador-pism/">simulador</a>.</p>'
                '<p class="pg-fonte">Fonte: UFJF/Copese, resultado final do PISM III.</p>')
        + faq
        + bloco("Venha conhecer", VISITA, "pg-lilas")
        + cta("Comece o Preparatório PISM", "A coordenação do Quarks responde pelo WhatsApp com as turmas e os próximos passos.", "Quero saber do Preparatório PISM",
              "Olá! Quero saber do Preparatório PISM do Quarks.", ("Ver notas de corte", "/nota-de-corte-pism/")))
    escrever("preparatorio-pism", titulo="Preparatório PISM em Juiz de Fora | Quarks Edu", sec="pgpism",
             descricao="Preparatório PISM presencial em Juiz de Fora, para os módulos I, II e III da UFJF: turmas de até 10 alunos, apostila própria, trilha do edital e notas de corte oficiais.",
             h1="Preparatório PISM em Juiz de Fora", selo="Presencial · até 10 por turma",
             lead="O ano todo ao lado do aluno, com foco no que mais cai na UFJF, nos três módulos do PISM.",
             ctas=botoes("Quero saber mais", "Olá! Quero saber do Preparatório PISM do Quarks.", ("Ver notas de corte", "/nota-de-corte-pism/")),
             numeros='<div class="pg-num"><div><b>200+</b><span>aprovados</span></div><div><b>10</b><span>alunos, no máximo, por turma</span></div><div><b>3</b><span>módulos: PISM I, II e III</span></div></div>',
             corpo=corpo, trilha=[("Preparatório PISM", "/preparatorio-pism/")], imagem="/site/img/curso-pism.webp", prioridade="0.9",
             schemas=[curso("Preparatório PISM (UFJF)", "Preparatório presencial em Juiz de Fora para os módulos I, II e III do PISM da UFJF, em turmas de até 10 alunos."), fs])

    # Preparatório IF Sudeste
    perguntas = [
        ("O Preparatório IF Sudeste do Quarks é presencial?", f"Sim, na {ENDERECO}, em turmas de até 10 alunos."),
        ("Quais matérias o preparatório cobre?", "Física, Química, Português e Matemática, com apostila própria e a trilha do IF no Portal Quarks."),
        ("Quantos pontos precisa para passar no IF Sudeste em Juiz de Fora?", 'Depende do curso e da modalidade. Na ampla concorrência de 2026, Desenvolvimento de Sistemas fechou em 70 de 90 pontos (35 acertos de 45). Veja <a href="/nota-de-corte-if-sudeste/">as notas de corte de todos os cursos integrados</a>.'),
        ("Como é a seleção do IF?", "Nos ingressos de 2023 a 2026 do campus Juiz de Fora, foi uma prova de 45 questões, cada uma valendo 2 pontos (até 90). As regras mudam de um ano para outro: confira sempre o edital do IF Sudeste MG do seu ano."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (
        bloco("Para entrar nos cursos técnicos integrados do IF", "<p>Os cursos técnicos integrados ao ensino médio do IF Sudeste MG, em Juiz de Fora, são disputados por quem está no 9º ano. "
              "O Preparatório IF Sudeste do Quarks prepara para a prova com <b>Física, Química, Português e Matemática</b>, apostila própria e a trilha do IF.</p>"
              '<div class="pg-foto"><img src="/site/img/curso-if.webp" alt="Aluno com IF escrito no braço" width="720" height="900" loading="lazy"></div>')
        + bloco("O que vem no Preparatório IF Sudeste", '<div class="pg-grade">'
                '<div class="pg-cartao"><b>Turmas pequenas</b><p>Até 10 alunos por turma, presencial em Juiz de Fora.</p></div>'
                '<div class="pg-cartao"><b>Apostila própria</b><p>Raio-X da prova, questões por nível e gabarito comentado.</p></div>'
                '<div class="pg-cartao"><b>Trilha do IF</b><p>Os conteúdos da prova na ordem certa, com treino e questões que caíram de verdade.</p></div>'
                '<div class="pg-cartao"><b>Família junto</b><p>No portal das famílias, presença, tarefas, simulados e trilha.</p></div></div>')
        + bloco("A trilha de estudos", TRILHA_PASSOS)
        + bloco("Aprovados no IF Sudeste", '<p>Alunos do Quarks aprovados no IF Sudeste em 2025 e 2026 em Desenvolvimento de Sistemas, Edificações, Eletromecânica, Eletrotécnica e Meio Ambiente. '
                'Veja <a href="/aprovados/">os aprovados</a> e <a href="/nota-de-corte-if-sudeste/">a nota de corte de cada curso</a>.</p>')
        + faq + bloco("Venha conhecer", VISITA, "pg-lilas")
        + cta("Comece o Preparatório IF Sudeste", "A coordenação do Quarks responde pelo WhatsApp com as turmas e os próximos passos.", "Quero saber do Preparatório IF",
              "Olá! Quero saber do Preparatório IF Sudeste do Quarks.", ("Ver notas de corte do IF", "/nota-de-corte-if-sudeste/")))
    escrever("preparatorio-if-sudeste", titulo="Preparatório IF Sudeste MG em Juiz de Fora | Quarks Edu", sec="pgif",
             descricao="Preparatório presencial em Juiz de Fora para a prova dos cursos técnicos integrados do IF Sudeste MG: Física, Química, Português e Matemática, turmas de até 10 alunos e apostila própria.",
             h1="Preparatório IF Sudeste MG em Juiz de Fora", selo="Presencial · até 10 por turma",
             lead="Física, Química, Português e Matemática, apostila própria e a trilha do IF, para entrar nos técnicos integrados.",
             ctas=botoes("Quero saber mais", "Olá! Quero saber do Preparatório IF Sudeste do Quarks.", ("Ver notas de corte do IF", "/nota-de-corte-if-sudeste/")),
             corpo=corpo, trilha=[("Preparatório IF Sudeste", "/preparatorio-if-sudeste/")], imagem="/site/img/curso-if.webp", prioridade="0.9",
             schemas=[curso("Preparatório IF Sudeste MG", "Preparatório presencial em Juiz de Fora para a prova dos cursos técnicos integrados do IF Sudeste MG: Física, Química, Português e Matemática."), fs])

    # Acompanhamento Escolar
    perguntas = [
        ("Como funciona o Acompanhamento Escolar do Quarks?", "Aulas de 1h30 de Física, Química, Matemática e Português, com no máximo 2 alunos por turma e o mesmo horário o ano todo. O professor acompanha a matéria da escola e já prepara para o PISM e o IF Sudeste."),
        ("Quais são os horários?", "De segunda a sexta: 14h às 15h30, 15h30 às 17h, 17h15 às 18h45 e 18h45 às 20h15. Sábado: 9h às 10h30 e 10h30 às 12h. As vagas são poucas por módulo."),
        ("Para quais anos é o Acompanhamento?", "Do 6º ano do ensino fundamental ao 3º ano do ensino médio."),
        ("Os pais acompanham?", "Sim. No portal das famílias você vê a presença, as tarefas, os simulados e a trilha, com cada número explicado."),
        ("Tem resultado?", "Todos os alunos que fizeram o Acompanhamento do Quarks ao longo de todo o ensino médio foram aprovados."),
    ]
    faq, fs = faq_html(perguntas)
    horarios = ('<div class="pg-tab"><table><thead><tr><th>Dia</th><th>Módulos de 1h30</th></tr></thead><tbody>'
                '<tr><td>Segunda a sexta</td><td>14h às 15h30 · 15h30 às 17h · 17h15 às 18h45 · 18h45 às 20h15</td></tr>'
                '<tr><td>Sábado</td><td>9h às 10h30 · 10h30 às 12h</td></tr></tbody></table></div>'
                '<p>O horário escolhido fica fixo o ano todo. As vagas são poucas por módulo.</p>')
    corpo = (
        bloco("O ano inteiro ao lado do seu filho", "<p>No Acompanhamento Escolar do Quarks, o aluno tem <b>Física, Química, Matemática e Português</b> toda semana, com <b>no máximo 2 alunos por turma</b> e o mesmo horário o ano todo. "
              "As aulas têm 1h30, tempo para explicar, praticar e tirar dúvida na mesma aula. O professor acompanha a matéria da escola e já prepara para o PISM e o IF Sudeste.</p>"
              "<p>O PISM é feito em três etapas, uma em cada ano do ensino médio. Estudando junto com a escola, o aluno fecha cada etapa sem dúvidas acumuladas e chega à prova confiante, sem correria de última hora.</p>"
              '<div class="pg-foto"><img src="/site/img/sala-pism.webp" alt="Sala de aula do Quarks em Juiz de Fora" width="960" height="540" loading="lazy"></div>')
        + bloco("Horários", horarios)
        + bloco("Os pais veem tudo, sem precisar perguntar", PAIS + "<p>Inclui a trilha de estudos no Portal Quarks, montada pelo edital da prova. No Acompanhamento Escolar, a trilha cobre só as disciplinas escolhidas na matrícula.</p>")
        + bloco("Resultado", "<p><b>100%:</b> todos os alunos que fizeram o Acompanhamento do Quarks ao longo de todo o ensino médio foram aprovados.</p>", "pg-lilas")
        + faq + bloco("Venha conhecer", VISITA)
        + cta("Garanta a vaga do seu filho", "Diga o ano escolar e as matérias. A coordenação do Quarks responde pelo WhatsApp com os horários livres.", "Quero conhecer o Acompanhamento",
              "Olá! Quero conhecer o Acompanhamento Escolar do Quarks."))
    escrever("acompanhamento-escolar", titulo="Acompanhamento e reforço escolar em Juiz de Fora | Quarks Edu", sec="pgacomp",
             descricao="Acompanhamento e reforço escolar em Juiz de Fora: Física, Química, Matemática e Português, aulas de 1h30 com no máximo 2 alunos, mesmo horário o ano todo, do 6º ano ao 3º do médio.",
             h1="Acompanhamento e reforço escolar em Juiz de Fora", selo="No máximo 2 alunos por turma",
             lead="Física, Química, Matemática e Português toda semana, no mesmo horário o ano todo. A aprovação vem como consequência.",
             ctas=botoes("Quero conhecer", "Olá! Quero conhecer o Acompanhamento Escolar do Quarks.", ("Ver horários", "#horarios")),
             numeros='<div class="pg-num"><div><b>1h30</b><span>cada aula</span></div><div><b>2</b><span>alunos, no máximo, por turma</span></div><div><b>100%</b><span>de aprovação de quem fez o médio todo</span></div></div>',
             corpo=corpo.replace('<section class="pg-bloco "><h2>Horários', '<section class="pg-bloco " id="horarios"><h2>Horários'),
             trilha=[("Acompanhamento Escolar", "/acompanhamento-escolar/")], prioridade="0.9",
             schemas=[servico("Acompanhamento Escolar", "Reforço e acompanhamento escolar em Juiz de Fora: Física, Química, Matemática e Português, aulas de 1h30 com no máximo 2 alunos."), fs])

    # Aula particular
    perguntas = [
        ("De quais matérias é a aula particular?", "Física, Química, Matemática ou Português."),
        ("Para que serve a aula avulsa?", "Para tirar dúvidas, revisar a matéria da escola ou se preparar para uma prova, quando precisar."),
        ("Onde é a aula?", f"Na {ENDERECO}."),
        ("Como agendar?", "Pelo WhatsApp (32) 99805-7212: diga a matéria, o conteúdo e os dias possíveis."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (bloco("Uma aula só sua, quando precisar", "<p>A aula avulsa do Quarks é uma aula particular, individual, de <b>Física, Química, Matemática ou Português</b>. "
                   "Serve para tirar dúvidas, revisar a matéria da escola ou se preparar para uma prova: o professor parte do que o aluno trouxer.</p>"
                   "<p>Para quem precisa de acompanhamento toda semana, o caminho é o <a href=\"/acompanhamento-escolar/\">Acompanhamento Escolar</a>, com no máximo 2 alunos e horário fixo.</p>"
                   '<div class="pg-foto"><img src="/site/img/aula-avulsa.webp" alt="Aula particular no Quarks" width="960" height="540" loading="lazy"></div>')
             + faq + bloco("Onde fica", VISITA, "pg-lilas")
             + cta("Agende a sua aula", "Diga a matéria e o conteúdo. O Quarks responde pelo WhatsApp com os horários.", "Agendar uma aula", "Olá! Quero agendar uma aula avulsa no Quarks."))
    escrever("aula-particular", titulo="Aula particular de Física, Química, Matemática e Português em Juiz de Fora | Quarks Edu", sec="pgavulsa",
             descricao="Aula particular em Juiz de Fora de Física, Química, Matemática ou Português, para tirar dúvidas, revisar a matéria da escola ou se preparar para uma prova.",
             h1="Aula particular em Juiz de Fora", selo="Individual · quando precisar",
             lead="Física, Química, Matemática ou Português, para tirar dúvidas, revisar a matéria da escola ou se preparar para uma prova.",
             ctas=botoes("Agendar uma aula", "Olá! Quero agendar uma aula avulsa no Quarks."), corpo=corpo,
             trilha=[("Aula particular", "/aula-particular/")], imagem="/site/img/aula-avulsa.webp", prioridade="0.8",
             schemas=[servico("Aula particular (aula avulsa)", "Aula particular individual de Física, Química, Matemática ou Português em Juiz de Fora."), fs])

    # Mentoria
    perguntas = [
        ("O que é a mentoria de estudos?", "Metas claras, um plano de estudo que cabe na rotina e encontros individuais ao longo do ano para acompanhar a evolução."),
        ("Para quem é?", "Para o aluno que quer organizar os estudos para o PISM, o IF Sudeste ou a escola e precisa de alguém acompanhando o plano."),
        ("Como começar?", "Fale com o Quarks pelo WhatsApp (32) 99805-7212."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (bloco("Estudar com plano", "<p>A mentoria do Quarks é individual: o aluno sai com <b>metas claras</b>, um <b>plano de estudo que cabe na rotina</b> e <b>encontros ao longo do ano</b> para acompanhar a evolução e ajustar o caminho.</p>"
                   '<p>Quem estuda para o PISM pode usar as <a href="/nota-de-corte-pism/">notas de corte</a> e o <a href="/simulador-pism/">simulador</a> para definir a meta de cada módulo.</p>'
                   '<div class="pg-foto"><img src="/site/img/mentoria.webp" alt="Mentoria de estudos no Quarks" width="960" height="540" loading="lazy"></div>')
             + faq + bloco("Onde fica", VISITA, "pg-lilas")
             + cta("Quero uma mentoria", "O Quarks responde pelo WhatsApp com os próximos passos.", "Quero uma mentoria", "Olá! Quero saber da Mentoria de estudos do Quarks."))
    escrever("mentoria-de-estudos", titulo="Mentoria de estudos em Juiz de Fora | Quarks Edu", sec="pgment",
             descricao="Mentoria de estudos individual em Juiz de Fora: metas claras, plano de estudo que cabe na rotina e encontros ao longo do ano, para o PISM, o IF Sudeste e a escola.",
             h1="Mentoria de estudos em Juiz de Fora", selo="Individual · encontros ao longo do ano",
             lead="Metas claras, um plano de estudo que cabe na rotina e encontros para acompanhar a evolução.",
             ctas=botoes("Quero uma mentoria", "Olá! Quero saber da Mentoria de estudos do Quarks."), corpo=corpo,
             trilha=[("Mentoria de estudos", "/mentoria-de-estudos/")], imagem="/site/img/mentoria.webp", prioridade="0.7",
             schemas=[servico("Mentoria de estudos", "Mentoria de estudos individual em Juiz de Fora, com metas, plano de estudo e encontros ao longo do ano."), fs])


def pagina_aprovados():
    h = open(os.path.join(RAIZ, "index.html"), encoding="utf-8").read()
    itens = re.findall(r'<figure class="apf".*?src="([^"]+)".*?<b data-f="f0">([^<]+)</b><span data-f="f1">([^<]+)</span>', h)
    figs = "".join(f'<figure><img src="/{e(s)}" alt="{e(n)}" width="352" height="440" loading="lazy"><figcaption><b>{e(n)}</b>{e(c)}</figcaption></figure>' for s, n, c in itens)
    corpo = (bloco("Eles escreveram no braço o curso que conquistaram", f"<p>Alguns dos alunos do Quarks aprovados na UFJF, na UFRJ e no IF Sudeste MG.</p><div class=\"pg-aprov\">{figs}</div>")
             + bloco("Qual é o seu curso?", '<p>Veja quanto cada curso pediu no <a href="/nota-de-corte-pism/">PISM</a> e no <a href="/nota-de-corte-if-sudeste/">IF Sudeste</a>, e faça a conta no <a href="/simulador-pism/">simulador</a>.</p>', "pg-lilas")
             + cta("O próximo pode ser você", "Conheça o Preparatório PISM, o Preparatório IF Sudeste e o Acompanhamento Escolar.", "Falar com o Quarks", "Olá! Vi os aprovados do Quarks e quero saber como estudar aí.",
                   ("Preparatório PISM", "/preparatorio-pism/")))
    escrever("aprovados", titulo="Aprovados do Quarks: UFJF, UFRJ e IF Sudeste MG | Quarks Edu",
             descricao="Alunos do Quarks Edu aprovados na UFJF (PISM), na UFRJ e no IF Sudeste MG. Mais de 200 aprovados em Juiz de Fora.",
             h1="Aprovados do Quarks", selo="200+ aprovados", lead="UFJF, UFRJ e IF Sudeste MG. Cada um escreveu no braço o curso que conquistou.",
             corpo=corpo, trilha=[("Aprovados", "/aprovados/")], imagem="/site/img/equipe-aprovados.webp", prioridade="0.7")


# ---------------------------------------------------------------------------------------------------------------
# guia do PISM e gabarito (Edital 10/2026 retificado pelos Editais 12 e 15/2026, e Resolução CONGRAD 340/2026)
# ---------------------------------------------------------------------------------------------------------------
EDITAL = "https://www2.ufjf.br/copese/2026/06/10/publicado-edital-do-pism-2027/"
RES340 = "https://www2.ufjf.br/copese/wp-content/uploads/sites/42/2026/06/SEI_3007081_ADM_Legislacao_002.01___Resolucao_340.pdf"
COPESE = "https://www2.ufjf.br/copese/vestibular-pism-2/"
DATAS = [("Provas de todos os módulos", "05 e 06/12/2026"), ("Gabaritos", "07/12/2026"), ("Recurso contra as provas", "08/12/2026 (9h às 16h)"),
         ("Gabarito final e notas do módulo III", "19/01/2027 (a partir das 15h)"), ("Recurso das notas do módulo III", "20/01/2027 (9h às 16h)"),
         ("Resultado final do módulo III", "04/02/2027 (a partir das 15h)"), ("Notas dos módulos I e II", "05/05/2027 (a partir das 15h)"),
         ("Recurso das notas dos módulos I e II", "06/05/2027 (9h às 16h)"), ("Resultado final dos módulos I e II", "25/05/2027 (a partir das 15h)")]
FONTE_EDITAL = (f'<p class="pg-fonte">Fontes: <a href="{EDITAL}" target="_blank" rel="noopener">Edital 10/2026 da Copese/UFJF (PISM 2027), retificado pelos Editais 12/2026 e 15/2026</a> '
                f'e <a href="{RES340}" target="_blank" rel="noopener">Resolução CONGRAD/UFJF 340/2026</a>. Conferido em 11/11/2026; vale sempre o que estiver no site da Copese.</p>')


def tabela_datas():
    return ('<div class="pg-tab"><table><thead><tr><th>Etapa</th><th>Data</th></tr></thead><tbody>'
            + "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td></tr>" for a, b in DATAS) + "</tbody></table></div>")


def paginas_pism():
    formato = ('<div class="pg-tab"><table><thead><tr><th>Módulo</th><th>1º dia</th><th>2º dia</th><th>Vale</th></tr></thead><tbody>'
               '<tr><td><b>PISM I e PISM II</b></td><td>20 objetivas (5 de Língua Portuguesa, Matemática, Geografia e Química) e 8 discursivas (2 de cada)</td>'
               '<td>20 objetivas (5 de Literatura, Biologia, Física e História) e 8 discursivas (2 de cada)</td><td>120 pontos</td></tr>'
               '<tr><td><b>PISM III</b></td><td>20 objetivas (5 de Língua Portuguesa, Matemática, Literatura e Biologia) e 10 discursivas da área do curso</td>'
               '<td>20 objetivas (5 de Física, Química, Geografia e História) e 10 discursivas da área do curso</td><td>140 pontos</td></tr>'
               '</tbody></table></div>'
               '<p>Cada objetiva vale 1 ponto e cada discursiva, até 5. As provas duram no máximo 4 horas.</p>')
    areas = ('<div class="pg-tab"><table><thead><tr><th>Área do curso</th><th>Discursivas do 1º dia</th><th>Discursivas do 2º dia</th></tr></thead><tbody>'
             '<tr><td>Exatas</td><td>5 de Língua Portuguesa e 5 de Matemática</td><td>5 de Física e 5 de Química</td></tr>'
             '<tr><td>Saúde</td><td>5 de Língua Portuguesa e 5 de Biologia</td><td>5 de Física e 5 de Química</td></tr>'
             '<tr><td>Economia e Administração</td><td>4 de Língua Portuguesa, 4 de Matemática e 2 de Sociologia</td><td>4 de Geografia, 4 de História e 2 de Filosofia</td></tr>'
             '<tr><td>Humanas</td><td>4 de Língua Portuguesa, 4 de Literatura e 2 de Sociologia</td><td>4 de Geografia, 4 de História e 2 de Filosofia</td></tr>'
             '</tbody></table></div>')
    perguntas = [
        ("Quando é o PISM 2027?", "As provas dos três módulos são em 05 e 06/12/2026, e os gabaritos saem em 07/12/2026."),
        ("Como é calculada a nota final do PISM?", "Pela Resolução CONGRAD 340/2026: Nota Final = PISM I × 0,20 + PISM II × 0,30 + PISM III × 0,50. Nos resultados, a UFJF mostra as notas com peso 2, 3 e 5 (até 240, 360 e 700 pontos, total de 1.300), que é a mesma proporção."),
        ("Quem pode fazer o PISM I?", "Quem está matriculado na 1ª série do ensino médio (ou na 2ª série de técnico de 4 anos, ou na EJA). Quem já concluiu o ensino médio não pode se inscrever no PISM I."),
        ("Quando escolho o curso?", "Só na inscrição do módulo III. É nela também que se escolhe o grupo de cotas."),
        ("Onde são as provas?", "Em Juiz de Fora, Governador Valadares e Muriaé (MG), e em Petrópolis e Três Rios (RJ)."),
        ("Quanto custa a inscrição?", "R$ 150,00 no PISM 2027, com isenção para quem tem direito, nas datas do edital."),
        ("Quem perde o PISM?", "Quem faltar a qualquer prova do módulo em que está inscrito, ou tirar zero em algum conteúdo somando os três módulos do triênio."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (
        bloco("O que é o PISM", "<p>O <b>PISM (Programa de Ingresso Seletivo Misto)</b> é o vestibular seriado da Universidade Federal de Juiz de Fora (UFJF). O aluno faz uma prova por ano do ensino médio:</p>"
              "<ul><li><b>PISM I:</b> conteúdo do 1º ano;</li><li><b>PISM II:</b> conteúdo do 1º e do 2º ano;</li><li><b>PISM III:</b> conteúdo dos três anos.</li></ul>"
              "<p>A nota final soma os três módulos, com peso maior a cada ano. Por isso o PISM I e o PISM II contam muito: são 46% da nota final. "
              "No PISM 2027, as provas valem para o triênio 2026-2028 (módulo I), 2025-2027 (módulo II) e 2024-2026 (módulo III).</p>")
        + bloco("Datas do PISM 2027", tabela_datas() + FONTE_EDITAL)
        + bloco("Como é a prova", formato + "<h3>Discursivas do PISM III, por área</h3>" + areas + FONTE_EDITAL)
        + bloco("Como se calcula a nota", "<p>Pela Resolução CONGRAD 340/2026: <b>Nota Final = PISM I × 0,20 + PISM II × 0,30 + PISM III × 0,50</b>.</p>"
                "<p>Nos resultados, a UFJF mostra as notas com peso: o PISM I vale até 120 pontos e entra com peso 2 (até 240), o PISM II vale até 120 e entra com peso 3 (até 360), e o PISM III vale até 140 e entra com peso 5 (até 700). O total vai até <b>1.300</b>. É nessa escala que saem as notas de corte.</p>"
                "<p>Exemplo: 80 no PISM I, 85 no PISM II e 100 no PISM III dão 80 × 2 + 85 × 3 + 100 × 5 = 160 + 255 + 500 = <b>915 pontos</b>.</p>"
                '<p>Faça a sua conta no <a href="/simulador-pism/">simulador do PISM</a>.</p>')
        + bloco("Vagas e cotas", "<p>No módulo III, pelo menos 50% das vagas de cada curso ficam reservadas para quem estudou em escola pública, divididas em 10 grupos de cotas (A a J; a ampla concorrência é o grupo C). "
                "Quem está num grupo de cotas concorre primeiro na ampla. O candidato do PISM também pode concorrer pelo Sisu.</p>" + FONTE_EDITAL)
        + bloco("Quanto cada curso pede", '<p>Veja a <a href="/nota-de-corte-pism/">nota de corte de todos os cursos da UFJF em Juiz de Fora</a>, ano a ano desde 2019 e por grupo de cotas.</p>'
                '<ul class="pg-links">' + "".join(f'<li><a href="/nota-de-corte-pism/{s}/">{e(n)}</a></li>' for s, n in DESTAQUES) + "</ul>", "pg-lilas")
        + faq
        + cta("Prepare-se para o PISM com o Quarks", "Preparatório presencial em Juiz de Fora para os três módulos, em turmas de até 10 alunos.", "Quero saber do Preparatório PISM",
              "Olá! Li o guia do PISM e quero saber do Preparatório PISM do Quarks.", ("Ver o Preparatório PISM", "/preparatorio-pism/")))
    escrever("pism", titulo="PISM 2027 (UFJF): datas, como é a prova, nota e cotas | Guia do Quarks",
             descricao="Guia do PISM 2027 da UFJF: provas em 05 e 06/12/2026, gabarito em 07/12, resultado do módulo III em 04/02/2027, como é a prova, como calcular a nota e as cotas.",
             h1="PISM 2027: o guia completo", selo="Atualizado em 11/11/2026",
             lead="Datas, como é a prova de cada módulo, como a UFJF calcula a nota e como funcionam as cotas, conferido no edital da Copese.",
             ctas=f'<div class="pg-ctas"><a class="btn am" href="/nota-de-corte-pism/">Ver notas de corte</a><a class="pg-bt2" href="/simulador-pism/">Simular minha nota</a></div>',
             numeros='<div class="pg-num"><div><b>05 e 06/12</b><span>provas do PISM 2027</span></div><div><b>07/12</b><span>gabaritos</span></div><div><b>04/02/2027</b><span>resultado do módulo III</span></div></div>',
             corpo=corpo, trilha=[("Guia do PISM", "/pism/")], prioridade="0.9",
             schemas=[fs, {"@type": "Article", "headline": "PISM 2027: o guia completo", "author": ORG, "publisher": ORG, "dateModified": HOJE, "inLanguage": "pt-BR"}])

    perguntas = [
        ("Quando sai o gabarito do PISM 2027?", "A Copese divulga os gabaritos em 07/12/2026, no dia seguinte às provas (05 e 06/12/2026)."),
        ("Onde vejo o gabarito oficial?", f'No site da Copese/UFJF, na página do PISM 2027.'),
        ("Posso entrar com recurso?", "Sim, em 08/12/2026, das 9h às 16h, pelo site da Copese."),
        ("Quando saem as notas?", "O gabarito final e as notas do módulo III saem em 19/01/2027 e o resultado final do módulo III em 04/02/2027. As notas dos módulos I e II saem em 05/05/2027."),
        ("Como sei se a minha nota dá para o meu curso?", 'Compare com a <a href="/nota-de-corte-pism/">nota de corte de cada curso</a> e use o <a href="/simulador-pism/">simulador do PISM</a>.'),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (
        bloco("Quando sai o gabarito", "<p>As provas do PISM 2027 são em <b>05 e 06/12/2026</b>, para os três módulos. A Copese/UFJF divulga os <b>gabaritos em 07/12/2026</b> no site oficial, e o recurso contra as questões vai até 08/12/2026.</p>"
              f'<p>O gabarito oficial fica no <a href="{COPESE}" target="_blank" rel="noopener">site da Copese</a>. Esta página do Quarks é atualizada assim que ele sair, com o link direto.</p>')
        + bloco("Calendário depois da prova", tabela_datas() + FONTE_EDITAL)
        + bloco("Confira a sua nota", "<p>Com o gabarito, conte as objetivas certas de cada dia (cada uma vale 1 ponto). As discursivas valem até 5 pontos cada e só aparecem nas notas oficiais.</p>"
                '<p>Depois, leve a nota para a escala da UFJF (peso 2 no PISM I, 3 no PISM II e 5 no PISM III) no <a href="/simulador-pism/">simulador do PISM</a> e compare com a <a href="/nota-de-corte-pism/">nota de corte do seu curso</a>.</p>', "pg-lilas")
        + faq
        + cta("Próximo módulo começa agora", "Quem faz o PISM I ou o PISM II em dezembro já pode começar o próximo módulo com o Quarks, presencial em Juiz de Fora.", "Quero saber do Preparatório PISM",
              "Olá! Fiz o PISM e quero saber do Preparatório PISM do Quarks.", ("Guia do PISM 2027", "/pism/")))
    escrever("gabarito-pism-2027", titulo="Gabarito do PISM 2027: data e onde conferir | Quarks Edu",
             descricao="Gabarito do PISM 2027 da UFJF: as provas são em 05 e 06/12/2026 e a Copese divulga os gabaritos em 07/12/2026. Veja o calendário de recursos, notas e resultado.",
             h1="Gabarito do PISM 2027", selo="Gabaritos em 07/12/2026",
             lead="As provas são em 05 e 06/12/2026 e a Copese divulga os gabaritos em 07/12/2026. Veja o que vem depois e como conferir a sua nota.",
             ctas=f'<div class="pg-ctas"><a class="btn am" href="{COPESE}" target="_blank" rel="noopener">Site da Copese</a><a class="pg-bt2" href="/nota-de-corte-pism/">Notas de corte</a></div>',
             corpo=corpo, trilha=[("Guia do PISM", "/pism/"), ("Gabarito do PISM 2027", "/gabarito-pism-2027/")], prioridade="0.8",
             schemas=[fs])


# ---------------------------------------------------------------------------------------------------------------
# notas de corte (Banco de notas da gestão)
# ---------------------------------------------------------------------------------------------------------------
ACENTO = {"ADMINISTRACAO": "Administração", "CIENCIA": "Ciência", "CIENCIAS": "Ciências", "COMPUTACAO": "Computação", "ECONOMICAS": "Econômicas", "CONTABEIS": "Contábeis",
          "BIOLOGICAS": "Biológicas", "EDUCACAO": "Educação", "FISICA": "Física", "FARMACIA": "Farmácia", "ELETRICA": "Elétrica", "MECANICA": "Mecânica", "PRODUCAO": "Produção",
          "QUIMICA": "Química", "MATEMATICA": "Matemática", "ESTATISTICA": "Estatística", "HISTORIA": "História", "MUSICA": "Música", "RADIO": "Rádio", "RELIGIAO": "Religião",
          "SANITARIA": "Sanitária", "INFORMACAO": "Informação", "SERVICO": "Serviço", "NUTRICAO": "Nutrição", "VETERINARIA": "Veterinária", "ROBOTICA": "Robótica",
          "AUTOMACAO": "Automação", "POTENCIA": "Potência", "ELETRONICOS": "Eletrônicos", "TELECOMUNICACOES": "Telecomunicações", "TV": "TV", "BACHARELADO": "Bacharelado",
          "LICENCIATURA": "Licenciatura", "LIBRAS": "Libras"}
PEQ = {"de", "da", "do", "das", "dos", "e", "em", "integral", "noturno", "vespertino", "diurno", "matutino"}


def nome_curso(s):
    partes = re.split(r"(\s+|-|\(|\)|/|,)", s.lower())
    out = []
    for i, w in enumerate(partes):
        if not re.search(r"[a-z]", w):
            out.append(w); continue
        U = w.upper()
        if U in ACENTO: out.append(ACENTO[U])
        elif w in PEQ and i: out.append(w)
        else: out.append(w[:1].upper() + w[1:])
    return "".join(out).replace("Bacharelado Interdisciplinar", "Bacharelado Interdisciplinar")


def nome_curto(s):
    """Medicina (integral) -> Medicina; usado em títulos curtos"""
    return re.sub(r"\s*\([^)]*\)\s*$", "", nome_curso(s))


DESTAQUES = []   # preenchido em paginas_notas (links do guia do PISM)


def paginas_notas(gestao):
    d = json.load(open(os.path.join(gestao, "bancodenotas", "pism.json"), encoding="utf-8"))
    rot_novos, rot_antigos = d["grupos"]["novos"], d["grupos"]["antigos"]
    pesos = {1: 2, 2: 3, 3: 5}
    cursos = []
    for c in d["cursos"]:
        slug = re.sub(r"^juiz-de-fora-", "", c["id"])
        assert re.fullmatch(r"[a-z0-9-]+", slug), slug
        C = c["g"].get("C") or {}
        cortes = {int(a): v for a, v in (C.get("cortes") or {}).items() if v is not None}
        ult = max(cortes) if cortes else None
        cursos.append(dict(c=c, slug=slug, nome=nome_curso(c["k"]), curto=nome_curto(c["k"]), C=C, cortes=cortes, ult=ult))
    assert len({x["slug"] for x in cursos}) == len(cursos)
    anos_todos = sorted({a for x in cursos for a in x["c"]["anos"]})
    ano_max = max(anos_todos)
    fonte = (f'<p class="pg-fonte">Fonte: {e(d["fonte"])}. Ponto de corte = pontuação mínima de quem entrou nas vagas, no resultado final do PISM III. '
             f'Notas com peso (módulo I × 2, II × 3, III × 5; total até 1.300). Só números agregados, sem nome de ninguém. Banco de notas do Quarks, atualizado em {e(d["gerado"])}.</p>')

    # destaques para o guia (os 12 cortes mais altos do último ano)
    top = sorted([x for x in cursos if x["ult"] == ano_max], key=lambda x: -x["cortes"][ano_max])
    DESTAQUES[:] = [(x["slug"], x["nome"]) for x in top[:12]]
    medicina = next((x for x in cursos if x["slug"] == "medicina-integral"), None)

    def rot_grupo(g):
        return rot_novos.get(g) or rot_antigos.get(g) or g

    def ordem_grupos(gs):
        pref = ["C", "A", "B", "D", "E", "F", "G", "H", "I", "J", "A1", "B1", "D1", "E1"]
        return sorted(gs, key=lambda g: pref.index(g) if g in pref else 99)

    for x in cursos:
        c, C, nome, curto = x["c"], x["C"], x["nome"], x["curto"]
        anos = sorted(c["anos"])
        ult = x["ult"]
        mesmos = [y for y in cursos if y["c"]["area"] == c["area"] and y is not x][:10]
        # tabela de cortes por grupo e ano
        cab = "".join(f'<th{DEST if a == ano_max else ""}>PISM {a}</th>' for a in anos)
        linhas = []
        for g in ordem_grupos(c["g"].keys()):
            G = c["g"][g]; ct = G.get("cortes") or {}
            if not any(ct.get(str(a)) is not None for a in anos):
                continue
            celulas = "".join(f'<td{DEST if a == ano_max else ""}>{br(ct.get(str(a)))}</td>' for a in anos)
            linhas.append(f'<tr><td><b>{e(g)}</b> · {e(rot_grupo(g))}</td>{celulas}</tr>')
        tab_grupos = f'<div class="pg-tab"><table><thead><tr><th>Grupo</th>{cab}</tr></thead><tbody>{"".join(linhas)}</tbody></table></div>'
        # vagas da ampla
        vag = C.get("vagas") or {}
        tab_ampla = ""
        if x["cortes"]:
            tab_ampla = ('<div class="pg-tab"><table><thead><tr><th>Edição</th><th>Nota de corte (ampla)</th><th>Vagas na ampla</th></tr></thead><tbody>'
                         + "".join(f'<tr><td>PISM {a}</td><td{DEST if a == ano_max else ""}>{br(x["cortes"].get(a))}</td><td>{br(vag.get(str(a)), 0) if vag.get(str(a)) is not None else "—"}</td></tr>' for a in sorted(x["cortes"], reverse=True))
                         + "</tbody></table></div>")
        # quem passou (só com 5 ou mais aprovados: regra do Banco de notas)
        ap = C.get("aprovados") or {}
        bloco_ap = ""
        if ap.get("n", 0) >= 5 and ap.get("m1"):
            lin = ""
            for m, rot, mx in ((1, "PISM I (peso 2)", 240), (2, "PISM II (peso 3)", 360), (3, "PISM III (peso 5)", 700)):
                s = ap.get(f"m{m}") or {}
                lin += f'<tr><td>{rot}</td><td>{br(s.get("media", 0) * pesos[m])}</td><td>{br(s.get("min", 0) * pesos[m])}</td><td>até {mx}</td></tr>'
            t = ap.get("t") or {}
            lin += f'<tr><td><b>Total</b></td><td><b>{br(t.get("media"))}</b></td><td><b>{br(t.get("min"))}</b></td><td>até 1.300</td></tr>'
            bloco_ap = bloco(f"Quanto tiraram os aprovados em {curto}",
                             f'<p>Notas, com peso, dos {ap["n"]} aprovados na ampla concorrência de {e(", ".join(ap.get("anos", [])[:1]))} a {e(ap.get("anos", [""])[-1])}: a média de cada módulo e a menor nota de quem entrou.</p>'
                             f'<div class="pg-tab"><table><thead><tr><th>Módulo</th><th>Média de quem passou</th><th>Menor nota de quem passou</th><th>Máximo</th></tr></thead><tbody>{lin}</tbody></table></div>'
                             "<p>Use como meta: quem chega ao PISM III perto da média dos aprovados nos módulos I e II entra na disputa com folga.</p>")
        # textos
        if ult:
            resumo = (f"No PISM {ult}, a nota de corte de <b>{e(nome)}</b> na UFJF (Juiz de Fora), na ampla concorrência, foi de <b>{br(x['cortes'][ult])} pontos</b> de 1.300"
                      + (f", com {br(vag.get(str(ult)), 0)} vagas na ampla" if vag.get(str(ult)) else "") + ".")
            if C.get("media2") is not None:
                resumo += f" A média dos {len(C.get('anos2') or [])} últimos anos foi {br(C['media2'])}"
                resumo += f", e nos últimos {len(C.get('anos6') or [])} anos a nota variou de {br(C.get('menor'))} a {br(C.get('maior'))}." if C.get("menor") is not None else "."
            desc = f"Nota de corte de {nome} no PISM da UFJF: {br(x['cortes'][ult])} pontos na ampla concorrência em {ult}. Veja todos os anos desde {min(x['cortes'])}, por grupo de cotas, vagas e quanto tiraram os aprovados."
        else:
            resumo = f"Este curso não teve ponto de corte na ampla concorrência nas edições do Banco de notas. Veja abaixo os grupos que tiveram."
            desc = f"Notas de corte de {nome} no PISM da UFJF por grupo de cotas e ano, com as notas oficiais da Copese."
        if ult and ult < ano_max:
            resumo += f" O último ano com este curso no PISM foi {ult}."
        perguntas = []
        if ult:
            perguntas.append((f"Qual foi a nota de corte de {nome} no PISM {ult}?", f"Na ampla concorrência, {br(x['cortes'][ult])} pontos, de 1.300 (resultado final do PISM III da UFJF)."))
        if C.get("media2") is not None:
            perguntas.append((f"Quanto preciso tirar no PISM para passar em {nome}?", f"Como referência, a média dos {len(C.get('anos2') or [])} últimos anos na ampla foi {br(C['media2'])} pontos de 1.300. Cada ano tem a sua prova e a sua concorrência, então mire acima disso. Faça a conta módulo a módulo no simulador do PISM."))
        if vag.get(str(ult)) if ult else None:
            perguntas.append((f"Quantas vagas {nome} tem no PISM?", f"No PISM {ult}, foram {br(vag[str(ult)], 0)} vagas na ampla concorrência, além das vagas dos grupos de cotas (no mínimo 50% das vagas do curso são para escola pública)."))
        perguntas.append(("Como é calculada a nota do PISM?", "Nota final = PISM I × 0,20 + PISM II × 0,30 + PISM III × 0,50 (Resolução CONGRAD 340/2026). A UFJF publica as notas com peso 2, 3 e 5, num total de até 1.300 pontos."))
        faq, fs = faq_html(perguntas)
        corpo = (
            bloco(f"Nota de corte de {nome} no PISM", f"<p>{resumo}</p>" + tab_ampla + fonte)
            + bloco("Simule a sua nota", f'<p>Escolha <b>Meu curso (PISM III)</b>, depois {e(nome)} e o seu grupo, e veja quanto precisa em cada módulo que falta.</p><div id="simulador-quarks" style="margin-top:14px"></div>', "pg-lilas")
            + bloco_ap
            + bloco("Por grupo de cotas", "<p>Ponto de corte de cada grupo, ano a ano. Desde o PISM 2025 os grupos mudaram (Lei 14.723/2023 e Resolução CONSU 120/2024): a renda passou de até 1,5 para até 1 salário mínimo por pessoa, e surgiram os grupos G a J. As letras de antes e de depois não são exatamente iguais.</p>" + tab_grupos + fonte)
            + faq
            + (bloco(f"Outros cursos de {e(c['area'])}", '<ul class="pg-links">' + "".join(f'<li><a href="/nota-de-corte-pism/{y["slug"]}/">{e(y["nome"])}</a></li>' for y in mesmos) + '</ul><p style="margin-top:12px"><a href="/nota-de-corte-pism/">Ver todos os cursos</a></p>') if mesmos else "")
            + cta(f"Rumo a {curto}", "O Preparatório PISM do Quarks acompanha os três módulos, presencial em Juiz de Fora, em turmas de até 10 alunos.", "Quero saber do Preparatório PISM",
                  f"Olá! Vi a nota de corte de {nome} no site e quero saber do Preparatório PISM do Quarks.", ("Ver o Preparatório PISM", "/preparatorio-pism/")))
        dataset = {"@type": "Dataset", "name": f"Notas de corte de {nome} no PISM da UFJF", "description": desc + " Dados agregados do resultado final do PISM III (UFJF/Copese), sem nome de candidatos.",
                   "creator": ORG, "isBasedOn": COPESE, "temporalCoverage": f"{min(anos)}/{max(anos)}", "spatialCoverage": {"@type": "Place", "name": "Juiz de Fora, MG"},
                   "inLanguage": "pt-BR", "isAccessibleForFree": True, "dateModified": HOJE}
        tit = f"Nota de corte de {nome} no PISM {ult or ano_max} (UFJF) | Quarks Edu"
        escrever(f"nota-de-corte-pism/{x['slug']}", titulo=tit, descricao=desc, h1=f"Nota de corte de {nome} no PISM",
                 selo=f"UFJF · Juiz de Fora · {c['area']}", lead=f"Ano a ano desde o PISM {min(anos)}, por grupo de cotas, com as notas oficiais da UFJF.",
                 numeros=(f'<div class="pg-num"><div><b>{br(x["cortes"][ult])}</b><span>corte na ampla, PISM {ult}</span></div>'
                          + (f'<div><b>{br(C["media2"])}</b><span>média dos 2 últimos anos</span></div>' if C.get("media2") is not None else "")
                          + (f'<div><b>{br(vag.get(str(ult)), 0)}</b><span>vagas na ampla em {ult}</span></div>' if vag.get(str(ult)) else "") + "</div>") if ult else "",
                 corpo=corpo, trilha=[("Notas de corte do PISM", "/nota-de-corte-pism/"), (nome, f"/nota-de-corte-pism/{x['slug']}/")],
                 scripts=simulador_js("pism3"), prioridade="0.7", schemas=[fs, dataset])

    # índice
    por_area = {}
    for x in cursos:
        por_area.setdefault(x["c"]["area"], []).append(x)
    linhas = []
    for area in sorted(por_area):
        linhas.append(f'<tr class="grp"><td colspan="4">{e(area)}</td></tr>')
        for x in sorted(por_area[area], key=lambda y: y["nome"]):
            C, ult = x["C"], x["ult"]
            v = (C.get("vagas") or {}).get(str(ult)) if ult else None
            linhas.append(f'<tr data-busca="{e(x["nome"].lower())}"><td><a href="/nota-de-corte-pism/{x["slug"]}/">{e(x["nome"])}</a></td>'
                          f'<td class="dest">{br(x["cortes"][ult]) + ("" if ult == ano_max else f" ({ult})") if ult else "—"}</td>'
                          f'<td>{br(C.get("media2"))}</td><td>{br(v, 0) if v is not None else "—"}</td></tr>')
    tabela = (f'<input class="pg-filtro" type="search" placeholder="Procure o curso (ex.: medicina, direito)" aria-label="Procurar curso" data-filtro>'
              f'<div class="pg-tab"><table data-tabela><thead><tr><th>Curso</th><th class="dest">Corte PISM {ano_max} (ampla)</th><th>Média 2 últimos anos</th><th>Vagas na ampla</th></tr></thead><tbody>{"".join(linhas)}</tbody></table></div>')
    filtro = """<script>(function(){var i=document.querySelector('[data-filtro]');if(!i)return;i.addEventListener('input',function(){var q=i.value.trim().toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');document.querySelectorAll('[data-tabela] tbody tr').forEach(function(t){if(t.classList.contains('grp')){t.hidden=!!q;return;}var s=(t.dataset.busca||'').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');t.hidden=q&&s.indexOf(q)<0;});});})();</script>"""
    top10 = "".join(f'<tr><td><a href="/nota-de-corte-pism/{x["slug"]}/">{e(x["nome"])}</a></td><td class="dest">{br(x["cortes"][ano_max])}</td></tr>' for x in top[:10])
    perguntas = [
        (f"Qual é a nota de corte de Medicina no PISM {ano_max}?", f"Na ampla concorrência, {br(medicina['cortes'][ano_max])} pontos de 1.300 (UFJF, Juiz de Fora)." if medicina and medicina["ult"] == ano_max else "Veja a página de Medicina."),
        ("O que é a nota de corte do PISM?", "É a menor pontuação de quem entrou nas vagas de um curso e grupo, no resultado final do PISM III. Ela muda todo ano, com a prova e a concorrência."),
        ("Como é calculada a nota do PISM?", "Nota final = PISM I × 0,20 + PISM II × 0,30 + PISM III × 0,50 (Resolução CONGRAD 340/2026). A UFJF publica com peso 2, 3 e 5, num total de até 1.300."),
        ("De onde vêm esses números?", "Do resultado final e das notas do PISM III publicados pela Copese/UFJF em cada edição, conferidos pelo Quarks. Só números agregados, sem nome de ninguém."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (
        bloco(f"Os cursos com nota de corte mais alta no PISM {ano_max}", f'<div class="pg-tab"><table><thead><tr><th>Curso</th><th class="dest">Corte na ampla</th></tr></thead><tbody>{top10}</tbody></table></div>')
        + bloco(f"Nota de corte de todos os cursos ({len(cursos)})", "<p>Clique no curso para ver todos os anos, cada grupo de cotas, as vagas e quanto tiraram os aprovados em cada módulo.</p>" + tabela + fonte)
        + bloco("Simule a sua nota", '<p>Digite as suas notas e veja onde você estaria entre quem fez o PISM e quanto falta para o curso que você quer.</p><p style="margin-top:14px"><a class="btn am" href="/simulador-pism/">Abrir o simulador</a></p>', "pg-lilas")
        + faq
        + cta("Do corte à aprovação", "O Preparatório PISM do Quarks acompanha os três módulos, presencial em Juiz de Fora.", "Quero saber do Preparatório PISM",
              "Olá! Vi as notas de corte do PISM no site e quero saber do Preparatório PISM do Quarks.", ("Guia do PISM 2027", "/pism/")))
    escrever("nota-de-corte-pism", titulo=f"Nota de corte do PISM {ano_max} (UFJF): todos os cursos de Juiz de Fora | Quarks Edu",
             descricao=f"Nota de corte do PISM da UFJF em todos os {len(cursos)} cursos de Juiz de Fora, de {min(anos_todos)} a {ano_max}, na ampla e em cada grupo de cotas, com as notas oficiais da Copese.",
             h1=f"Nota de corte do PISM: todos os cursos da UFJF", selo=f"PISM {min(anos_todos)} a {ano_max} · notas oficiais",
             lead=f"A nota de corte de cada curso de Juiz de Fora, ano a ano e por grupo de cotas, com as notas oficiais da UFJF.",
             numeros=f'<div class="pg-num"><div><b>{len(cursos)}</b><span>cursos de Juiz de Fora</span></div><div><b>{len(anos_todos)}</b><span>edições ({min(anos_todos)} a {ano_max})</span></div><div><b>1.300</b><span>pontos possíveis</span></div></div>',
             corpo=corpo, trilha=[("Notas de corte do PISM", "/nota-de-corte-pism/")], scripts=filtro, prioridade="0.9",
             schemas=[fs, {"@type": "Dataset", "name": f"Notas de corte do PISM (UFJF), Juiz de Fora, {min(anos_todos)} a {ano_max}",
                           "description": f"Pontos de corte de {len(cursos)} cursos da UFJF em Juiz de Fora no PISM, por edição e grupo de cotas, a partir do resultado final do PISM III publicado pela Copese/UFJF. Só números agregados.",
                           "creator": ORG, "isBasedOn": COPESE, "temporalCoverage": f"{min(anos_todos)}/{ano_max}", "inLanguage": "pt-BR", "isAccessibleForFree": True, "dateModified": HOJE}])
    return cursos


def paginas_if(gestao):
    d = json.load(open(os.path.join(gestao, "bancodenotas", "if.json"), encoding="utf-8"))
    anos = d["anos"]
    MOD = {"AC": "Ampla concorrência", "LB-EP": "Escola pública, renda até 1 salário", "LB-PPI": "Escola pública, renda até 1 salário, PPI", "LB-Q": "Escola pública, renda até 1 salário, quilombola",
           "LB-PCD": "Escola pública, renda até 1 salário, com deficiência", "LI-EP": "Escola pública, qualquer renda", "LI-PPI": "Escola pública, qualquer renda, PPI",
           "LI-Q": "Escola pública, qualquer renda, quilombola", "LI-PCD": "Escola pública, qualquer renda, com deficiência", "PCD": "Pessoa com deficiência",
           "L1": "L1 (até 2024): escola pública, renda até 1,5 salário", "L2": "L2 (até 2024): L1 e PPI", "L5": "L5 (até 2024): escola pública, qualquer renda", "L6": "L6 (até 2024): L5 e PPI",
           "L9": "L9 (até 2024): L1 com deficiência", "L10": "L10 (até 2024): L2 com deficiência", "L13": "L13 (até 2024): L5 com deficiência", "L14": "L14 (até 2024): L6 com deficiência", "PRONAF": "PRONAF"}
    ORD = ["AC", "LB-EP", "LB-PPI", "LB-Q", "LB-PCD", "LI-EP", "LI-PPI", "LI-Q", "LI-PCD", "PCD", "PRONAF", "L1", "L2", "L5", "L6", "L9", "L10", "L13", "L14"]
    blocos, resumo = [], []
    for c in d["cursos"]:
        ac = c["mod"].get("AC") or {}
        ct = ac.get("cortes") or {}
        ult = max((int(a) for a in ct), default=None)
        if ult:
            resumo.append(f'<tr><td><a href="#{e(c["id"])}">{e(c["curso"])}</a></td>' + "".join(f'<td{DEST if a == max(anos) else ""}>{br(ct.get(str(a)))}</td>' for a in anos)
                          + f'<td>{br(ac.get("media2"))}</td><td>{int(round(ac["media2"] / 2)) if ac.get("media2") else "—"}</td></tr>')
        linhas = ""
        for m in sorted(c["mod"], key=lambda k: ORD.index(k) if k in ORD else 99):
            M = c["mod"][m]; cm = M.get("cortes") or {}
            if not any(cm.get(str(a)) is not None for a in anos):
                continue
            linhas += f'<tr><td><b>{e(m)}</b> · {e(MOD.get(m, m))}</td>' + "".join(f'<td{DEST if a == max(anos) else ""}>{br(cm.get(str(a)))}</td>' for a in anos) + "</tr>"
        cham = ac.get("chamada") or {}
        txt_cham = (" Nas chamadas seguintes da ampla, a menor nota chamada foi " + " e ".join(f"{br(v)} em {a}" for a, v in sorted(cham.items())) + ".") if cham else ""
        vag = (ac.get("vagas") or {}).get(str(max(anos)))
        txt = (f"<p>Na ampla concorrência de {ult}, o último classificado de <b>{e(c['curso'])}</b> fez <b>{br(ct[str(ult)])} pontos</b> de 90 ({int(round(ct[str(ult)] / 2))} acertos de 45)"
               + (f", com {vag} vagas na ampla" if vag else "") + f".{txt_cham}</p>") if ult else ""
        blocos.append(f'<section class="pg-bloco" id="{e(c["id"])}"><h2>Nota de corte de {e(c["curso"])} no IF Sudeste MG</h2>{txt}'
                      f'<div class="pg-tab"><table><thead><tr><th>Modalidade</th>' + "".join(f'<th{DEST if a == max(anos) else ""}>{a}</th>' for a in anos)
                      + f'</tr></thead><tbody>{linhas}</tbody></table></div></section>')
    fonte = f'<p class="pg-fonte">Fonte: {e(d["fonte"])}. Nota do último classificado em cada curso e modalidade, de 0 a 90. Só números agregados, sem nome de ninguém.</p>'
    perguntas = [
        ("Quantos pontos precisa para passar no IF Sudeste em Juiz de Fora?", "Depende do curso e da modalidade. Na ampla concorrência, os cortes de 2023 a 2026 ficaram entre os valores da tabela desta página; divida por 2 para saber os acertos de 45."),
        ("Como foi a prova do IF nesses anos?", "Nos ingressos de 2023 a 2026 do campus Juiz de Fora, a seleção dos técnicos integrados foi uma prova de 45 questões, cada uma valendo 2 pontos (de 0 a 90). Confira sempre o edital do IF Sudeste MG do seu ano: as regras podem mudar."),
        ("Por que as modalidades mudaram?", "Desde 2025 as cotas usam os grupos LB (renda até 1 salário) e LI (qualquer renda). Até 2024 eram L1 a L14, com renda até 1,5 salário."),
    ]
    faq, fs = faq_html(perguntas)
    cab = "".join(f'<th{DEST if a == max(anos) else ""}>{a}</th>' for a in anos)
    corpo = (bloco("Resumo: ampla concorrência", f'<div class="pg-tab"><table><thead><tr><th>Curso</th>{cab}<th>Média 2 últimos anos</th><th>Acertos (de 45)</th></tr></thead><tbody>{"".join(resumo)}</tbody></table></div>' + fonte)
             + "".join(blocos)
             + bloco("Simule a sua nota", '<p>No <a href="/simulador-pism/">simulador</a>, aba <b>IF Sudeste MG</b>, digite a sua nota e veja quantos acertos faltam para o curso que você quer.</p>', "pg-lilas")
             + faq
             + cta("Prepare-se para o IF com o Quarks", "Preparatório IF Sudeste presencial em Juiz de Fora: Física, Química, Português e Matemática, em turmas de até 10 alunos.", "Quero saber do Preparatório IF",
                   "Olá! Vi as notas de corte do IF no site e quero saber do Preparatório IF Sudeste do Quarks.", ("Ver o Preparatório IF", "/preparatorio-if-sudeste/")))
    escrever("nota-de-corte-if-sudeste", titulo=f"Nota de corte do IF Sudeste MG em Juiz de Fora ({min(anos)} a {max(anos)}) | Quarks Edu",
             descricao=f"Nota de corte dos cursos técnicos integrados do IF Sudeste MG, campus Juiz de Fora, de {min(anos)} a {max(anos)}: Desenvolvimento de Sistemas, Edificações, Eletromecânica, Eletrotécnica, Mecânica, Meio Ambiente e Metalurgia, por modalidade.",
             h1="Nota de corte do IF Sudeste MG em Juiz de Fora", selo=f"Técnicos integrados · {min(anos)} a {max(anos)}",
             lead="A nota do último classificado em cada curso técnico integrado do campus Juiz de Fora, ano a ano e por modalidade de cotas.",
             numeros=f'<div class="pg-num"><div><b>{len(d["cursos"])}</b><span>cursos integrados</span></div><div><b>45</b><span>questões, 2 pontos cada</span></div><div><b>90</b><span>pontos possíveis</span></div></div>',
             corpo=corpo, trilha=[("Notas de corte do IF Sudeste", "/nota-de-corte-if-sudeste/")], prioridade="0.8",
             schemas=[fs, {"@type": "Dataset", "name": "Notas de corte dos técnicos integrados do IF Sudeste MG, campus Juiz de Fora",
                           "description": f"Nota do último classificado por curso e modalidade nos ingressos de {min(anos)} a {max(anos)}, a partir das classificações finais publicadas pelo IF Sudeste MG. Só números agregados.",
                           "creator": ORG, "temporalCoverage": f"{min(anos)}/{max(anos)}", "inLanguage": "pt-BR", "isAccessibleForFree": True, "dateModified": HOJE}])


def simulador_js(prova="pism1"):
    return (f'<script src="https://sistema.quarksedu.com.br/bancodenotas/simulador.js?v={SIM_V}" defer></script>\n'
            "<script>window.addEventListener('DOMContentLoaded', function () { var el = document.getElementById('simulador-quarks'); if (el && window.QuarksSimulador) "
            f"window.QuarksSimulador.montar(el, {{ modo: 'site', prova: '{prova}' }}); else if (el) el.innerHTML = ''; }});</script>")


def pagina_simulador():
    perguntas = [
        ("O simulador do PISM é oficial?", "Não é da UFJF: é do Quarks, feito com as notas oficiais publicadas pela Copese/UFJF desde o triênio 2016-2018. É uma estimativa: cada ano tem a sua prova e a sua concorrência."),
        ("A minha nota fica guardada?", "Não. A nota digitada fica só na sua tela; nada sai do seu navegador."),
        ("Serve para o IF Sudeste?", "Sim, na aba IF Sudeste MG, com a nota de 0 a 90 e os cursos técnicos integrados do campus Juiz de Fora."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (bloco("Simule a sua aprovação", "<p>Escolha a prova: <b>PISM I</b> ou <b>PISM II</b> para ver onde você estaria entre quem fez aquele módulo, <b>Meu curso (PISM III)</b> para ver quanto precisa em cada módulo que falta, ou <b>IF Sudeste MG</b>.</p>"
                   '<div id="simulador-quarks" style="margin-top:16px"></div>')
             + bloco("Como a nota do PISM é calculada", '<p>Nota final = PISM I × 0,20 + PISM II × 0,30 + PISM III × 0,50 (Resolução CONGRAD 340/2026). A UFJF publica com peso 2, 3 e 5: até 240, 360 e 700 pontos, total de 1.300. Veja o <a href="/pism/">guia do PISM 2027</a> e a <a href="/nota-de-corte-pism/">nota de corte de cada curso</a>.</p>', "pg-lilas")
             + faq
             + cta("Quero chegar lá", "O Quarks monta a trilha até a nota do seu curso, presencial em Juiz de Fora.", "Quero chegar lá com o Quarks",
                   "Olá! Fiz o simulador do site e quero saber como estudar no Quarks.", ("Preparatório PISM", "/preparatorio-pism/")))
    escrever("simulador-pism", titulo="Simulador do PISM (UFJF) e do IF Sudeste: quanto falta para o seu curso | Quarks Edu",
             descricao="Simulador do PISM da UFJF e do IF Sudeste MG com as notas oficiais desde 2016: veja onde você estaria entre os candidatos e quanto precisa em cada módulo para o seu curso.",
             h1="Simulador do PISM e do IF Sudeste", selo="Notas oficiais da UFJF e do IF",
             lead="Digite a sua nota e veja onde você estaria entre quem fez o PISM e quanto falta para o curso que você quer.",
             corpo=corpo, trilha=[("Simulador do PISM", "/simulador-pism/")], scripts=simulador_js(), prioridade="0.8",
             schemas=[fs, {"@type": "WebApplication", "name": "Simulador do PISM e do IF Sudeste", "applicationCategory": "EducationalApplication", "operatingSystem": "Web",
                           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "BRL"}, "provider": ORG}])


def sitemap():
    fixas = [("/", "1.0"), ("/privacidade/", "0.2"), ("/termos/", "0.2")]
    urls = "".join(f"  <url><loc>{SITE}{c}</loc><lastmod>{HOJE}</lastmod><priority>{p}</priority></url>\n" for c, p in fixas + sorted(PAGINAS))
    with open(os.path.join(RAIZ, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!-- Gerado por scripts/gerar_paginas.py. Não edite à mão. -->\n'
                f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    pastas = sorted({c.strip("/").split("/")[0] for c, _ in PAGINAS})
    with open(os.path.join(RAIZ, "paginas.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(pastas) + "\n")
    return pastas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gestao", default=os.path.join(os.path.dirname(RAIZ), "quarks-gestao"))
    a = ap.parse_args()
    if not os.path.isfile(os.path.join(a.gestao, "bancodenotas", "pism.json")):
        sys.exit(f"Não achei {a.gestao}/bancodenotas/pism.json (use --gestao CAMINHO).")
    # limpa as pastas geradas antes (curso que saiu do banco não fica para trás)
    if os.path.isfile(os.path.join(RAIZ, "paginas.txt")):
        for p in open(os.path.join(RAIZ, "paginas.txt"), encoding="utf-8").read().split():
            if p and p not in PROIBIDAS and os.path.isdir(os.path.join(RAIZ, p)):
                shutil.rmtree(os.path.join(RAIZ, p))
    paginas_notas(a.gestao)   # antes do guia: preenche DESTAQUES
    paginas_servicos()
    pagina_aprovados()
    paginas_pism()
    paginas_if(a.gestao)
    pagina_simulador()
    pastas = sitemap()
    print(f"{len(PAGINAS)} páginas em {len(pastas)} pastas: {', '.join(pastas)}")


if __name__ == "__main__":
    main()
