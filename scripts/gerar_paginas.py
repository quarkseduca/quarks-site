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

Visual (13/11/2026): site/paginas-20261113.css e site/paginas-20261113.js (mudou? nome novo com a data, aqui e nos
index.html da raiz, privacidade e termos: o CDN da Hostinger guarda o arquivo antigo por 7 dias). Fotos reais em site/img/ft-*.webp.
Imagens de compartilhamento: node scripts/gerar_og.js e depois rode este gerador de novo (site/og/*.jpg).

Banco de notas novo (todo ano, quando sai o resultado do PISM III)? Rode de novo, depois o gerar_og.js e de novo este, e faça commit.
Página nova? Acrescente aqui; não edite os index.html gerados à mão (serão sobrescritos).
"""
import argparse, html, json, os, re, shutil, sys, datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.quarksedu.com.br"
HOJE = datetime.date.today().isoformat()
ZAP = "5532998057212"
AVALIAR = "https://g.page/r/CU071YWDNuDYEBM/review"   # link "Pedir avaliações" do Perfil da Empresa no Google (dono, 12/11/2026)
SIM_V = "25.14"   # mesmo ?v= do simulador na página inicial (index.html)
CSS = ["/site/site-20261019c.css", "/site/vitrine-20261019.css", "/site/paginas-20261114.css"]   # nome novo a cada mudança (o CDN guarda 7 dias)
JS_SITE = "/site/site-20261110.js"
PISM_INICIO = "07/06/2027"        # Preparatório PISM online (decisão do dono, 06/11/2026)
PISM_INICIO_CURTO = "07/06"
JS_PG = "/site/paginas-20261113.js"   # contagem regressiva, linha do tempo, filtros, tabelas no celular, aparição suave
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

GUIAS = [("/preparatorio-pism/", "Preparatório PISM online"), ("/preparatorio-if-sudeste/", "Preparatório IF Sudeste"),
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


def faq_html(perguntas, olho="Dúvidas"):
    if not perguntas:
        return "", None
    corpo = "".join(f"<details><summary>{e(p)}</summary><p>{r}</p></details>" for p, r in perguntas)
    schema = {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": p, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", r)}} for p, r in perguntas]}
    return (f'<section class="pg-sec pg-auto"><div class="pg-in pg-faqg"><div class="pg-cab"><span class="pg-olho">{e(olho)}</span><h2>Perguntas frequentes</h2>'
            f'<p style="margin-top:12px">Não achou o que procurava? <a href="{zap("Olá! Tenho uma dúvida sobre o Quarks.")}" target="_blank" rel="noopener">Pergunte pelo WhatsApp</a>.</p></div>'
            f'<div class="pg-faq">{corpo}</div></div></section>'), schema


SIMBOLO = '<img src="/site/img/symbol-purple-transparent.png" alt="" width="58" height="58" loading="lazy">'


def cta(titulo, texto, botao, msg, segundo=None):
    s = f'<a class="pg-bt2" href="{segundo[1]}">{e(segundo[0])}</a>' if segundo else ""
    return (f'<section class="pg-sec pg-auto pg-cta-sec"><div class="pg-in"><div class="pg-cta"><i class="pg-orb a" aria-hidden="true"></i><i class="pg-orb b" aria-hidden="true"></i>'
            f'<div><h2>{e(titulo)}</h2><p>{texto}</p><div class="pg-ctas" style="margin-top:22px"><a class="btn am" href="{zap(msg)}" target="_blank" rel="noopener">{e(botao)}</a>{s}</div></div>'
            f'<span class="pg-simb" aria-hidden="true">{SIMBOLO}</span></div></div></section>')


# ---------------------------------------------------------------------------------------------------------------
# peças visuais (ícones, foto da capa, cartão de dado, gráfico, rota, galeria, linha do tempo)
# ---------------------------------------------------------------------------------------------------------------
_IC = {
    "turma": '<circle cx="9" cy="8" r="3.2"/><path d="M3 19c.6-3.2 3-5 6-5s5.4 1.8 6 5"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14.2c2.6.2 4.4 1.8 5 4.8"/>',
    "livro": '<path d="M4 5.5C6.5 4.3 9.3 4.3 12 6c2.7-1.7 5.5-1.7 8-.5V19c-2.5-1.2-5.3-1.2-8 .5-2.7-1.7-5.5-1.7-8-.5z"/><path d="M12 6v13.5"/>',
    "rota": '<circle cx="6" cy="18" r="2.4"/><circle cx="18" cy="6" r="2.4"/><path d="M8.4 18H15a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h6.6"/>',
    "frasco": '<path d="M9 3h6M10 3v6L4.5 18.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-2.5L14 9V3"/><path d="M7 15h10"/>',
    "grafico": '<path d="M4 20V4"/><path d="M4 20h16"/><path d="m7 15 4-4 3 3 5-6"/>',
    "familia": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v10h13V10"/><path d="M10 20v-5h4v5"/>',
    "relogio": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "alvo": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/>',
    "estrela": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    "calendario": '<rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    "chat": '<path d="M5 18.5 3.5 21l.8-4A8 8 0 1 1 7.5 19"/><path d="M8.5 11h7M8.5 14h4"/>',
    "lapis": '<path d="M4 20l1-4L16 5l3 3L8 19z"/><path d="M14 7l3 3"/>',
    "check": '<circle cx="12" cy="12" r="8.5"/><path d="m8 12.2 2.7 2.6L16 9.5"/>',
    "pessoa": '<circle cx="12" cy="8" r="3.6"/><path d="M5 20c.8-4 3.6-6 7-6s6.2 2 7 6"/>',
}


def ic(nome):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_IC[nome]}</svg>'


def capa_foto(src, alt, pos="50% 40%", chips=()):
    """foto real numa moldura arredondada com órbitas; chips = [(ícone, título, texto)] (até 2)"""
    ch = "".join(f'<span class="chip c{i + 1}"><i>{ic(c[0])}</i><span><b>{e(c[1])}</b>{e(c[2])}</span></span>' for i, c in enumerate(chips[:2]))
    return (f'<div class="pg-fc"><span class="pg-anel" aria-hidden="true"></span><span class="pg-anel b" aria-hidden="true"></span>'
            f'<div class="foto"><img src="{src}" alt="{e(alt)}" width="900" height="900" fetchpriority="high" style="object-position:{pos}"></div>{ch}'
            f'<span class="sim" aria-hidden="true"><img src="/site/img/symbol-purple-transparent.png" alt="" width="46" height="46"></span></div>')


def grafico(pontos, alto=150, rotulo=lambda v: br(v), minimo=None):
    """gráfico de linha em SVG (sem JS): pontos = [(rótulo do eixo, valor)], o último em destaque"""
    pts = [(a, v) for a, v in pontos if v is not None]
    if len(pts) < 2:
        return ""
    W, H, pe, pd, pt_, pb = 560, alto, 26, 34, 30, 26
    vs = [v for _, v in pts]
    lo, hi = min(vs), max(vs)
    if minimo is not None:
        lo = min(lo, minimo)
    folga = (hi - lo) * .18 or 10
    lo, hi = lo - folga, hi + folga * .6
    n = len(pts)
    X = lambda i: pe + i * (W - pe - pd) / (n - 1)
    Y = lambda v: pt_ + (hi - v) * (H - pt_ - pb) / (hi - lo)
    xy = [(X(i), Y(v)) for i, (_, v) in enumerate(pts)]
    linha = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(xy))
    area = linha + f" L{xy[-1][0]:.1f},{H - pb} L{xy[0][0]:.1f},{H - pb} Z"
    gx = "".join(f'<line class="gx" x1="{x:.1f}" x2="{x:.1f}" y1="{pt_ - 8}" y2="{H - pb}"/>' for x, _ in xy)
    pontos_svg = "".join(f'<circle class="pt{" ult" if i == n - 1 else ""}" cx="{x:.1f}" cy="{y:.1f}" r="{6 if i == n - 1 else 4.5}"/>' for i, (x, y) in enumerate(xy))
    vals = "".join(f'<text class="v{" ult" if i == n - 1 else ""}" x="{x:.1f}" y="{y - 12:.1f}" text-anchor="middle">{e(rotulo(v))}</text>' for i, ((x, y), (_, v)) in enumerate(zip(xy, pts)))
    eixo = "".join(f'<text x="{x:.1f}" y="{H - 6}" text-anchor="middle">{e(a)}</text>' for (x, _), (a, _) in zip(xy, pts))
    desc = "; ".join(f"{a}: {rotulo(v)}" for a, v in pts)
    return (f'<svg class="pg-graf" viewBox="0 0 {W} {H}" role="img" aria-label="{e(desc)}"><defs><linearGradient id="pgGrad" x1="0" x2="0" y1="0" y2="1">'
            f'<stop offset="0" stop-color="#6551D1" stop-opacity=".22"/><stop offset="1" stop-color="#6551D1" stop-opacity="0"/></linearGradient></defs>'
            f'{gx}<path class="ar" d="{area}"/><path class="ln" d="{linha}"/>{pontos_svg}{vals}{eixo}</svg>')


def capa_dado(rotulo, valor, unidade, sub, graf="", rodape=""):
    return (f'<div class="pg-dado"><div class="rot">{e(rotulo)}</div><div class="val">{valor}<small>{e(unidade)}</small></div>'
            f'<div class="sub">{sub}</div>' + (f'<div class="pg-dgraf">{graf}</div>' if graf else "") + (f'<div class="pg-drod">{rodape}</div>' if rodape else "") + '</div>')


def capa_contagem(alvo, rotulo, titulo, sub, depois, acao=""):
    """contagem regressiva até `alvo` (ISO, horário de Brasília); depois da data mostra `depois`"""
    return (f'<div class="pg-dado" data-conta="{alvo}"><div data-antes><div class="rot">{e(rotulo)}</div><div class="val" style="font-size:40px">{titulo}</div>'
            f'<div class="sub">{sub}</div><div class="pg-conta" aria-live="off"><div><b data-d>–</b><span>dias</span></div><div><b data-h>–</b><span>horas</span></div><div><b data-m>–</b><span>minutos</span></div></div></div>'
            f'<div data-depois>{depois}</div>{acao}</div>')


def recursos(itens):
    """itens = [(ícone, título, texto)]"""
    n = len(itens)
    cls = " n2" if n == 2 else " n4" if n == 4 else ""
    return f'<div class="pg-recursos{cls}">' + "".join(f'<div class="pg-rec"><i>{ic(a)}</i><b>{e(b)}</b><p>{c}</p></div>' for a, b, c in itens) + "</div>"


def tabela(html_tabela, arraste="Arraste para o lado para ver tudo"):
    return f'<div class="pg-tabw"><span class="pg-arraste">{e(arraste)} →</span><div class="pg-tab">{html_tabela}</div></div>'


GALERIA = [("/site/img/ft-turma.webp", "Alunos e professores do Quarks com a camiseta da marca", "50% 40%"),
           ("/site/img/ft-equipe-festa.webp", "Equipe do Quarks comemorando", "50% 40%"),
           ("/site/img/ft-convivencia.webp", "Aluno no espaço de convivência do Quarks", "50% 30%"),
           ("/site/img/fachada.webp", "Fachada do Quarks na Av. Rui Barbosa, em Juiz de Fora", "50% 40%"),
           ("/site/img/ft-comemoracao.webp", "Aprovados e professores do Quarks comemorando", "50% 40%")]


def galeria(fotos=GALERIA):
    return '<div class="pg-galeria">' + "".join(f'<figure><img src="{s}" alt="{e(a)}" loading="lazy" width="900" height="700" style="object-position:{p}"></figure>' for s, a, p in fotos) + "</div>"


def moldura(src, alt, legenda="", pos="50% 40%"):
    leg = f"<figcaption>{e(legenda)}</figcaption>" if legenda else ""
    return f'<figure class="pg-moldura"><img src="{src}" alt="{e(alt)}" loading="lazy" width="900" height="760" style="object-position:{pos}">{leg}</figure>'


def dois(texto, visual, inv=False):
    return f'<div class="pg-dois{" inv" if inv else ""}"><div>{texto}</div><div>{visual}</div></div>'


def celular(src, alt, lazy=True, classe=""):
    """tela real do Portal num celular desenhado em CSS"""
    return (f'<div class="pg-celular{(" " + classe) if classe else ""}"><img src="{src}" alt="{e(alt)}" width="540" height="1080"'
            f'{" loading=\"lazy\"" if lazy else " fetchpriority=\"high\""}></div>')


def capa_portal(chips=()):
    """capa com dois celulares do Portal (Minha trilha na frente, teoria atrás), órbitas e selos"""
    ch = "".join(f'<span class="chip c{i + 1}"><i>{ic(c[0])}</i><span><b>{e(c[1])}</b>{e(c[2])}</span></span>' for i, c in enumerate(chips[:2]))
    return (f'<div class="pg-fc pg-fcel"><span class="pg-anel" aria-hidden="true"></span><span class="pg-anel b" aria-hidden="true"></span>'
            + celular("/site/img/trilha-3.webp", "Teoria de Gráficos do movimento no Portal Quarks", classe="tras")
            + celular("/site/img/trilha-2.webp?v=2", "Minha trilha no Portal Quarks: o edital do PISM, assunto por assunto", lazy=False, classe="frente")
            + ch + '<span class="sim" aria-hidden="true"><img src="/site/img/symbol-purple-transparent.png" alt="" width="46" height="46"></span></div>')


def demo_portal():
    """animação: no Portal, a teoria, o treino e a questão oficial abrem uma depois da outra (só CSS; parada para quem pede menos movimento)"""
    passos = [("Teoria", "O que o edital pede e a explicação completa, com gráficos e exemplos."),
              ("Treino Quarks", "Exercícios do fácil ao nível da prova. A etapa conclui com 10 certas."),
              ("Prova oficial", "Questões que caíram de verdade no PISM, com a prova e o ano.")]
    lista = "".join(f'<li class="d{i + 1}"><span class="n">{i + 1}</span><div><b>{e(t)}</b><p>{e(x)}</p></div></li>' for i, (t, x) in enumerate(passos))
    telas = [("/site/img/trilha-3.webp", "Teoria de Gráficos do movimento"), ("/site/img/trilha-4.webp", "Treino Quarks com a resposta certa e a resolução comentada"),
             ("/site/img/trilha-5.webp", "Questão oficial do PISM I 2024")]
    camadas = "".join(f'<img class="l l{i + 1}" src="{s}" alt="{e(a)}" width="540" height="1080" loading="lazy">' for i, (s, a) in enumerate(telas))
    return ('<div class="pg-demo">'
            f'<ol class="pg-demo-passos">{lista}</ol>'
            '<div class="pg-demo-cel"><span class="pg-anel" aria-hidden="true"></span>'
            '<div class="pg-celular"><div class="tela">'
            '<img class="base" src="/site/img/trilha-2.webp?v=2" alt="Minha trilha no Portal Quarks" width="540" height="1080" loading="lazy">'
            f'{camadas}<i class="toque t1" aria-hidden="true"></i><i class="toque t2" aria-hidden="true"></i><i class="toque t3" aria-hidden="true"></i>'
            '</div></div></div></div>')


def escrever(caminho, *, titulo, descricao, h1, lead, corpo, trilha, selo="", ctas="", numeros="", schemas=(), imagem="/site/img/sala-pism.webp",
             scripts="", prioridade="0.7", sec=None, visual="", og_quadro=""):
    pasta = caminho.strip("/")
    assert pasta.split("/")[0] not in PROIBIDAS, pasta
    mig, mig_schema = migalhas(trilha)
    url = f"{SITE}/{pasta}/"
    grafo = [mig_schema, {"@type": "WebPage", "@id": url, "url": url, "name": titulo, "description": descricao, "inLanguage": "pt-BR",
                          "isPartOf": {"@id": f"{SITE}/#site"}, "publisher": ORG, "dateModified": HOJE}] + [s for s in schemas if s]
    ld = json.dumps({"@context": "https://schema.org", "@graph": grafo}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    dc = (lambda k: f' data-c="site.{sec}.{k}"') if sec else (lambda k: "")
    secattr = f' data-sec="site.{sec}" data-sec-rot="{e(h1)}"' if sec else ""
    # faixas alternadas: branco e névoa; lilás/roxo explícitos quebram a sequência
    tons = iter(["pg-branco", "pg-nevoa"] * 40)
    def _tom(m):
        return m.group(0).replace("pg-auto", next(tons))
    corpo = re.sub(r'<section class="pg-sec pg-auto[^"]*"', _tom, corpo)
    og = OG.get(pasta)
    og_img = f"{SITE}/site/og/{og}.jpg" if og else f"{SITE}{imagem}"
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
<meta property="og:image" content="{og_img}">
{'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' if og else ''}
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#5B37AE">
<link rel="icon" href="/site/img/favicon-96.png" sizes="96x96" type="image/png">
<link rel="apple-touch-icon" href="/site/img/apple-touch-icon.png">
<link rel="preload" href="/site/fontes/BricolageGrotesque-800.woff2" as="font" type="font/woff2" crossorigin>
{chr(10).join(f'<link rel="stylesheet" href="{c}">' for c in CSS)}
<script>document.documentElement.classList.add('pg-js')</script>
<script type="application/ld+json">{ld}</script>
</head>
<body class="mk d-g lj pg-site pg-interna">
{TOPO}
<main id="conteudo" class="pg">
  <section class="pg-capa{'' if visual else ' pg-capa--so'}"{secattr}>
    <i class="pg-orb a" aria-hidden="true"></i><i class="pg-orb b" aria-hidden="true"></i>
    <div class="pg-in pg-capa-grid">
      <div class="pg-capa-tx">
      {mig}
      {f'<span class="pg-selo">{e(selo)}</span>' if selo else ''}
      <h1{dc('h1')}>{e(h1)}</h1>
      <p class="pg-lead"{dc('lead')}>{lead}</p>
      {ctas}
      {numeros}
      </div>
      {f'<div class="pg-capa-vis">{visual}</div>' if visual else ''}
    </div>
  </section>
{corpo}
</main>
{RODAPE}
<script src="{JS_SITE}"></script>
<script src="{JS_PG}" defer></script>
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
    m = re.search(r'class="val">([^<]+)<small>([^<]*)', visual or "")
    OG_LISTA.append({"pasta": pasta, "titulo": h1, "selo": selo, "lead": re.sub(r"<[^>]+>", "", lead),
                     "valor": m.group(1) if m else "", "unidade": m.group(2) if m else "",
                     "foto": (re.search(r'class="foto"><img src="([^"]+)"', visual or "") or [None, ""])[1], "quadro": og_quadro})


OG = {}          # pasta -> nome do arquivo em site/og/ (preenchido em main, se a imagem existir)
OG_LISTA = []    # para scripts/gerar_og.js


def bloco(titulo, conteudo, classe="", olho="", tx=False, id_=""):
    """uma faixa inteira; classe: "" (alterna branco/névoa), "pg-lilas" ou "pg-roxo"."""
    tom = classe if classe in ("pg-lilas", "pg-roxo") else "pg-auto"
    extra = " ".join(c for c in classe.split() if c not in ("pg-lilas", "pg-roxo"))
    o = f'<span class="pg-olho">{e(olho)}</span>' if olho else ""
    c = f'<div class="pg-tx">{conteudo}</div>' if tx else conteudo
    i = f' id="{id_}"' if id_ else ""
    return f'<section class="pg-sec {tom} {extra}"{i}><div class="pg-in"><div class="pg-cab">{o}<h2>{e(titulo)}</h2></div>{c}</div></section>'


def botoes(principal, msg, segundo=None):
    s = f'<a class="pg-bt2" href="{segundo[1]}">{e(segundo[0])}</a>' if segundo else ""
    return f'<div class="pg-ctas"><a class="btn am" href="{zap(msg)}" target="_blank" rel="noopener">{e(principal)}</a>{s}</div>'


ENDERECO = "Av. Rui Barbosa, 1449, Santa Terezinha, Juiz de Fora (MG)"
HORARIO = "segunda a quinta, das 9h às 20h; sexta, das 9h às 19h; sábado, das 8h às 12h"
MAPA = "https://maps.google.com/?q=Av.%20Rui%20Barbosa%2C%201449%2C%20Juiz%20de%20Fora"
PASSOS = [("Diagnóstico", "Algumas questões por matéria mostram onde o aluno está, e a trilha começa no ponto certo."),
          ("Trilha do edital", "Os conteúdos da prova na ordem certa. A coordenação ajusta para cada aluno."),
          ("Videoaula e teoria", "Cada etapa tem a explicação em vídeo e a teoria escrita pelo Quarks."),
          ("Treino Quarks", "Exercícios do fácil ao nível de prova. A etapa só conclui com 10 questões certas."),
          ("Prova oficial", "Questões que caíram de verdade na prova, com a prova e o ano."),
          ("Revisão", "Cada erro vai para o caderno de erros, e o conteúdo volta em 1, 7 e 30 dias.")]
ROTA = '<ol class="pg-rota">' + "".join(f"<li><b>{e(t)}</b><span>{e(x)}</span></li>" for t, x in PASSOS) + "</ol>"
PAIS = recursos([
    ("check", "A semana numa frase", "Como o filho está, com o selo Indo bem, Pede atenção ou Precisa de apoio."),
    ("grafico", "Os sinais explicados", "Presença, tarefas, simulados e estudo em casa, com o que cada número quer dizer e como ajudar."),
    ("rota", "A trilha até a prova", "Quanto do edital já foi estudado, matéria por matéria."),
    ("chat", "A coordenação junto", "Ela acompanha a mesma trilha e é avisada quando o aluno fica dias sem estudar."),
])


def visita(titulo="Venha conhecer o Quarks"):
    return (f'<section class="pg-sec pg-lilas"><div class="pg-in"><div class="pg-visita">'
            f'<div class="foto"><img src="/site/img/fachada.webp" alt="Fachada do Quarks na Av. Rui Barbosa, 1449, em Juiz de Fora" width="560" height="839" loading="lazy" style="object-position:50% 35%"></div>'
            f'<div class="tx"><span class="pg-olho">Visite</span><h2>{e(titulo)}</h2>'
            f'<dl><dt>Endereço</dt><dd>{e(ENDERECO)}</dd><dt>Seg a qui</dt><dd>9h às 20h</dd><dt>Sexta</dt><dd>9h às 19h</dd><dt>Sábado</dt><dd>8h às 12h</dd><dt>WhatsApp</dt><dd>(32) 99805-7212</dd></dl>'
            f'<div class="pg-ctas"><a class="btn am" href="{zap("Olá! Quero agendar uma visita ao Quarks.")}" target="_blank" rel="noopener">Agendar visita</a>'
            f'<a class="pg-bt2" href="{MAPA}" target="_blank" rel="noopener">Como chegar</a></div>'
            f'<p class="avalie">Já estuda ou estudou no Quarks? <a href="{AVALIAR}" target="_blank" rel="noopener">Conte como foi no Google ★</a></p></div></div></div></section>')


def aprovados_index():
    h = open(os.path.join(RAIZ, "index.html"), encoding="utf-8").read()
    return re.findall(r'<figure class="apf".*?src="([^"]+)".*?<b data-f="f0">([^<]+)</b><span data-f="f1">([^<]+)</span>', h)


def faixa_aprovados(titulo="Eles escreveram no braço o curso que conquistaram", filtro=None, classe="pg-roxo"):
    itens = sorted(aprovados_index(), key=lambda x: 0 if filtro and filtro in x[2] else 1)   # os da prova da página primeiro
    figs = "".join(f'<figure><img src="/{e(s)}" alt="{e(n)}" width="352" height="440" loading="lazy"><figcaption><b>{e(n)}</b>{e(c)}</figcaption></figure>' for s, n, c in itens)
    return (f'<section class="pg-sec {classe}"><div class="pg-in"><div class="pg-cab"><span class="pg-olho">Aprovados Quarks</span><h2>{e(titulo)}</h2></div>'
            f'<div class="pg-aprovs">{figs}</div><a class="pg-mais" href="/aprovados/">Ver todos os aprovados →</a></div></section>')


def servico(nome, desc):
    return {"@type": "Service", "name": nome, "description": desc, "provider": ORG, "areaServed": {"@type": "City", "name": "Juiz de Fora"}}


def curso(nome, desc, online=False, inicio=None):
    inst = ({"@type": "CourseInstance", "courseMode": "online", "courseWorkload": "PT4H30M"} if online
            else {"@type": "CourseInstance", "courseMode": "onsite", "location": {"@type": "Place", "name": "Quarks Edu", "address": ENDERECO}})
    if inicio:
        inst["startDate"] = inicio
    return {"@type": "Course", "name": nome, "description": desc, "provider": ORG, "inLanguage": "pt-BR", "hasCourseInstance": inst}


def num(*itens):
    return '<div class="pg-num">' + "".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in itens) + "</div>"


# ---------------------------------------------------------------------------------------------------------------
# páginas dos serviços
# ---------------------------------------------------------------------------------------------------------------
def paginas_servicos():
    # Preparatório PISM: só online desde 2027 (decisão do dono, 06/11/2026; início das aulas em 07/06/2027)
    perguntas = [
        ("O Preparatório PISM do Quarks é presencial?", "Não. O Preparatório PISM do Quarks é <b>só online</b>: aulas ao vivo, em turmas reduzidas, com o professor junto e todas as disciplinas no Portal Quarks. "
         'Quem quer estudar para o PISM presencialmente, em Juiz de Fora, pode fazer o <a href="/acompanhamento-escolar/">Acompanhamento Escolar</a>.'),
        ("Quando começam as aulas?", f"Em <b>{PISM_INICIO}</b>, e seguem até as provas do PISM de dezembro de 2027."),
        ("Para qual módulo é o preparatório?", "Para o PISM I (1º ano do ensino médio) e o PISM II (2º ano), com Física, Química, Matemática e Português ao vivo. A trilha de estudos segue o conteúdo de cada módulo."),
        ("Como é a aula online?", "Ao vivo, com o professor explicando e respondendo às perguntas na hora. A turma é reduzida, então o professor conhece cada aluno. "
         "Entre uma aula e outra, o aluno estuda pelo Portal Quarks: teoria, treino e questões oficiais de cada assunto."),
        ("Como sei quanto preciso tirar para o meu curso?", 'Veja a <a href="/nota-de-corte-pism/">nota de corte de cada curso da UFJF</a> e use o <a href="/simulador-pism/">simulador do PISM</a>, feitos com as notas oficiais da UFJF.'),
        ("Os pais acompanham o estudo?", "Sim. No portal das famílias os pais veem a presença, as tarefas, os simulados e a trilha, com cada número explicado."),
    ]
    faq, fs = faq_html(perguntas)
    portal = ('<div class="pg-cels">'
              + "".join(f'<figure>{celular(s, a)}<figcaption><b>{e(t)}</b>{e(x)}</figcaption></figure>' for s, a, t, x in [
                  ("/site/img/trilha-1.webp", "Diagnóstico de entrada no Portal Quarks", "Diagnóstico", "Algumas questões mostram onde o aluno está."),
                  ("/site/img/trilha-2.webp?v=2", "Minha trilha: o edital do PISM II, assunto por assunto", "Minha trilha", "O edital do PISM, assunto por assunto."),
                  ("/site/img/trilha-6.webp?v=2", "Plano do dia no Portal Quarks, com teoria, treino e prova oficial de cada disciplina", "Plano do dia", "O que estudar hoje, disciplina por disciplina."),
                  ("/site/img/trilha-7.webp?v=2", "Portal das famílias: a semana do aluno numa frase", "Para os pais", "A semana do filho numa frase."),
              ]) + "</div>")
    corpo = (
        bloco("Online, ao vivo e perto do professor", recursos([
            ("chat", "Aula ao vivo", "O professor explica, resolve e responde às perguntas na hora, como numa sala, de onde o aluno estiver."),
            ("turma", "Turmas reduzidas", "Poucos alunos por turma, para o professor conhecer cada um e acompanhar de perto."),
            ("pessoa", "Interação com o professor", "Dúvida não fica para depois: pergunte durante a aula e receba retorno sobre o seu progresso."),
            ("livro", "Todas as disciplinas no Portal", "Física, Química, Matemática e Português, com teoria, treino e questões oficiais de cada assunto."),
            ("rota", "Trilha do edital", "Os conteúdos do PISM I e do PISM II na ordem certa. A coordenação ajusta para cada aluno."),
            ("familia", "Família junto", "Portal das famílias com presença, tarefas, simulados e a trilha."),
        ]), olho="Como funciona")
        + bloco("Teoria, treino e prova oficial, um depois do outro", demo_portal(), "pg-lilas", olho="Veja o Portal por dentro", id_="portal")
        + bloco("Tudo do PISM num lugar só", "<p style=\"max-width:62ch;margin-bottom:30px\">Telas reais do Portal Quarks, com uma aluna de exemplo. Funciona no computador e no celular.</p>" + portal, olho="Portal Quarks")
        + bloco("O PISM se ganha nos três anos", dois(
            "<p>O PISM é o vestibular seriado da UFJF: uma prova por ano do ensino médio, e a nota final soma os três módulos, com peso maior a cada ano. "
            "Quem chega ao PISM III com o I e o II bem feitos entra na disputa do curso que quer.</p>"
            "<p>Por isso o Preparatório PISM online do Quarks começa cedo, no PISM I e no PISM II, com foco no que mais cai na UFJF e a trilha do edital no Portal Quarks.</p>"
            '<div class="pg-pesos" style="margin-top:22px" role="img" aria-label="Peso dos módulos na nota final: PISM I até 240, PISM II até 360, PISM III até 700 pontos"><div class="m1"><b>240</b><span>PISM I</span></div><div class="m2"><b>360</b><span>PISM II</span></div><div class="m3"><b>700</b><span>PISM III · total 1.300</span></div></div>',
            moldura("/site/img/ft-professores-alunas.webp", "Professores do Quarks com duas alunas aprovadas", "Professores e aprovadas do Quarks", "50% 30%")), olho="Por que começar cedo")
        + bloco("A trilha de estudos, passo a passo", "<p style=\"max-width:62ch;margin-bottom:26px\">Vem junto com o Preparatório PISM. É montada pelo edital da prova e ajustada pela coordenação para cada aluno.</p>" + ROTA, "pg-lilas", olho="Portal Quarks")
        + faixa_aprovados(filtro="UFJF")
        + bloco("Quanto o seu curso pede", '<div class="pg-destaques">'
                '<a class="pg-dq" href="/nota-de-corte-pism/medicina-integral/"><small>Medicina (integral)</small><b>1.040,25</b><span>pontos no PISM 2026 →</span></a>'
                '<a class="pg-dq" href="/nota-de-corte-pism/direito-integral/"><small>Direito (integral)</small><b>890</b><span>pontos no PISM 2026 →</span></a>'
                '<a class="pg-dq" href="/nota-de-corte-pism/direito-noturno/"><small>Direito (noturno)</small><b>806,75</b><span>pontos no PISM 2026 →</span></a></div>'
                '<p style="margin-top:18px">Ampla concorrência, de 1.300 possíveis. Veja <a href="/nota-de-corte-pism/">a nota de corte de todos os cursos de Juiz de Fora</a> ou faça a conta no <a href="/simulador-pism/">simulador</a>.</p>'
                '<p class="pg-fonte">Fonte: UFJF/Copese, resultado final do PISM III.</p>', olho="Notas de corte")
        + faq
        + cta("Garanta a vaga no PISM online", f"As aulas começam em {PISM_INICIO}, em turmas reduzidas. A coordenação do Quarks responde pelo WhatsApp com os próximos passos.", "Quero saber do PISM online",
              "Olá! Quero saber do Preparatório PISM online do Quarks.", ("Ver notas de corte", "/nota-de-corte-pism/")))
    escrever("preparatorio-pism", titulo="Preparatório PISM online, ao vivo | Quarks Edu", sec="pgpism",
             descricao=f"Preparatório PISM online do Quarks: aulas ao vivo de Física, Química, Matemática e Português para o PISM I e II, turmas reduzidas, interação com o professor e todas as disciplinas no Portal Quarks. Início em {PISM_INICIO}.",
             h1="Preparatório PISM online", selo="Online · ao vivo · turmas reduzidas",
             lead=f"Aulas ao vivo para o PISM I e o PISM II, com o professor junto e todas as disciplinas no Portal Quarks. Começa em <b>{PISM_INICIO}</b>.",
             ctas=botoes("Quero saber mais", "Olá! Quero saber do Preparatório PISM online do Quarks.", ("Ver como é o Portal", "#portal")),
             numeros=num((PISM_INICIO_CURTO, "início das aulas"), ("4", "disciplinas ao vivo"), ("200+", "aprovados do Quarks")),
             visual=capa_portal([("chat", "Ao vivo", "com o professor"), ("calendario", "Início", PISM_INICIO)]),
             corpo=corpo, trilha=[("Preparatório PISM", "/preparatorio-pism/")], imagem="/site/img/portal-pism.webp", prioridade="0.9",
             og_quadro="/site/img/portal-pism.webp",
             schemas=[curso("Preparatório PISM online (UFJF)", f"Preparatório online, com aulas ao vivo, para o PISM I e o PISM II da UFJF: Física, Química, Matemática e Português, turmas reduzidas e trilha do edital no Portal Quarks. Início em {PISM_INICIO}.", online=True, inicio="2027-06-07"), fs])

    # Preparatório IF Sudeste
    perguntas = [
        ("O Preparatório IF Sudeste do Quarks é presencial?", f"Sim, na {ENDERECO}, em turmas de até 10 alunos."),
        ("Quais matérias o preparatório cobre?", "Física, Química, Português e Matemática, com apostila própria e a trilha do IF no Portal Quarks."),
        ("Quantos pontos precisa para passar no IF Sudeste em Juiz de Fora?", 'Depende do curso e da modalidade. Na ampla concorrência de 2026, Desenvolvimento de Sistemas fechou em 70 de 90 pontos (35 acertos de 45). Veja <a href="/nota-de-corte-if-sudeste/">as notas de corte de todos os cursos integrados</a>.'),
        ("Como é a seleção do IF?", "Nos ingressos de 2023 a 2026 do campus Juiz de Fora, foi uma prova de 45 questões, cada uma valendo 2 pontos (até 90). As regras mudam de um ano para outro: confira sempre o edital do IF Sudeste MG do seu ano."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (
        bloco("Para entrar nos cursos técnicos integrados do IF", dois(
            "<p>Os cursos técnicos integrados ao ensino médio do IF Sudeste MG, em Juiz de Fora, são disputados por quem está no 9º ano.</p>"
            "<p>O Preparatório IF Sudeste do Quarks prepara para a prova com <b>Física, Química, Português e Matemática</b>, apostila própria e a trilha do IF, em turmas presenciais de até 10 alunos.</p>"
            '<div class="pg-destaques" style="grid-template-columns:repeat(2,minmax(0,1fr));margin-top:22px"><div class="pg-dq"><small>Prova</small><b>45</b><span>questões, 2 pontos cada</span></div>'
            '<div class="pg-dq"><small>Desenvolvimento de Sistemas 2026</small><b>70</b><span>de 90 pontos na ampla</span></div></div>',
            moldura("/site/img/ft-grupo.webp", "Professores e alunos aprovados do Quarks", "Equipe e aprovados do Quarks", "50% 40%")), olho="9º ano")
        + bloco("O que vem no Preparatório IF Sudeste", recursos([
            ("turma", "Turmas pequenas", "Até 10 alunos por turma, presencial em Juiz de Fora."),
            ("livro", "Apostila própria", "Raio-X da prova, questões por nível e gabarito comentado."),
            ("rota", "Trilha do IF", "Os conteúdos da prova na ordem certa, com treino e questões que caíram de verdade."),
            ("familia", "Família junto", "No portal das famílias, presença, tarefas, simulados e trilha."),
        ]), olho="Tudo incluído")
        + bloco("A trilha de estudos", ROTA, "pg-lilas", olho="Portal Quarks")
        + faixa_aprovados("Aprovados no IF Sudeste", filtro="IF Sudeste")
        + faq + visita()
        + cta("Comece o Preparatório IF Sudeste", "A coordenação do Quarks responde pelo WhatsApp com as turmas e os próximos passos.", "Quero saber do Preparatório IF",
              "Olá! Quero saber do Preparatório IF Sudeste do Quarks.", ("Ver notas de corte do IF", "/nota-de-corte-if-sudeste/")))
    escrever("preparatorio-if-sudeste", titulo="Preparatório IF Sudeste MG em Juiz de Fora | Quarks Edu", sec="pgif",
             descricao="Preparatório presencial em Juiz de Fora para a prova dos cursos técnicos integrados do IF Sudeste MG: Física, Química, Português e Matemática, turmas de até 10 alunos e apostila própria.",
             h1="Preparatório IF Sudeste MG em Juiz de Fora", selo="Presencial · até 10 por turma",
             lead="Física, Química, Português e Matemática, apostila própria e a trilha do IF, para entrar nos técnicos integrados.",
             ctas=botoes("Quero saber mais", "Olá! Quero saber do Preparatório IF Sudeste do Quarks.", ("Ver notas de corte do IF", "/nota-de-corte-if-sudeste/")),
             numeros=num(("4", "matérias da prova"), ("10", "alunos, no máximo, por turma")),
             visual=capa_foto("/site/img/ft-aprovados-if.webp", "Alunos do Quarks aprovados no IF Sudeste, com o curso escrito no braço", "50% 40%",
                              [("estrela", "Aprovados no IF", "em 5 cursos integrados"), ("livro", "Apostila própria", "raio-X da prova")]),
             corpo=corpo, trilha=[("Preparatório IF Sudeste", "/preparatorio-if-sudeste/")], imagem="/site/img/ft-aprovados-if.webp", prioridade="0.9",
             schemas=[curso("Preparatório IF Sudeste MG", "Preparatório presencial em Juiz de Fora para a prova dos cursos técnicos integrados do IF Sudeste MG: Física, Química, Português e Matemática."), fs])

    # Acompanhamento Escolar
    perguntas = [
        ("Como funciona o Acompanhamento Escolar do Quarks?", "Aulas de 1h30 de Física, Química, Matemática e Português, com no máximo 2 alunos por turma e o mesmo horário o ano todo. O professor acompanha a matéria da escola e já prepara para o PISM e o IF Sudeste."),
        ("Quais são os horários?", "De segunda a sexta: 14h às 15h30, 15h30 às 17h, 17h15 às 18h45 e 18h45 às 20h15. Sábado: 9h às 10h30 e 10h30 às 12h. As vagas são poucas por módulo."),
        ("Para quais anos é o Acompanhamento?", "Do 6º ano do ensino fundamental ao 3º ano do ensino médio."),
        ("Quero estudar para o PISM presencialmente. Posso?", 'Sim, pelo Acompanhamento Escolar: no ensino médio, o professor acompanha a matéria da escola e já prepara para o PISM. O <a href="/preparatorio-pism/">Preparatório PISM</a> do Quarks é só online, com aulas ao vivo.'),
        ("Os pais acompanham?", "Sim. No portal das famílias você vê a presença, as tarefas, os simulados e a trilha, com cada número explicado."),
        ("Tem resultado?", "Todos os alunos que fizeram o Acompanhamento do Quarks ao longo de todo o ensino médio foram aprovados."),
    ]
    faq, fs = faq_html(perguntas)
    horarios = ('<div class="pg-recursos n2"><div class="pg-rec"><i>' + ic("relogio") + '</i><b>Segunda a sexta</b><p>14h às 15h30 · 15h30 às 17h · 17h15 às 18h45 · 18h45 às 20h15</p></div>'
                '<div class="pg-rec"><i>' + ic("calendario") + '</i><b>Sábado</b><p>9h às 10h30 · 10h30 às 12h</p></div></div>'
                '<p style="margin-top:18px">O horário escolhido fica fixo o ano todo. As vagas são poucas por módulo.</p>')
    corpo = (
        bloco("O ano inteiro ao lado do seu filho", dois(
            "<p>No Acompanhamento Escolar do Quarks, o aluno tem <b>Física, Química, Matemática e Português</b> toda semana, com <b>no máximo 2 alunos por turma</b> e o mesmo horário o ano todo. "
            "As aulas têm 1h30, tempo para explicar, praticar e tirar dúvida na mesma aula. O professor acompanha a matéria da escola e já prepara para o PISM e o IF Sudeste.</p>"
            "<p>O PISM é feito em três etapas, uma em cada ano do ensino médio. Estudando junto com a escola, o aluno fecha cada etapa sem dúvidas acumuladas e chega à prova confiante, sem correria de última hora.</p>",
            moldura("/site/img/ft-equipe.webp", "Professores do Quarks abraçados, com a camiseta da marca", "A equipe do Quarks", "50% 30%")), olho="Do 6º ano ao 3º do médio")
        + bloco("Horários", horarios, olho="1h30 cada aula", id_="horarios")
        + bloco("Os pais veem tudo, sem precisar perguntar", PAIS + "<p style=\"margin-top:18px\">Inclui a trilha de estudos no Portal Quarks, montada pelo edital da prova. No Acompanhamento Escolar, a trilha cobre só as disciplinas escolhidas na matrícula.</p>", "pg-lilas", olho="Portal das famílias")
        + bloco("100% de aprovação", '<p style="font-size:20px;max-width:46ch">Todos os alunos que fizeram o Acompanhamento do Quarks ao longo de todo o ensino médio foram aprovados.</p>', "pg-roxo", olho="Resultado")
        + bloco("Por dentro do Quarks", galeria(), olho="Fotos")
        + faq + visita()
        + cta("Garanta a vaga do seu filho", "Diga o ano escolar e as matérias. A coordenação do Quarks responde pelo WhatsApp com os horários livres.", "Quero conhecer o Acompanhamento",
              "Olá! Quero conhecer o Acompanhamento Escolar do Quarks."))
    escrever("acompanhamento-escolar", titulo="Acompanhamento e reforço escolar em Juiz de Fora | Quarks Edu", sec="pgacomp",
             descricao="Acompanhamento e reforço escolar em Juiz de Fora: Física, Química, Matemática e Português, aulas de 1h30 com no máximo 2 alunos, mesmo horário o ano todo, do 6º ano ao 3º do médio.",
             h1="Acompanhamento e reforço escolar em Juiz de Fora", selo="No máximo 2 alunos por turma",
             lead="Física, Química, Matemática e Português toda semana, no mesmo horário o ano todo. A aprovação vem como consequência.",
             ctas=botoes("Quero conhecer", "Olá! Quero conhecer o Acompanhamento Escolar do Quarks.", ("Ver horários", "#horarios")),
             numeros=num(("1h30", "cada aula"), ("2", "alunos, no máximo, por turma"), ("100%", "de aprovação de quem fez o médio todo")),
             visual=capa_foto("/site/img/ft-equipe-festa.webp", "Professores do Quarks comemorando", "50% 40%",
                              [("relogio", "Mesmo horário", "o ano todo"), ("familia", "Pais por dentro", "no portal das famílias")]),
             corpo=corpo, trilha=[("Acompanhamento Escolar", "/acompanhamento-escolar/")], imagem="/site/img/ft-equipe-festa.webp", prioridade="0.9",
             schemas=[servico("Acompanhamento Escolar", "Reforço e acompanhamento escolar em Juiz de Fora: Física, Química, Matemática e Português, aulas de 1h30 com no máximo 2 alunos."), fs])

    # Aula particular
    perguntas = [
        ("De quais matérias é a aula particular?", "Física, Química, Matemática ou Português."),
        ("Para que serve a aula avulsa?", "Para tirar dúvidas, revisar a matéria da escola ou se preparar para uma prova, quando precisar."),
        ("Onde é a aula?", f"Na {ENDERECO}."),
        ("Como agendar?", "Pelo WhatsApp (32) 99805-7212: diga a matéria, o conteúdo e os dias possíveis."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (bloco("Uma aula só sua, quando precisar", dois(
                "<p>A aula avulsa do Quarks é uma aula particular, individual, de <b>Física, Química, Matemática ou Português</b>. "
                "Serve para tirar dúvidas, revisar a matéria da escola ou se preparar para uma prova: o professor parte do que o aluno trouxer.</p>"
                "<p>Para quem precisa de acompanhamento toda semana, o caminho é o <a href=\"/acompanhamento-escolar/\">Acompanhamento Escolar</a>, com no máximo 2 alunos e horário fixo.</p>",
                moldura("/site/img/aula-avulsa.webp", "Sala de aula do Quarks", "Sala do Quarks em Juiz de Fora", "50% 50%")), olho="Individual")
             + bloco("Como funciona", recursos([
                 ("chat", "1. Fale com o Quarks", "Pelo WhatsApp, diga a matéria, o conteúdo e os dias possíveis."),
                 ("calendario", "2. Escolha o horário", "O Quarks responde com os horários livres dos professores."),
                 ("lapis", "3. Traga a sua dúvida", "A aula parte do que o aluno trouxer: lista, prova, caderno ou conteúdo."),
             ]), "pg-lilas", olho="Passo a passo")
             + faq + visita("Onde fica")
             + cta("Agende a sua aula", "Diga a matéria e o conteúdo. O Quarks responde pelo WhatsApp com os horários.", "Agendar uma aula", "Olá! Quero agendar uma aula avulsa no Quarks."))
    escrever("aula-particular", titulo="Aula particular de Física, Química, Matemática e Português em Juiz de Fora | Quarks Edu", sec="pgavulsa",
             descricao="Aula particular em Juiz de Fora de Física, Química, Matemática ou Português, para tirar dúvidas, revisar a matéria da escola ou se preparar para uma prova.",
             h1="Aula particular em Juiz de Fora", selo="Individual · quando precisar",
             lead="Física, Química, Matemática ou Português, para tirar dúvidas, revisar a matéria da escola ou se preparar para uma prova.",
             ctas=botoes("Agendar uma aula", "Olá! Quero agendar uma aula avulsa no Quarks."), corpo=corpo,
             numeros=num(("1", "aluno e um professor"), ("4", "matérias à escolha")),
             visual=capa_foto("/site/img/ft-equipe-alto.webp", "Professores do Quarks com a camiseta da marca", "50% 40%",
                              [("pessoa", "Só você e o professor", "aula individual"), ("lapis", "Traga a dúvida", "lista, prova ou caderno")]),
             trilha=[("Aula particular", "/aula-particular/")], imagem="/site/img/ft-equipe-alto.webp", prioridade="0.8",
             schemas=[servico("Aula particular (aula avulsa)", "Aula particular individual de Física, Química, Matemática ou Português em Juiz de Fora."), fs])

    # Mentoria
    perguntas = [
        ("O que é a mentoria de estudos?", "Metas claras, um plano de estudo que cabe na rotina e encontros individuais ao longo do ano para acompanhar a evolução."),
        ("Para quem é?", "Para o aluno que quer organizar os estudos para o PISM, o IF Sudeste ou a escola e precisa de alguém acompanhando o plano."),
        ("Como começar?", "Fale com o Quarks pelo WhatsApp (32) 99805-7212."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (bloco("Estudar com plano", dois(
                "<p>A mentoria do Quarks é individual: o aluno sai com <b>metas claras</b>, um <b>plano de estudo que cabe na rotina</b> e <b>encontros ao longo do ano</b> para acompanhar a evolução e ajustar o caminho.</p>"
                '<p>Quem estuda para o PISM pode usar as <a href="/nota-de-corte-pism/">notas de corte</a> e o <a href="/simulador-pism/">simulador</a> para definir a meta de cada módulo.</p>',
                moldura("/site/img/mentoria.webp", "Professores e alunas aprovadas do Quarks", "Aprovadas e professores do Quarks", "50% 30%")), olho="Individual")
             + bloco("O que a mentoria entrega", recursos([
                 ("alvo", "Metas claras", "A nota que o curso pede, dividida em metas por módulo e por matéria."),
                 ("calendario", "Plano que cabe na rotina", "Um cronograma possível, com escola, cursos e descanso."),
                 ("chat", "Encontros ao longo do ano", "Para ver a evolução, ajustar o plano e não perder o rumo."),
             ]), "pg-lilas", olho="Na prática")
             + faq + visita("Onde fica")
             + cta("Quero uma mentoria", "O Quarks responde pelo WhatsApp com os próximos passos.", "Quero uma mentoria", "Olá! Quero saber da Mentoria de estudos do Quarks."))
    escrever("mentoria-de-estudos", titulo="Mentoria de estudos em Juiz de Fora | Quarks Edu", sec="pgment",
             descricao="Mentoria de estudos individual em Juiz de Fora: metas claras, plano de estudo que cabe na rotina e encontros ao longo do ano, para o PISM, o IF Sudeste e a escola.",
             h1="Mentoria de estudos em Juiz de Fora", selo="Individual · encontros ao longo do ano",
             lead="Metas claras, um plano de estudo que cabe na rotina e encontros para acompanhar a evolução.",
             ctas=botoes("Quero uma mentoria", "Olá! Quero saber da Mentoria de estudos do Quarks."), corpo=corpo,
             visual=capa_foto("/site/img/ft-foco.webp", "Aluna do Quarks concentrada", "50% 28%",
                              [("alvo", "Meta por módulo", "a partir da nota de corte"), ("calendario", "Plano semanal", "que cabe na rotina")]),
             trilha=[("Mentoria de estudos", "/mentoria-de-estudos/")], imagem="/site/img/ft-foco.webp", prioridade="0.7",
             schemas=[servico("Mentoria de estudos", "Mentoria de estudos individual em Juiz de Fora, com metas, plano de estudo e encontros ao longo do ano."), fs])


def pagina_aprovados():
    itens = aprovados_index()
    def prova(c):
        return "UFJF" if "UFJF" in c else "IF Sudeste" if "IF" in c else "UFRJ" if "UFRJ" in c else "Outras"
    provas = sorted({prova(c) for _, _, c in itens}, key=lambda p: ["UFJF", "UFRJ", "IF Sudeste", "Outras"].index(p))
    chips = '<div class="pg-chips" data-chips="aprov"><button type="button" aria-pressed="true" data-v="">Todos</button>' + "".join(f'<button type="button" aria-pressed="false" data-v="{e(p)}">{e(p)}</button>' for p in provas) + "</div>"
    figs = "".join(f'<figure data-prova="{e(prova(c))}"><img src="/{e(s)}" alt="{e(n)}" width="352" height="440" loading="lazy"><figcaption><b>{e(n)}</b>{e(c)}</figcaption></figure>' for s, n, c in itens)
    corpo = (bloco("Eles escreveram no braço o curso que conquistaram", f'<div class="pg-filtros">{chips}</div><div class="pg-aprov" data-aprov>{figs}</div>', olho=f"{len(itens)} na vitrine")
             + bloco("Por dentro do Quarks", galeria(), "pg-lilas", olho="Fotos")
             + bloco("Qual é o seu curso?", '<div class="pg-destaques"><a class="pg-dq" href="/nota-de-corte-pism/"><small>UFJF</small><b>72 cursos</b><span>notas de corte do PISM →</span></a>'
                     '<a class="pg-dq" href="/nota-de-corte-if-sudeste/"><small>IF Sudeste MG</small><b>7 cursos</b><span>notas de corte do IF →</span></a>'
                     '<a class="pg-dq" href="/simulador-pism/"><small>Simulador</small><b>Sua nota</b><span>quanto falta para o curso →</span></a></div>', olho="Agora é você")
             + cta("O próximo pode ser você", "Conheça o Preparatório PISM online, o Preparatório IF Sudeste e o Acompanhamento Escolar.", "Falar com o Quarks", "Olá! Vi os aprovados do Quarks e quero saber como estudar aí.",
                   ("Preparatório PISM", "/preparatorio-pism/")))
    escrever("aprovados", titulo="Aprovados do Quarks: UFJF, UFRJ e IF Sudeste MG | Quarks Edu",
             descricao="Alunos do Quarks Edu aprovados na UFJF (PISM), na UFRJ e no IF Sudeste MG. Mais de 200 aprovados em Juiz de Fora.",
             h1="Aprovados do Quarks", selo="200+ aprovados", lead="UFJF, UFRJ e IF Sudeste MG. Cada um escreveu no braço o curso que conquistou.",
             numeros=num(("200+", "aprovados"), ("3", "instituições: UFJF, UFRJ e IF")),
             visual=capa_foto("/site/img/ft-aprovados-ufjf.webp", "Aprovados do Quarks com APROVADO e UFJF escritos nos braços, junto da equipe", "50% 35%",
                              [("estrela", "UFJF, UFRJ e IF", "aprovados de verdade"), ("turma", "Turmas pequenas", "até 10 por turma")]),
             corpo=corpo, trilha=[("Aprovados", "/aprovados/")], imagem="/site/img/ft-aprovados-ufjf.webp", prioridade="0.7")


# ---------------------------------------------------------------------------------------------------------------
# guia do PISM e gabarito (Edital 10/2026 retificado pelos Editais 12 e 15/2026, e Resolução CONGRAD 340/2026)
# ---------------------------------------------------------------------------------------------------------------
EDITAL = "https://www2.ufjf.br/copese/2026/06/10/publicado-edital-do-pism-2027/"
RES340 = "https://www2.ufjf.br/copese/wp-content/uploads/sites/42/2026/06/SEI_3007081_ADM_Legislacao_002.01___Resolucao_340.pdf"
COPESE = "https://www2.ufjf.br/copese/vestibular-pism-2/"
# (evento, data como aparece, data ISO do dia, detalhe)
DATAS = [("Provas de todos os módulos", "05 e 06/12/2026", "2026-12-05", "Juiz de Fora, Governador Valadares, Muriaé, Petrópolis e Três Rios"),
         ("Gabaritos", "07/12/2026", "2026-12-07", "no site da Copese"),
         ("Recurso contra as provas", "08/12/2026", "2026-12-08", "das 9h às 16h"),
         ("Gabarito final e notas do módulo III", "19/01/2027", "2027-01-19", "a partir das 15h"),
         ("Recurso das notas do módulo III", "20/01/2027", "2027-01-20", "das 9h às 16h"),
         ("Resultado final do módulo III", "04/02/2027", "2027-02-04", "a partir das 15h"),
         ("Notas dos módulos I e II", "05/05/2027", "2027-05-05", "a partir das 15h"),
         ("Recurso das notas dos módulos I e II", "06/05/2027", "2027-05-06", "das 9h às 16h"),
         ("Resultado final dos módulos I e II", "25/05/2027", "2027-05-25", "a partir das 15h")]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FONTE_EDITAL = (f'<p class="pg-fonte">Fontes: <a href="{EDITAL}" target="_blank" rel="noopener">Edital 10/2026 da Copese/UFJF (PISM 2027), retificado pelos Editais 12/2026 e 15/2026</a> '
                f'e <a href="{RES340}" target="_blank" rel="noopener">Resolução CONGRAD/UFJF 340/2026</a>. Conferido em 11/11/2026; vale sempre o que estiver no site da Copese.</p>')


def tabela_datas():
    """linha do tempo; o JS marca o que já passou e o próximo passo"""
    li = []
    for ev, quando, iso, det in DATAS:
        a, m, d = iso.split("-")
        dia = f"{d}–06" if ev.startswith("Provas") else d
        li.append(f'<li data-dia="{iso}"><div class="dia"><b>{dia}</b><small>{MESES[int(m) - 1]} {a}</small></div><div class="ev"><b>{e(ev)}</b><small>{e(quando)} · {e(det)}</small></div></li>')
    return '<ol class="pg-tempo">' + "".join(li) + "</ol>"


def paginas_pism():
    formato = tabela('<table><thead><tr><th>Módulo</th><th>1º dia</th><th>2º dia</th><th>Vale</th></tr></thead><tbody>'
               '<tr><td><b>PISM I e PISM II</b></td><td style="white-space:normal">20 objetivas (5 de Língua Portuguesa, Matemática, Geografia e Química) e 8 discursivas (2 de cada)</td>'
               '<td style="white-space:normal">20 objetivas (5 de Literatura, Biologia, Física e História) e 8 discursivas (2 de cada)</td><td>120 pontos</td></tr>'
               '<tr><td><b>PISM III</b></td><td style="white-space:normal">20 objetivas (5 de Língua Portuguesa, Matemática, Literatura e Biologia) e 10 discursivas da área do curso</td>'
               '<td style="white-space:normal">20 objetivas (5 de Física, Química, Geografia e História) e 10 discursivas da área do curso</td><td>140 pontos</td></tr>'
               '</tbody></table>') + '<p>Cada objetiva vale 1 ponto e cada discursiva, até 5. As provas duram no máximo 4 horas.</p>'
    areas = tabela('<table><thead><tr><th>Área do curso</th><th>Discursivas do 1º dia</th><th>Discursivas do 2º dia</th></tr></thead><tbody>'
             '<tr><td>Exatas</td><td>5 de Língua Portuguesa e 5 de Matemática</td><td>5 de Física e 5 de Química</td></tr>'
             '<tr><td>Saúde</td><td>5 de Língua Portuguesa e 5 de Biologia</td><td>5 de Física e 5 de Química</td></tr>'
             '<tr><td>Economia e Administração</td><td>4 de Língua Portuguesa, 4 de Matemática e 2 de Sociologia</td><td>4 de Geografia, 4 de História e 2 de Filosofia</td></tr>'
             '<tr><td>Humanas</td><td>4 de Língua Portuguesa, 4 de Literatura e 2 de Sociologia</td><td>4 de Geografia, 4 de História e 2 de Filosofia</td></tr>'
             '</tbody></table>')
    modulos = ('<div class="pg-modulos">'
               '<div class="pg-mod"><em>1º ano</em><b>PISM I</b><p>Conteúdo do 1º ano. Vale até 120 e entra com peso 2: até <b>240</b> pontos.</p></div>'
               '<div class="pg-mod"><em>2º ano</em><b>PISM II</b><p>Conteúdo do 1º e do 2º ano. Vale até 120 e entra com peso 3: até <b>360</b> pontos.</p></div>'
               '<div class="pg-mod"><em>3º ano</em><b>PISM III</b><p>Conteúdo dos três anos. Vale até 140 e entra com peso 5: até <b>700</b> pontos.</p></div></div>')
    pesos = ('<div class="pg-pesos" role="img" aria-label="Nota final de até 1.300 pontos: PISM I até 240, PISM II até 360, PISM III até 700">'
             '<div class="m1"><b>240</b><span>PISM I · 18%</span></div><div class="m2"><b>360</b><span>PISM II · 28%</span></div><div class="m3"><b>700</b><span>PISM III · 54% · total 1.300</span></div></div>')
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
    destaques = "".join(f'<a class="pg-dq" href="/nota-de-corte-pism/{s_}/"><small>{e(n)}</small><b>{br(v)}</b><span>pontos no PISM {a_} →</span></a>' for s_, n, v, a_ in DESTAQUES[:6])
    corpo = (
        bloco("O que é o PISM", "<p>O <b>PISM (Programa de Ingresso Seletivo Misto)</b> é o vestibular seriado da Universidade Federal de Juiz de Fora (UFJF). O aluno faz uma prova por ano do ensino médio, e a nota final soma os três módulos, com peso maior a cada ano.</p>"
              + modulos + "<p style=\"margin-top:22px\">Por isso o PISM I e o PISM II contam muito: são 46% da nota final. "
              "No PISM 2027, as provas valem para o triênio 2026-2028 (módulo I), 2025-2027 (módulo II) e 2024-2026 (módulo III).</p>", olho="Vestibular seriado da UFJF")
        + bloco("Datas do PISM 2027", dois("<p>Do dia da prova ao resultado final. A data marcada como <b>Próxima</b> se atualiza sozinha.</p>"
                                           f'<p style="margin-top:18px"><a class="btn am" href="/gabarito-pism-2027/">Gabarito do PISM 2027</a></p>' + FONTE_EDITAL, tabela_datas()), "pg-lilas", olho="Calendário", id_="datas")
        + bloco("Como é a prova", formato + "<h3>Discursivas do PISM III, por área</h3>" + areas + FONTE_EDITAL, olho="Formato")
        + bloco("Como se calcula a nota", pesos + "<div class=\"pg-tx\" style=\"margin-top:22px\"><p>Pela Resolução CONGRAD 340/2026: <b>Nota Final = PISM I × 0,20 + PISM II × 0,30 + PISM III × 0,50</b>.</p>"
                "<p>Nos resultados, a UFJF mostra as notas com peso: o PISM I vale até 120 pontos e entra com peso 2 (até 240), o PISM II vale até 120 e entra com peso 3 (até 360), e o PISM III vale até 140 e entra com peso 5 (até 700). O total vai até <b>1.300</b>. É nessa escala que saem as notas de corte.</p>"
                "<p>Exemplo: 80 no PISM I, 85 no PISM II e 100 no PISM III dão 80 × 2 + 85 × 3 + 100 × 5 = 160 + 255 + 500 = <b>915 pontos</b>.</p>"
                '<p><a class="btn am" href="/simulador-pism/">Fazer a minha conta no simulador</a></p></div>', "pg-roxo", olho="1.300 pontos")
        + bloco("Vagas e cotas", "<p>No módulo III, pelo menos 50% das vagas de cada curso ficam reservadas para quem estudou em escola pública, divididas em 10 grupos de cotas (A a J; a ampla concorrência é o grupo C). "
                "Quem está num grupo de cotas concorre primeiro na ampla. O candidato do PISM também pode concorrer pelo Sisu.</p>" + FONTE_EDITAL, olho="Cotas", tx=True)
        + bloco("Quanto cada curso pede", f'<div class="pg-destaques">{destaques}</div><p style="margin-top:18px"><a class="pg-mais" href="/nota-de-corte-pism/">Ver a nota de corte dos 72 cursos de Juiz de Fora →</a></p>', "pg-lilas", olho="Notas de corte")
        + faq
        + cta("Prepare-se para o PISM com o Quarks", f"Preparatório PISM online, com aulas ao vivo, turmas reduzidas e todas as disciplinas no Portal Quarks. Início em {PISM_INICIO}.", "Quero saber do Preparatório PISM",
              "Olá! Li o guia do PISM e quero saber do Preparatório PISM online do Quarks.", ("Ver o Preparatório PISM", "/preparatorio-pism/")))
    conta = capa_contagem("2026-12-05T13:00:00-03:00", "Falta para o PISM 2027", "05 e 06/12", "Provas dos três módulos. Gabaritos em 07/12.",
                          '<div class="rot">PISM 2027</div><div class="val" style="font-size:40px">Provas feitas</div><div class="sub">Os gabaritos saem em 07/12 e o resultado do módulo III em 04/02/2027.</div>',
                          '<div class="acao"><a class="btn am" href="#datas">Ver todas as datas</a></div>')
    escrever("pism", titulo="PISM 2027 (UFJF): datas, como é a prova, nota e cotas | Guia do Quarks",
             descricao="Guia do PISM 2027 da UFJF: provas em 05 e 06/12/2026, gabarito em 07/12, resultado do módulo III em 04/02/2027, como é a prova, como calcular a nota e as cotas.",
             h1="PISM 2027: o guia completo", selo="Atualizado em 11/11/2026",
             lead="Datas, como é a prova de cada módulo, como a UFJF calcula a nota e como funcionam as cotas, conferido no edital da Copese.",
             ctas=f'<div class="pg-ctas"><a class="btn am" href="/nota-de-corte-pism/">Ver notas de corte</a><a class="pg-bt2" href="/simulador-pism/">Simular minha nota</a></div>',
             numeros=num(("05 e 06/12", "provas"), ("07/12", "gabaritos"), ("04/02/2027", "resultado do módulo III")), visual=conta,
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
              f'<p>O gabarito oficial fica no <a href="{COPESE}" target="_blank" rel="noopener">site da Copese</a>. Esta página do Quarks é atualizada assim que ele sair, com o link direto.</p>', olho="07/12/2026", tx=True)
        + bloco("Calendário depois da prova", dois("<p>A data marcada como <b>Próxima</b> se atualiza sozinha.</p>" + FONTE_EDITAL, tabela_datas()), "pg-lilas", olho="Calendário")
        + bloco("Confira a sua nota", recursos([
            ("check", "1. Conte as objetivas", "Com o gabarito, conte as objetivas certas de cada dia. Cada uma vale 1 ponto."),
            ("lapis", "2. Espere as discursivas", "Valem até 5 pontos cada e só aparecem nas notas oficiais."),
            ("grafico", "3. Compare com o curso", 'Leve a nota para a escala da UFJF no <a href="/simulador-pism/">simulador</a> e compare com a <a href="/nota-de-corte-pism/">nota de corte</a>.'),
        ]), olho="Depois da prova")
        + faq
        + cta("O próximo módulo com o Quarks", f"O Preparatório PISM online do Quarks tem turmas de PISM I e PISM II, com aulas ao vivo e o Portal Quarks. Início em {PISM_INICIO}.", "Quero saber do Preparatório PISM",
              "Olá! Fiz o PISM e quero saber do Preparatório PISM online do Quarks.", ("Guia do PISM 2027", "/pism/")))
    conta = capa_contagem("2026-12-07T00:00:00-03:00", "Falta para o gabarito", "07/12/2026", "A Copese publica os gabaritos no dia seguinte às provas.",
                          f'<div class="rot">Gabarito do PISM 2027</div><div class="val" style="font-size:40px">Já saiu</div><div class="sub">Confira no site oficial da Copese/UFJF.</div>'
                          f'<div class="acao"><a class="btn am" href="{COPESE}" target="_blank" rel="noopener">Ver o gabarito na Copese</a></div>')
    escrever("gabarito-pism-2027", titulo="Gabarito do PISM 2027: data e onde conferir | Quarks Edu",
             descricao="Gabarito do PISM 2027 da UFJF: as provas são em 05 e 06/12/2026 e a Copese divulga os gabaritos em 07/12/2026. Veja o calendário de recursos, notas e resultado.",
             h1="Gabarito do PISM 2027", selo="Gabaritos em 07/12/2026",
             lead="As provas são em 05 e 06/12/2026 e a Copese divulga os gabaritos em 07/12/2026. Veja o que vem depois e como conferir a sua nota.",
             ctas=f'<div class="pg-ctas"><a class="btn am" href="{COPESE}" target="_blank" rel="noopener">Site da Copese</a><a class="pg-bt2" href="/nota-de-corte-pism/">Notas de corte</a></div>',
             visual=conta, corpo=corpo, trilha=[("Guia do PISM", "/pism/"), ("Gabarito do PISM 2027", "/gabarito-pism-2027/")], prioridade="0.8",
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
    DESTAQUES[:] = [(x["slug"], x["nome"], x["cortes"][ano_max], ano_max) for x in top[:12]]
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
        todos_v = [v for G in c["g"].values() for v in (G.get("cortes") or {}).values() if v is not None]
        vmin, vmax = (min(todos_v), max(todos_v)) if todos_v else (0, 1)
        def q(v):
            if v is None or vmax == vmin:
                return ""
            return f' data-q="{1 + min(4, int((v - vmin) / (vmax - vmin) * 5))}"'
        for g in ordem_grupos(c["g"].keys()):
            G = c["g"][g]; ct = G.get("cortes") or {}
            if not any(ct.get(str(a)) is not None for a in anos):
                continue
            celulas = "".join(f'<td{q(ct.get(str(a)))}>{br(ct.get(str(a)))}</td>' for a in anos)
            linhas.append(f'<tr><td><b>{e(g)}</b> · {e(rot_grupo(g))}</td>{celulas}</tr>')
        cab = "".join(f'<th>PISM {a}</th>' for a in anos)
        tab_grupos = (tabela(f'<table><thead><tr><th>Grupo</th>{cab}</tr></thead><tbody>{"".join(linhas)}</tbody></table>', "Arraste para ver todos os anos")
                      + f'<div class="pg-legenda"><span>{br(vmin)}</span><i></i><span>{br(vmax)} pontos</span></div>')
        # vagas da ampla
        vag = C.get("vagas") or {}
        tab_ampla = ""
        if x["cortes"]:
            tab_ampla = tabela('<table><thead><tr><th>Edição</th><th>Nota de corte (ampla)</th><th>Vagas na ampla</th></tr></thead><tbody>'
                         + "".join(f'<tr><td>PISM {a}</td><td{DEST if a == ano_max else ""}>{br(x["cortes"].get(a))}</td><td>{br(vag.get(str(a)), 0) if vag.get(str(a)) is not None else "—"}</td></tr>' for a in sorted(x["cortes"], reverse=True))
                         + "</tbody></table>")
        # quem passou (só com 5 ou mais aprovados: regra do Banco de notas)
        ap = C.get("aprovados") or {}
        bloco_ap = ""
        if ap.get("n", 0) >= 5 and ap.get("m1"):
            barras = ""
            for m, rot, mx in ((1, "PISM I (peso 2)", 240), (2, "PISM II (peso 3)", 360), (3, "PISM III (peso 5)", 700), (0, "Total", 1300)):
                st = (ap.get(f"m{m}") or {}) if m else (ap.get("t") or {})
                med = (st.get("media") or 0) * (pesos[m] if m else 1)
                mn = (st.get("min") or 0) * (pesos[m] if m else 1)
                barras += (f'<div class="pg-barra"><div class="top"><span>{rot}</span><span>média <b>{br(med)}</b> · menor {br(mn)} · até {br(mx, 0)}</span></div>'
                           f'<div class="trilho"><span class="med" style="width:{min(100, med / mx * 100):.1f}%"></span><span class="min" style="left:{min(99.5, mn / mx * 100):.1f}%"></span></div></div>')
            bloco_ap = bloco(f"Quanto tiraram os aprovados em {curto}", dois(
                             f'<p>Notas, com peso, dos {ap["n"]} aprovados na ampla concorrência de {e(", ".join(ap.get("anos", [])[:1]))} a {e(ap.get("anos", [""])[-1])}.</p>'
                             '<p>A barra roxa é a <b>média de quem passou</b>; o traço amarelo, a <b>menor nota de quem entrou</b>.</p>'
                             "<p>Use como meta: quem chega ao PISM III perto da média dos aprovados nos módulos I e II entra na disputa com folga.</p>",
                             f'<div class="pg-grafcard"><div class="pg-barras">{barras}</div></div>'), olho="Meta por módulo")
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
            bloco(f"Nota de corte de {nome} no PISM", dois(f"<p>{resumo}</p>" + fonte, tab_ampla), olho="Ampla concorrência")
            + bloco("Simule a sua nota", f'<p style="max-width:66ch;margin-bottom:18px">O simulador já abre em <b>{e(nome)}</b>. Escolha o seu grupo de concorrência, digite as notas dos módulos que você já fez e veja quanto precisa em cada um que falta.</p><div class="pg-simcard"><div id="simulador-quarks"></div></div>', "pg-lilas", olho="Simulador")
            + bloco_ap
            + bloco("Por grupo de cotas", "<p style=\"max-width:80ch;margin-bottom:18px\">Ponto de corte de cada grupo, ano a ano; quanto mais escuro, mais alto. Desde o PISM 2025 os grupos mudaram (Lei 14.723/2023 e Resolução CONSU 120/2024): a renda passou de até 1,5 para até 1 salário mínimo por pessoa, e surgiram os grupos G a J. As letras de antes e de depois não são exatamente iguais.</p>" + tab_grupos + fonte, olho="Cotas")
            + faq
            + (bloco(f"Outros cursos de {e(c['area'])}", '<ul class="pg-links">' + "".join(f'<li><a href="/nota-de-corte-pism/{y["slug"]}/">{e(y["nome"])}</a></li>' for y in mesmos) + '</ul><p style="margin-top:16px"><a class="pg-mais" href="/nota-de-corte-pism/">Ver todos os 72 cursos →</a></p>', "pg-lilas", olho="Compare") if mesmos else "")
            + cta(f"Rumo a {curto}", f"Preparatório PISM online do Quarks: aulas ao vivo, turmas reduzidas e todas as disciplinas no Portal Quarks. Início em {PISM_INICIO}.", "Quero saber do Preparatório PISM",
                  f"Olá! Vi a nota de corte de {nome} no site e quero saber do Preparatório PISM online do Quarks.", ("Ver o Preparatório PISM", "/preparatorio-pism/")))
        dataset = {"@type": "Dataset", "name": f"Notas de corte de {nome} no PISM da UFJF", "description": desc + " Dados agregados do resultado final do PISM III (UFJF/Copese), sem nome de candidatos.",
                   "creator": ORG, "isBasedOn": COPESE, "temporalCoverage": f"{min(anos)}/{max(anos)}", "spatialCoverage": {"@type": "Place", "name": "Juiz de Fora, MG"},
                   "inLanguage": "pt-BR", "isAccessibleForFree": True, "dateModified": HOJE}
        tit = f"Nota de corte de {nome} no PISM {ult or ano_max} (UFJF) | Quarks Edu"
        escrever(f"nota-de-corte-pism/{x['slug']}", titulo=tit, descricao=desc, h1=f"Nota de corte de {nome} no PISM",
                 selo=f"UFJF · Juiz de Fora · {c['area']}", lead=f"Ano a ano desde o PISM {min(anos)}, por grupo de cotas, com as notas oficiais da UFJF.",
                 numeros=(num(*([("PISM " + str(ult), "edição mais recente")] + ([(br(C["media2"]), "média dos 2 últimos anos")] if C.get("media2") is not None else [])))) if ult else "",
                 visual=capa_dado(f"Nota de corte · ampla · PISM {ult}", br(x["cortes"][ult]), "de 1.300",
                                  (f"{br(vag.get(str(ult)), 0)} vagas na ampla em {ult}" if vag.get(str(ult)) else "Ampla concorrência"),
                                  grafico([(str(a), x["cortes"][a]) for a in sorted(x["cortes"])]),
                                  (f'<span>Média 2 anos <b>{br(C["media2"])}</b></span>' if C.get("media2") is not None else "")
                                  + (f'<span>Variação <b>{br(C.get("menor"))} a {br(C.get("maior"))}</b></span>' if C.get("menor") is not None else "")) if ult else "",
                 corpo=corpo, trilha=[("Notas de corte do PISM", "/nota-de-corte-pism/"), (nome, f"/nota-de-corte-pism/{x['slug']}/")],
                 scripts=simulador_js("pism3", c["id"]), prioridade="0.7", schemas=[fs, dataset])

    # índice
    por_area = {}
    for x in cursos:
        por_area.setdefault(x["c"]["area"], []).append(x)
    linhas = []
    for area in sorted(por_area):
        linhas.append(f'<tr class="grp" data-area="{e(area)}"><td colspan="4">{e(area)}</td></tr>')
        for x in sorted(por_area[area], key=lambda y: y["nome"]):
            C, ult = x["C"], x["ult"]
            v = (C.get("vagas") or {}).get(str(ult)) if ult else None
            linhas.append(f'<tr data-busca="{e(x["nome"].lower())}" data-area="{e(area)}"><td><a href="/nota-de-corte-pism/{x["slug"]}/">{e(x["nome"])}</a></td>'
                          f'<td class="dest">{br(x["cortes"][ult]) + ("" if ult == ano_max else f" ({ult})") if ult else "—"}</td>'
                          f'<td>{br(C.get("media2"))}</td><td>{br(v, 0) if v is not None else "—"}</td></tr>')
    chips = '<div class="pg-chips" data-chips="area"><button type="button" aria-pressed="true" data-v="">Todas as áreas</button>' + "".join(f'<button type="button" aria-pressed="false" data-v="{e(a)}">{e(a)}</button>' for a in sorted(por_area)) + "</div>"
    tabela_ = (f'<div class="pg-filtros"><input class="pg-filtro" type="search" placeholder="Procure o curso (ex.: medicina, direito)" aria-label="Procurar curso" data-filtro>{chips}</div>'
               + tabela(f'<table data-tabela><thead><tr><th>Curso</th><th class="dest">Corte PISM {ano_max} (ampla)</th><th>Média 2 últimos anos</th><th>Vagas na ampla</th></tr></thead><tbody>{"".join(linhas)}</tbody></table>')
               + '<p class="pg-vazio" data-vazio>Nenhum curso com esse nome. Tente só uma palavra, como "engenharia".</p>')
    filtro = ""
    top10 = '<div class="pg-top">' + "".join(f'<a href="/nota-de-corte-pism/{x["slug"]}/"><small>{e(x["nome"])}</small><b>{br(x["cortes"][ano_max])}</b></a>' for x in top[:10]) + "</div>"
    perguntas = [
        (f"Qual é a nota de corte de Medicina no PISM {ano_max}?", f"Na ampla concorrência, {br(medicina['cortes'][ano_max])} pontos de 1.300 (UFJF, Juiz de Fora)." if medicina and medicina["ult"] == ano_max else "Veja a página de Medicina."),
        ("O que é a nota de corte do PISM?", "É a menor pontuação de quem entrou nas vagas de um curso e grupo, no resultado final do PISM III. Ela muda todo ano, com a prova e a concorrência."),
        ("Como é calculada a nota do PISM?", "Nota final = PISM I × 0,20 + PISM II × 0,30 + PISM III × 0,50 (Resolução CONGRAD 340/2026). A UFJF publica com peso 2, 3 e 5, num total de até 1.300."),
        ("De onde vêm esses números?", "Do resultado final e das notas do PISM III publicados pela Copese/UFJF em cada edição, conferidos pelo Quarks. Só números agregados, sem nome de ninguém."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (
        bloco(f"As 10 maiores notas de corte do PISM {ano_max}", top10 + '<p class="pg-fonte">Ampla concorrência, em pontos de 1.300.</p>', olho="Ranking")
        + bloco(f"Nota de corte de todos os cursos ({len(cursos)})", "<p style=\"margin-bottom:18px\">Procure pelo nome ou escolha a área. Clique no curso para ver todos os anos, cada grupo de cotas, as vagas e quanto tiraram os aprovados em cada módulo.</p>" + tabela_ + fonte, "pg-lilas", olho="Todos os cursos", id_="cursos")
        + bloco("Simule a sua nota", '<p>Digite as suas notas e veja onde você estaria entre quem fez o PISM e quanto falta para o curso que você quer.</p><p style="margin-top:18px"><a class="btn am" href="/simulador-pism/">Abrir o simulador</a></p>', "pg-roxo", olho="Simulador", tx=True)
        + faq
        + cta("Do corte à aprovação", f"Preparatório PISM online do Quarks, com aulas ao vivo e a trilha do edital no Portal Quarks. Início em {PISM_INICIO}.", "Quero saber do Preparatório PISM",
              "Olá! Vi as notas de corte do PISM no site e quero saber do Preparatório PISM online do Quarks.", ("Guia do PISM 2027", "/pism/")))
    escrever("nota-de-corte-pism", titulo=f"Nota de corte do PISM {ano_max} (UFJF): todos os cursos de Juiz de Fora | Quarks Edu",
             descricao=f"Nota de corte do PISM da UFJF em todos os {len(cursos)} cursos de Juiz de Fora, de {min(anos_todos)} a {ano_max}, na ampla e em cada grupo de cotas, com as notas oficiais da Copese.",
             h1=f"Nota de corte do PISM: todos os cursos da UFJF", selo=f"PISM {min(anos_todos)} a {ano_max} · notas oficiais",
             lead=f"A nota de corte de cada curso de Juiz de Fora, ano a ano e por grupo de cotas, com as notas oficiais da UFJF.",
             numeros=num((str(len(cursos)), "cursos de Juiz de Fora"), (str(len(anos_todos)), f"edições ({min(anos_todos)} a {ano_max})"), ("1.300", "pontos possíveis")),
             ctas='<div class="pg-ctas"><a class="btn am" href="#cursos">Procurar meu curso</a><a class="pg-bt2" href="/simulador-pism/">Simular minha nota</a></div>',
             visual=(capa_dado(f"Medicina (integral) · ampla", br(medicina["cortes"][ano_max]), "de 1.300", (f"a nota mais alta do PISM {ano_max}" if top and top[0] is medicina else f"PISM {ano_max}"),
                               grafico([(str(a), medicina["cortes"][a]) for a in sorted(medicina["cortes"])]),
                               f'<span>{"Maior nota de corte" if top and top[0] is medicina else "Ampla concorrência"}</span><a href="/nota-de-corte-pism/medicina-integral/">Ver Medicina →</a>') if medicina and medicina["ult"] == ano_max else ""),
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
    blocos, resumo, barras_if = [], [], []
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
        graf = grafico([(str(a), ct.get(str(a))) for a in anos], alto=140) if ult else ""
        blocos.append(bloco(f"Nota de corte de {c['curso']} no IF Sudeste MG",
                            dois(txt + (f'<div class="pg-grafcard" style="margin-top:18px">{graf}</div>' if graf else ""),
                                 tabela('<table><thead><tr><th>Modalidade</th>' + "".join(f'<th{DEST if a == max(anos) else ""}>{a}</th>' for a in anos)
                                        + f'</tr></thead><tbody>{linhas}</tbody></table>', "Arraste para ver todos os anos")),
                            olho="Técnico integrado", id_=e(c["id"])))
        if ult:
            barras_if.append((c, ct[str(ult)], ult))
    fonte = f'<p class="pg-fonte">Fonte: {e(d["fonte"])}. Nota do último classificado em cada curso e modalidade, de 0 a 90. Só números agregados, sem nome de ninguém.</p>'
    perguntas = [
        ("Quantos pontos precisa para passar no IF Sudeste em Juiz de Fora?", "Depende do curso e da modalidade. Na ampla concorrência, os cortes de 2023 a 2026 ficaram entre os valores da tabela desta página; divida por 2 para saber os acertos de 45."),
        ("Como foi a prova do IF nesses anos?", "Nos ingressos de 2023 a 2026 do campus Juiz de Fora, a seleção dos técnicos integrados foi uma prova de 45 questões, cada uma valendo 2 pontos (de 0 a 90). Confira sempre o edital do IF Sudeste MG do seu ano: as regras podem mudar."),
        ("Por que as modalidades mudaram?", "Desde 2025 as cotas usam os grupos LB (renda até 1 salário) e LI (qualquer renda). Até 2024 eram L1 a L14, com renda até 1,5 salário."),
    ]
    faq, fs = faq_html(perguntas)
    cab = "".join(f'<th{DEST if a == max(anos) else ""}>{a}</th>' for a in anos)
    barras_if.sort(key=lambda t: -t[1])
    barras = "".join(f'<a class="pg-barra" href="#{e(c["id"])}" style="display:block;text-decoration:none;color:inherit"><div class="top"><span><b>{e(c["curso"])}</b></span><span><b>{br(v)}</b> de 90 · {int(round(v / 2))} acertos{"" if u == max(anos) else f" ({u})"}</span></div>'
                     f'<div class="trilho"><span class="med" style="width:{v / 90 * 100:.1f}%"></span></div></a>' for c, v, u in barras_if)
    # ranking do último ano e resumo ano a ano lado a lado (dono, 12/11/2026: "falam quase a mesma língua"); no celular, um abaixo do outro
    corpo = (bloco("Ampla concorrência: o ranking e a série", '<div class="pg-par">'
                   f'<div><h3>Ranking de {max(anos)}</h3><div class="pg-grafcard"><div class="pg-barras">{barras}</div></div>'
                   '<p class="pg-fonte">Clique no curso para ver todos os anos e as modalidades de cotas.</p></div>'
                   '<div><h3>Ano a ano</h3>' + tabela(f'<table><thead><tr><th>Curso</th>{cab}<th>Média 2 anos</th><th>Acertos (de 45)</th></tr></thead><tbody>{"".join(resumo)}</tbody></table>') + '</div>'
                   '</div>' + fonte, olho="Ranking e todos os anos")
             + "".join(blocos)
             + bloco("Simule a sua nota", '<p>No <a href="/simulador-pism/">simulador</a>, aba <b>IF Sudeste MG</b>, digite a sua nota e veja quantos acertos faltam para o curso que você quer.</p>', "pg-lilas")
             + faq
             + cta("Prepare-se para o IF com o Quarks", "Preparatório IF Sudeste presencial em Juiz de Fora: Física, Química, Português e Matemática, em turmas de até 10 alunos.", "Quero saber do Preparatório IF",
                   "Olá! Vi as notas de corte do IF no site e quero saber do Preparatório IF Sudeste do Quarks.", ("Ver o Preparatório IF", "/preparatorio-if-sudeste/")))
    escrever("nota-de-corte-if-sudeste", titulo=f"Nota de corte do IF Sudeste MG em Juiz de Fora ({min(anos)} a {max(anos)}) | Quarks Edu",
             descricao=f"Nota de corte dos cursos técnicos integrados do IF Sudeste MG, campus Juiz de Fora, de {min(anos)} a {max(anos)}: Desenvolvimento de Sistemas, Edificações, Eletromecânica, Eletrotécnica, Mecânica, Meio Ambiente e Metalurgia, por modalidade.",
             h1="Nota de corte do IF Sudeste MG em Juiz de Fora", selo=f"Técnicos integrados · {min(anos)} a {max(anos)}",
             lead="A nota do último classificado em cada curso técnico integrado do campus Juiz de Fora, ano a ano e por modalidade de cotas.",
             numeros=num((str(len(d["cursos"])), "cursos integrados"), ("45", "questões, 2 pontos cada"), ("90", "pontos possíveis")),
             visual=(capa_dado(f"{barras_if[0][0]['curso']} · ampla · {barras_if[0][2]}", br(barras_if[0][1]), "de 90",
                               f"{int(round(barras_if[0][1] / 2))} acertos de 45 · a nota mais alta do campus",
                               grafico([(str(a), (barras_if[0][0]["mod"]["AC"].get("cortes") or {}).get(str(a))) for a in anos]),
                               f'<span>{len(d["cursos"])} cursos integrados</span><a href="#{e(barras_if[0][0]["id"])}">Ver o curso →</a>') if barras_if else ""),
             corpo=corpo, trilha=[("Notas de corte do IF Sudeste", "/nota-de-corte-if-sudeste/")], prioridade="0.8",
             schemas=[fs, {"@type": "Dataset", "name": "Notas de corte dos técnicos integrados do IF Sudeste MG, campus Juiz de Fora",
                           "description": f"Nota do último classificado por curso e modalidade nos ingressos de {min(anos)} a {max(anos)}, a partir das classificações finais publicadas pelo IF Sudeste MG. Só números agregados.",
                           "creator": ORG, "temporalCoverage": f"{min(anos)}/{max(anos)}", "inLanguage": "pt-BR", "isAccessibleForFree": True, "dateModified": HOJE}])


def simulador_js(prova="pism1", curso=None):
    """curso: id do Banco de notas (ex.: juiz-de-fora-medicina-integral) para já abrir o simulador nele"""
    pre = ""
    if curso:
        pre = ("var n = 0, t = setInterval(function () { var s = el.querySelector('#qs-curso'); if (s && s.querySelector('option[value=\"" + curso + "\"]')) "
               "{ s.value = '" + curso + "'; s.dispatchEvent(new Event('change', { bubbles: true })); clearInterval(t); } else if (++n > 40) clearInterval(t); }, 150);")
    return (f'<script src="https://sistema.quarksedu.com.br/bancodenotas/simulador.js?v={SIM_V}" defer></script>\n'
            "<script>window.addEventListener('DOMContentLoaded', function () { var el = document.getElementById('simulador-quarks'); if (el && window.QuarksSimulador) "
            f"{{ window.QuarksSimulador.montar(el, {{ modo: 'site', prova: '{prova}' }}); {pre} }} else if (el) el.innerHTML = ''; }});</script>")


def pagina_simulador():
    perguntas = [
        ("O simulador do PISM é oficial?", "Não é da UFJF: é do Quarks, feito com as notas oficiais publicadas pela Copese/UFJF desde o triênio 2016-2018. É uma estimativa: cada ano tem a sua prova e a sua concorrência."),
        ("A minha nota fica guardada?", "Não. A nota digitada fica só na sua tela; nada sai do seu navegador."),
        ("Serve para o IF Sudeste?", "Sim, na aba IF Sudeste MG, com a nota de 0 a 90 e os cursos técnicos integrados do campus Juiz de Fora."),
    ]
    faq, fs = faq_html(perguntas)
    corpo = (bloco("Simule a sua aprovação", "<p style=\"max-width:72ch;margin-bottom:20px\">Escolha a prova: <b>PISM I</b> ou <b>PISM II</b> para ver onde você estaria entre quem fez aquele módulo, <b>Meu curso (PISM III)</b> para ver quanto precisa em cada módulo que falta, ou <b>IF Sudeste MG</b>.</p>"
                   '<div class="pg-simcard"><div id="simulador-quarks"></div></div>', "pg-lilas", olho="Simulador", id_="simulador")
             + bloco("Como a nota do PISM é calculada", '<div class="pg-pesos" role="img" aria-label="PISM I até 240, PISM II até 360, PISM III até 700, total 1.300"><div class="m1"><b>240</b><span>PISM I</span></div><div class="m2"><b>360</b><span>PISM II</span></div><div class="m3"><b>700</b><span>PISM III · total 1.300</span></div></div>'
                     '<p style="margin-top:20px;max-width:72ch">Nota final = PISM I × 0,20 + PISM II × 0,30 + PISM III × 0,50 (Resolução CONGRAD 340/2026). A UFJF publica com peso 2, 3 e 5: até 240, 360 e 700 pontos, total de 1.300. Veja o <a href="/pism/">guia do PISM 2027</a> e a <a href="/nota-de-corte-pism/">nota de corte de cada curso</a>.</p>', olho="Pesos")
             + faq
             + cta("Quero chegar lá", "O Quarks monta a trilha até a nota do seu curso, no Preparatório PISM online, com aulas ao vivo.", "Quero chegar lá com o Quarks",
                   "Olá! Fiz o simulador do site e quero saber como estudar no Quarks.", ("Preparatório PISM", "/preparatorio-pism/")))
    escrever("simulador-pism", titulo="Simulador do PISM (UFJF) e do IF Sudeste: quanto falta para o seu curso | Quarks Edu",
             descricao="Simulador do PISM da UFJF e do IF Sudeste MG com as notas oficiais desde 2016: veja onde você estaria entre os candidatos e quanto precisa em cada módulo para o seu curso.",
             h1="Simulador do PISM e do IF Sudeste", selo="Notas oficiais da UFJF e do IF",
             lead="Digite a sua nota e veja onde você estaria entre quem fez o PISM e quanto falta para o curso que você quer.",
             ctas='<div class="pg-ctas"><a class="btn am" href="#simulador">Começar a simulação</a><a class="pg-bt2" href="/nota-de-corte-pism/">Notas de corte</a></div>',
             visual=capa_foto("/site/img/ft-comemoracao.webp", "Aprovados e professores do Quarks comemorando", "50% 40%",
                              [("grafico", "Notas oficiais", "UFJF e IF Sudeste"), ("alvo", "Quanto falta", "para o seu curso")]),
             numeros=num(("Desde 2016", "notas oficiais"), ("72", "cursos da UFJF"), ("7", "cursos do IF")),
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
    # imagens de compartilhamento (WhatsApp/Instagram) feitas por scripts/gerar_og.js (node): usa as que existirem
    pasta_og = os.path.join(RAIZ, "site", "og")
    if os.path.isdir(pasta_og):
        for f in os.listdir(pasta_og):
            if f.endswith(".jpg"):
                OG[f[:-4].replace("--", "/")] = f[:-4]
    paginas_notas(a.gestao)   # antes do guia: preenche DESTAQUES
    paginas_servicos()
    pagina_aprovados()
    paginas_pism()
    paginas_if(a.gestao)
    pagina_simulador()
    pastas = sitemap()
    with open(os.path.join(RAIZ, "scripts", "og-paginas.json"), "w", encoding="utf-8") as f:
        json.dump(OG_LISTA, f, ensure_ascii=False, indent=0)
    print(f"{len(PAGINAS)} páginas em {len(pastas)} pastas: {', '.join(pastas)}")


if __name__ == "__main__":
    main()
