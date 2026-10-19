/* =====================================================================
   Site principal do Quarks: aplica os textos, listas e imagens mudados no painel da loja
   (loja.quarksedu.com.br/admin > Textos do site > Site principal; chaves "site.*") e liga o menu.
   Depois chama a vitrine (site/vitrine.js: órbita, ciclo da trilha, blocos escondidos).
   ===================================================================== */
(() => {
"use strict";
const LOJA = "https://loja.quarksedu.com.br";
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));
const prontos = []; let pronto = false;
window.Loja = { esc, aoCarregar: fn => pronto ? fn() : prontos.push(fn) };

const linkOk = v => /^(https?:\/\/|\/(?!\/)|#|mailto:|tel:)/i.test(v);
/* imagens: as enviadas pelo painel ficam na loja (capas/up/site-…); as originais, em site/img */
function caminhoImg(v){
  if (/^\/?capas\/up\/site-[a-z0-9-]+\.(webp|jpg)$/i.test(v)) return `${LOJA}/${v.replace(/^\//, "")}`;
  if (/^https:\/\/www\.quarksedu\.com\.br\/site\/img\/[a-z0-9_.-]+\.(webp|jpg|png)$/i.test(v)) return location.hostname.endsWith("quarksedu.com.br") ? v.replace(/^https:\/\/www\.quarksedu\.com\.br\//, "/") : v;
  return "";
}
function trocarImagem(img, v){ const c = caminhoImg(v); if (c) { img.removeAttribute("srcset"); img.src = c; } }
function preencher(raiz, campos, imagens){
  raiz.querySelectorAll("[data-c]").forEach(x => {
    const v = campos[x.dataset.c]; if (typeof v !== "string") return;
    if (x.tagName === "META") x.setAttribute("content", v);
    else if (x.tagName === "TITLE") document.title = v;
    else { x.textContent = v; x.hidden = v.trim() === ""; }
  });
  raiz.querySelectorAll("[data-c-href]").forEach(x => { const v = campos[x.dataset.cHref]; if (typeof v === "string" && v && linkOk(v)) x.setAttribute("href", v); });
  raiz.querySelectorAll("[data-c-img]").forEach(x => { const v = imagens[x.dataset.cImg]; if (typeof v === "string" && v) trocarImagem(x, v); });
}
function aplicar(c){
  const campos = c.campos || {}, listas = c.listas || {}, imagens = c.imagens || {};
  document.querySelectorAll("[data-lista]").forEach(box => {
    const itens = listas[box.dataset.lista]; if (!Array.isArray(itens)) return;
    const modelos = [...box.children].filter(x => x.hasAttribute("data-item")); if (!modelos.length) return;
    const novos = itens.map((it, i) => {
      const el = modelos[i % modelos.length].cloneNode(true), com = (a) => [...(el.hasAttribute(a) ? [el] : []), ...el.querySelectorAll(`[${a}]`)];
      com("data-f").forEach(x => { const v = it[x.dataset.f]; if (typeof v === "string") { x.textContent = v; x.hidden = v.trim() === ""; } });
      com("data-f-href").forEach(x => { const v = it[x.dataset.fHref]; if (typeof v === "string" && v && linkOk(v)) x.setAttribute("href", v); });
      com("data-f-img").forEach(x => { const v = it[x.dataset.fImg]; if (typeof v === "string" && v) { trocarImagem(x, v); const nome = el.querySelector("[data-f='f0']"); if (nome && x.alt !== undefined) x.alt = nome.textContent; } });
      return el;
    });
    modelos[0].before(...novos); modelos.forEach(m => m.remove());
    box.hidden = !novos.length;
  });
  preencher(document, campos, imagens);
}

/* faixa dos aprovados: repete a lista para a passagem não ter emenda */
function duplicarAprovados(){
  document.querySelectorAll(".aprov-trilho").forEach(t => {
    [...t.children].forEach(f => { const c = f.cloneNode(true); c.setAttribute("aria-hidden", "true"); c.querySelectorAll("img").forEach(i => i.alt = ""); t.appendChild(c); });
  });
}

/* menu do celular */
function menu(){
  const h = document.querySelector(".hamb"), m = document.getElementById("menu"); if (!h || !m) return;
  h.addEventListener("click", () => { const a = m.classList.toggle("aberto"); h.setAttribute("aria-expanded", a); });
  m.addEventListener("click", e => { if (e.target.closest("a")) { m.classList.remove("aberto"); h.setAttribute("aria-expanded", "false"); } });
}

async function iniciar(){
  menu();
  try {
    const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), 4000);
    const r = await fetch(`${LOJA}/conteudo.php`, { cache:"no-cache", signal:ctl.signal }); clearTimeout(t);
    if (r.ok) aplicar(await r.json());
  } catch (e) { /* sem a loja, o site mostra os textos originais */ }
  duplicarAprovados();
  pronto = true; prontos.splice(0).forEach(fn => { try { fn(); } catch (e) { console.error(e); } });
}
document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", iniciar) : iniciar();
})();

