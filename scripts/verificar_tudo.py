#!/usr/bin/env python3
"""Verificação do site principal do Quarks (rode antes de publicar; a trava do push e o GitHub rodam sozinhos).

    python3 scripts/verificar_tudo.py              # confere tudo (não grava nada no repositório, não usa internet)
    python3 scripts/verificar_tudo.py --publicar   # o mesmo, do jeito que a trava do push chama (scripts/ganchos/pre-push)
    python3 scripts/verificar_tudo.py --gestao CAMINHO   # pasta do quarks-gestao (padrão: ../quarks-gestao)

Só usa a biblioteca padrão do Python. O node é usado para conferir o JavaScript (sem ele, vira aviso).
Sai com código 1 se alguma verificação falhar; avisos não bloqueiam.
Ao rodar, liga a trava do push deste clone (git config core.hooksPath scripts/ganchos).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # não deixa __pycache__/ no repositório
RAIZ = Path(__file__).resolve().parent.parent
FALHAS, AVISOS = [], []

# Pastas de outros sistemas no public_html: página do site nunca pode usar estes nomes (CLAUDE.md).
PROIBIDAS = ["familia", "lab", "labaluno", "labprof", "loja", "minhacasa", "portal", "prof", "quarks-backups", "sistema"]
FIXOS = ["index.html", "robots.txt", "sitemap.xml", ".htaccess"]   # arquivos soltos que o publicar.yml envia
PASTAS_FIXAS = ["site", "privacidade", "termos"]                   # pastas que o publicar.yml envia sempre
DOMINIO = "https://www.quarksedu.com.br"

# Pendências conhecidas: problema real de página que já está no ar e espera decisão do dono. Vira aviso, não falha.
# Formato: "pagina -> destino" (links) ou o texto exato do achado. Resolveu? Tire daqui.
PENDENCIAS_CONHECIDAS = set()


def ok(n): print("ok     " + n)
def aviso(n): AVISOS.append(n); print("aviso  " + n)
def falha(n, d=""): FALHAS.append(n); print("FALHA  " + n + (f"\n       {d}" if d else ""))
def rodar(c, **k): return subprocess.run(c, capture_output=True, text=True, **k)
def ler(p): return Path(p).read_text(encoding="utf-8", errors="replace")
def rel(p): return str(Path(p).relative_to(RAIZ))


def resultado(nome, erros, limite=25):
    """erros que estão em PENDENCIAS_CONHECIDAS viram aviso; os outros reprovam."""
    conhecidos = [x for x in erros if x in PENDENCIAS_CONHECIDAS]
    novos = [x for x in erros if x not in PENDENCIAS_CONHECIDAS]
    for x in conhecidos:
        aviso(f"pendência conhecida: {x}")
    if novos:
        falha(nome, "\n       ".join(novos[:limite]) + (f"\n       ... e mais {len(novos) - limite}" if len(novos) > limite else ""))
    else:
        ok(nome)


def arquivos_git():
    r = rodar(["git", "ls-files", "-z"], cwd=RAIZ)
    if r.returncode != 0:
        return [p for p in RAIZ.rglob("*") if p.is_file() and ".git" not in p.parts]
    return [RAIZ / l for l in r.stdout.split("\0") if l and (RAIZ / l).is_file()]


def fora_do_backup(p):
    return Path(rel(p)).parts[0] != "backup"


def pastas_paginas():
    f = RAIZ / "paginas.txt"
    return ler(f).split() if f.is_file() else []


def publicados():
    """arquivos que o publicar.yml envia para a Hostinger."""
    out = [RAIZ / f for f in FIXOS if (RAIZ / f).is_file()]
    for pasta in PASTAS_FIXAS + pastas_paginas():
        if (RAIZ / pasta).is_dir():
            out += [p for p in (RAIZ / pasta).rglob("*") if p.is_file()]
    return out


def instalar_trava():
    """liga a trava do push neste clone (o git não copia ganchos sozinho)."""
    gancho = RAIZ / "scripts" / "ganchos" / "pre-push"
    if not gancho.is_file() or not (RAIZ / ".git").exists():
        return
    if rodar(["git", "config", "--get", "core.hooksPath"], cwd=RAIZ).stdout.strip() != "scripts/ganchos":
        if rodar(["git", "config", "core.hooksPath", "scripts/ganchos"], cwd=RAIZ).returncode == 0:
            print("trava instalada: todo push para o main passa antes por esta verificação\n")


# ---------------------------------------------------------------- conferências
def v_paginas_txt():
    pastas = pastas_paginas()
    erros = []
    if not pastas:
        erros.append("paginas.txt vazio ou ausente")
    for p in pastas:
        if p in PROIBIDAS or p in PASTAS_FIXAS or p in ("backup", "scripts") or p.startswith(".") or "/" in p or ".." in p:
            erros.append(f"paginas.txt: '{p}' é pasta de outro sistema ou reservada (a publicação sobrescreveria)")
        elif not (RAIZ / p / "index.html").is_file():
            erros.append(f"paginas.txt: a pasta '{p}' não existe ou não tem index.html")
    na_raiz = [p.name for p in RAIZ.iterdir() if p.is_dir() and p.name in PROIBIDAS]
    erros += [f"a pasta '{n}/' é de outro sistema e não pode existir neste repositório" for n in na_raiz]
    resultado(f"paginas.txt: {len(pastas)} pastas, todas existem e nenhuma é de outro sistema", erros)


def sem_data(s):
    """a data do dia entra no sitemap e nos dados para o Google; não conta como diferença."""
    return re.sub(r'("dateModified": ?"|<lastmod>)\d{4}-\d\d-\d\d', r"\1DATA", s)


def v_geradas(gestao):
    """roda o gerador numa cópia e compara: página editada à mão ou gerador sem rodar aparecem aqui."""
    if not (Path(gestao) / "bancodenotas" / "pism.json").is_file():
        return aviso(f"páginas geradas NÃO conferidas contra o gerador: falta o Banco de notas da gestão em {gestao} (use --gestao CAMINHO)")
    pastas = pastas_paginas()
    with tempfile.TemporaryDirectory(prefix="qsite-") as tmp:
        tmp = Path(tmp)
        for p in arquivos_git():
            if fora_do_backup(p):
                d = tmp / rel(p); d.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, d)
        r = rodar([sys.executable, "-B", "scripts/gerar_paginas.py", "--gestao", str(Path(gestao).resolve())], cwd=tmp)
        if r.returncode != 0:
            return falha("gerador de páginas roda sem erro", (r.stdout + r.stderr).strip()[-800:])
        erros = []
        novas = ler(tmp / "paginas.txt").split()
        conferir = {"sitemap.xml", "paginas.txt", "scripts/og-paginas.json"}
        for base in (tmp, RAIZ):
            for pasta in set(pastas) | set(novas):
                if (base / pasta).is_dir():
                    conferir |= {str(q.relative_to(base)) for q in (base / pasta).rglob("*") if q.is_file()}
        for c in sorted(conferir):
            a, b = RAIZ / c, tmp / c
            if not a.is_file():
                erros.append(f"{c}: o gerador cria, mas não está no repositório")
            elif not b.is_file():
                erros.append(f"{c}: está no repositório, mas o gerador não cria mais (sobrou)")
            elif sem_data(ler(a)) != sem_data(ler(b)):
                erros.append(f"{c}: diferente do que o gerador faz (editado à mão ou gerador sem rodar)")
    if erros:
        erros.append("conserto: mude o scripts/gerar_paginas.py e rode python3 scripts/gerar_paginas.py")
    resultado(f"páginas geradas, sitemap.xml e paginas.txt iguais ao que o gerador faz ({len(conferir)} arquivos)", erros, 12)


def v_sitemap():
    s = ler(RAIZ / "sitemap.xml")
    locs = re.findall(r"<loc>([^<]+)</loc>", s)
    erros = []
    caminhos = set()
    for l in locs:
        if not l.startswith(DOMINIO + "/") or not l.endswith("/"):
            erros.append(f"sitemap: endereço fora do padrão: {l}"); continue
        c = l[len(DOMINIO):].strip("/")
        caminhos.add(c)
        if not (RAIZ / c / "index.html").is_file():
            erros.append(f"sitemap: /{c}/ não existe no repositório")
    if len(locs) != len(set(locs)):
        erros.append("sitemap: endereço repetido")
    esperadas = {""} | {p for p in ("privacidade", "termos")}
    for pasta in pastas_paginas():
        esperadas |= {str(q.parent.relative_to(RAIZ)) for q in (RAIZ / pasta).rglob("index.html")}
    erros += [f"sitemap: falta a página /{c}/" for c in sorted(esperadas - caminhos)]
    erros += [f"sitemap: /{c}/ não é página publicada" for c in sorted(caminhos - esperadas)]
    resultado(f"sitemap.xml lista exatamente as {len(esperadas)} páginas publicadas", erros)


RX_LINK = re.compile(r"""(?<![\w-])(?:href|src|poster|data-src)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
RX_SRCSET = re.compile(r"""(?<![\w-])srcset\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)


def destinos(html):
    sem_script = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)   # link montado por JavaScript não dá para conferir
    out = [a or b for a, b in RX_LINK.findall(sem_script)]
    for a, b in RX_SRCSET.findall(sem_script):
        out += [x.strip().split()[0] for x in (a or b).split(",") if x.strip()]
    return out


def v_links():
    """todo link, imagem, CSS e JS interno das páginas publicadas aponta para arquivo que existe."""
    pub = {rel(p) for p in publicados()}
    erros, n = [], 0
    for p in publicados():
        if p.suffix != ".html":
            continue
        pagina = rel(p)
        for d in sorted(set(destinos(ler(p)))):
            d = d.strip()
            if d.startswith(DOMINIO):
                d = d[len(DOMINIO):] or "/"
            if not d or d.startswith(("#", "//", "data:", "mailto:", "tel:", "javascript:", "{", "$")) or re.match(r"[a-z][a-z0-9+.-]*:", d, re.I):
                continue
            caminho = re.split(r"[?#]", d, maxsplit=1)[0]
            if not caminho:
                continue
            alvo = caminho.lstrip("/") if caminho.startswith("/") else os.path.normpath(os.path.join(os.path.dirname(pagina), caminho))
            alvo = os.path.normpath(alvo) if alvo else ""
            if alvo.split("/")[0] in PROIBIDAS:   # endereço de outro sistema no mesmo domínio: não é deste repositório
                continue
            n += 1
            if alvo in ("", "."):
                alvo = "index.html"
            elif caminho.endswith("/") or (RAIZ / alvo).is_dir():
                alvo = alvo.rstrip("/") + "/index.html"
            if alvo not in pub:
                erros.append(f"{pagina} -> {d}")
    resultado(f"links, imagens, CSS e JS internos das páginas publicadas existem ({n} conferidos)", erros)


def scripts_embutidos(html):
    out = []
    for m in re.finditer(r"<script\b([^>]*)>(.*?)</script>", html, re.S | re.I):
        attrs = m.group(1) or ""
        t = re.search(r"""\btype\s*=\s*["']?([^"'\s>]+)""", attrs, re.I)
        tipo = t.group(1).lower() if t else "text/javascript"
        if re.search(r"\bsrc\s*=", attrs, re.I) or tipo not in ("text/javascript", "application/javascript", "module"):
            continue   # JSON-LD e arquivos de fora ficam de fora
        if m.group(2).strip():
            out.append((m.group(2), tipo == "module"))
    return out


def v_javascript():
    if not shutil.which("node"):
        return aviso("JavaScript NÃO conferido: node não encontrado neste computador")
    erros, n = [], 0
    with tempfile.TemporaryDirectory(prefix="qsite-js-") as tmp:
        for p in publicados() + [q for q in arquivos_git() if rel(q).startswith("scripts/")]:
            if p.suffix == ".js":
                n += 1
                r = rodar(["node", "--check", str(p)])
                if r.returncode != 0:
                    erros.append(f"{rel(p)}: {r.stderr.strip()[:400]}")
            elif p.suffix == ".html":
                for i, (js, modulo) in enumerate(scripts_embutidos(ler(p))):
                    f = Path(tmp) / (f"s{n}." + ("mjs" if modulo else "js")); f.write_text(js, encoding="utf-8"); n += 1
                    r = rodar(["node", "--check", str(f)])
                    if r.returncode != 0:
                        erros.append(f"{rel(p)}, script {i + 1}: {r.stderr.strip()[:400]}")
    resultado(f"JavaScript sem erro de escrita ({n} arquivos e scripts dentro das páginas)", erros)


def textos():
    exts = {".html", ".css", ".js", ".py", ".md", ".txt", ".xml", ".json", ".yml", ".yaml", ".sh", ".htaccess", ".svg", ".webmanifest", ""}
    for p in arquivos_git():
        if fora_do_backup(p) and (p.suffix.lower() in exts or p.name.startswith(".")) and p.stat().st_size < 3_000_000:
            yield p, ler(p)


def v_nome():
    rx = re.compile(r"\b(?:[dn]?a|à|pela|toda a|nossa|essa|esta|uma)\s+Quarks\b(?!\s+Edu\s+Ltda)", re.I)
    eu = Path(__file__).resolve()
    erros = []
    for p, s in textos():
        if p.resolve() == eu or p.name in ("CLAUDE.md",):
            continue
        for i, l in enumerate(s.splitlines()):
            m = rx.search(l)
            if m:
                erros.append(f"{rel(p)}:{i + 1}: \"{l[max(0, m.start() - 30):m.end() + 20].strip()}\"")
    resultado("o nome é masculino em todo lugar (o Quarks, do Quarks, no Quarks)", erros)


def v_segredos():
    padroes = [("chave da Anthropic", r"sk-ant-[A-Za-z0-9_-]{20,}"), ("chave do Asaas", r"\$aact_[A-Za-z0-9_=-]{20,}"),
               ("token do GitHub", r"\b(?:gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{30,})"), ("chave da AWS", r"\bAKIA[0-9A-Z]{16}\b"),
               ("chave privada", "-----BEGIN (?:RSA |EC |OPENSSH )?" + "PRIVATE KEY-----"),
               ("senha de FTP escrita", r"(?i)\b(?:FTP_SENHA|FTP_PASSWORD|ftp_pass(?:word)?)\b\s*[:=]\s*['\"]?(?!\$\{\{)[^\s'\"$]{6,}"),
               ("endereço de FTP com senha", r"(?i)\bftps?://[^\s:/@]+:[^\s@/]+@")]
    erros = []
    for p in arquivos_git():
        r = rel(p)
        if p.name == "config.php" or p.suffix in (".sqlite", ".sqlite3", ".db", ".pem", ".key") or p.name.startswith(".env") or p.name == ".ftp-deploy-sync-state.json":
            erros.append(f"{r} não pode estar no git")
        if "__pycache__" in p.parts or p.suffix == ".pyc":
            erros.append(f"{r}: arquivo temporário do Python no git")
    eu = Path(__file__).resolve()
    for p in arquivos_git():   # aqui o backup/ também entra: o repositório é público
        if p.resolve() == eu or p.stat().st_size > 8_000_000 or p.suffix.lower() in (".webp", ".jpg", ".jpeg", ".png", ".woff2", ".woff", ".ico", ".avif", ".mp4", ".pdf"):
            continue
        s = ler(p)
        erros += [f"{nome} em {rel(p)}" for nome, rx in padroes if re.search(rx, s)]
    resultado("sem chaves, senhas ou arquivos proibidos no repositório (ele é público)", erros)


def v_conflitos():
    erros = [f"{rel(p)}:{i + 1}" for p, s in textos() for i, l in enumerate(s.splitlines()) if l.startswith(("<" * 7 + " ", ">" * 7 + " ")) or l == "=" * 7]
    resultado("sem marcadores de conflito de merge", erros)


def v_publicar_yml():
    """o envio leva só o que o CLAUDE.md diz e a verificação roda antes dele."""
    f = RAIZ / ".github" / "workflows" / "publicar.yml"
    if not f.is_file():
        return falha("publicar.yml existe")
    s = ler(f)
    corpo = "\n".join(l for l in s.splitlines() if not l.lstrip().startswith("#"))
    erros = []
    m = re.search(r"- name: Separar só os arquivos do site\s*\n\s*run: \|\n(.*?)(?=\n\s*- (?:name|uses):|\Z)", corpo, re.S)
    if not m:
        erros.append("publicar.yml: não achei o passo 'Separar só os arquivos do site'")
    else:
        linhas = [re.sub(r"\s+#.*$", "", l).strip() for l in m.group(1).splitlines() if l.strip()]
        esperado = ["mkdir _publicar", "cp " + " ".join(FIXOS) + " _publicar/",
                    'for p in $(cat paginas.txt); do cp -r "$p" _publicar/; done', "cp -r " + " ".join(PASTAS_FIXAS) + " _publicar/"]
        if linhas != esperado:
            erros.append("publicar.yml: o passo que separa os arquivos mudou. Esperado:\n         " + "\n         ".join(esperado) + "\n       Está:\n         " + "\n         ".join(linhas))
    if not re.search(r"local-dir:\s*\./_publicar/", corpo):
        erros.append("publicar.yml: o envio tem de sair só da pasta ./_publicar/")
    if not re.search(r"dangerous-clean-slate:\s*false", corpo):
        erros.append("publicar.yml: dangerous-clean-slate tem de ser false (senão apaga as pastas dos outros sistemas)")
    if not re.search(r"protocol:\s*ftps", corpo):
        erros.append("publicar.yml: o envio tem de ser por FTPS (senha cifrada)")
    iv, ie = corpo.find("scripts/verificar_tudo.py"), corpo.find("FTP-Deploy-Action")
    if iv < 0 or ie < 0 or iv > ie:
        erros.append("publicar.yml: a verificação (scripts/verificar_tudo.py) tem de rodar antes do envio por FTP")
    for n in re.findall(r"secrets\.([A-Z_]+)", corpo):
        if n not in ("FTP_SERVIDOR", "FTP_USUARIO", "FTP_SENHA", "FTP_PASTA"):
            erros.append(f"publicar.yml: segredo desconhecido {n}")
    ht = "\n".join(l for l in ler(RAIZ / ".htaccess").splitlines() if l.strip() and not l.lstrip().startswith("#"))
    if re.sub(r"\s+", " ", ht).strip() != '<Files ".ftp-deploy-sync-state.json"> Require all denied </Files>':
        erros.append(".htaccess: ele fica na raiz do public_html e vale para os outros sistemas; só pode ter a regra que fecha o .ftp-deploy-sync-state.json")
    resultado("publicar.yml envia só os arquivos do site, por FTPS, depois da verificação; .htaccess só com a regra combinada", erros)


def v_troca_de_nome():
    """--publicar: CSS ou JS do site que mudou em relação ao que está no ar precisa de nome novo (o cache guarda 7 dias)."""
    base = os.environ.get("QK_PUBLICAR_BASE", "").strip()
    if not base or set(base) == {"0"}:
        base = "origin/main"
    if rodar(["git", "cat-file", "-e", base + "^{commit}"], cwd=RAIZ).returncode != 0:
        return aviso(f"troca de nome de CSS/JS não conferida: não achei o que está no ar ({base[:12]}) neste clone")
    r = rodar(["git", "diff", "--name-status", "--no-renames", base, "--", "site"], cwd=RAIZ)
    mudados = [l.split("\t", 1)[1] for l in r.stdout.splitlines() if l.startswith("M\t") and l.endswith((".css", ".js"))]
    usados = "\n".join(ler(p) for p in publicados() if p.suffix == ".html")
    erros = [f"{f} mudou sem trocar de nome e as páginas ainda apontam para ele: quem já visitou o site fica até 7 dias com o arquivo antigo (crie um nome novo, ex.: site/nome-AAAAMMDD.css, e atualize as referências)"
             for f in mudados if "/" + f in usados]
    resultado("CSS e JS do site que mudaram trocaram de nome (cache de 7 dias da Hostinger)", erros)


def main():
    args = sys.argv[1:]
    gestao = args[args.index("--gestao") + 1] if "--gestao" in args and args.index("--gestao") + 1 < len(args) else str(RAIZ.parent / "quarks-gestao")
    print(f"Verificação do site do Quarks em {RAIZ}\n")
    instalar_trava()
    passos = [v_paginas_txt, lambda: v_geradas(gestao), v_sitemap, v_links, v_javascript, v_nome, v_segredos, v_conflitos, v_publicar_yml]
    if "--publicar" in args:
        passos.append(v_troca_de_nome)
    for v in passos:
        try:
            v()
        except Exception as e:  # noqa: BLE001  (uma conferência quebrada não pode esconder as outras)
            falha(getattr(v, "__name__", "verificação"), f"erro ao verificar: {e!r}")
    print()
    if FALHAS:
        print(f"{len(FALHAS)} verificação(ões) FALHARAM. Corrija antes de publicar o site.")
        sys.exit(1)
    print("Tudo certo." + (f" ({len(AVISOS)} aviso(s))" if AVISOS else ""))


if __name__ == "__main__":
    main()