/* Acompanhamento Escolar (19/10/2026): "Quero conhecer" e "Ver horários" abrem uma janela com a explicação e um pedido curto,
   enviado pelo WhatsApp da coordenação (nada fica guardado no site). Sem JavaScript, os botões continuam indo direto ao WhatsApp. */
function janelas(){
  const zap = (a) => ((a && a.getAttribute("href") || "").match(/wa\.me\/(\d{10,13})/) || [])[1] || "5532998057212";
  document.querySelectorAll("[data-janela]").forEach((a) => a.addEventListener("click", (e) => {
    const j = document.getElementById("j-" + a.dataset.janela); if (!j || !j.showModal) return;
    e.preventDefault(); j.dataset.zap = zap(a); j.showModal(); j.scrollTop = 0; document.documentElement.classList.add("sem-rolar");
  }));
  document.querySelectorAll("dialog.janela").forEach((j) => {
    j.addEventListener("close", () => document.documentElement.classList.remove("sem-rolar"));
    j.addEventListener("click", (e) => { if (e.target === j || e.target.closest("[data-fechar]")) j.close(); });
    j.querySelectorAll("[data-hor]").forEach((b) => b.addEventListener("click", () => {
      j.querySelectorAll("[data-hor]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      const sel = j.querySelector("select[name=horario]"); if (sel) sel.value = b.dataset.hor;
      const f = j.querySelector("form"); if (f) f.scrollIntoView({ behavior: "smooth", block: "start" });
    }));
    const f = j.querySelector("form[data-form-acomp]"); if (!f) return;
    f.addEventListener("submit", (e) => {
      e.preventDefault(); const d = new FormData(f), erro = f.querySelector(".jf-erro"), disc = d.getAll("disc");
      const falta = [["aluno", "o nome do aluno"], ["escola", "a escola"], ["ano", "o ano escolar"]].filter(([k]) => !String(d.get(k) || "").trim()).map((x) => x[1]);
      if (!disc.length) falta.push("ao menos uma disciplina");
      if (falta.length) { erro.textContent = "Falta preencher " + falta.join(", ") + "."; erro.hidden = false; return; }
      erro.hidden = true;
      const linhas = ["Olá! " + d.get("interesse") + " (Acompanhamento Escolar).", "", "Aluno: " + d.get("aluno").trim(), "Escola: " + d.get("escola").trim(), "Ano escolar: " + d.get("ano"), "Disciplinas: " + disc.join(", ")];
      if (d.get("horario")) linhas.push("Horário de preferência: " + d.get("horario"));
      window.open("https://wa.me/" + (j.dataset.zap || "5532998057212") + "?text=" + encodeURIComponent(linhas.join("\n")), "_blank", "noopener");
    });
  });
}
document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", janelas) : janelas();
