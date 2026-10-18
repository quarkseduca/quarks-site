/* =====================================================================
   Vitrine do Quarks (desenho aprovado em 18/10/2026): partes que se mexem nas páginas da loja.
   - órbita do topo (.orbita): os itens giram com profundidade; o da frente aparece no cartão ao lado;
   - escolha da prova (.pvt button[data-pv]): mostra o painel .pvp daquela prova e lembra a escolha;
   - ciclo da trilha (.ciclo): etapa ativa gira sozinha, com a tela de verdade ao lado;
   - blocos que o dono escondeu no painel: campo "mostrar" = "não".
   Os textos vêm das páginas e do painel (window.Loja aplica antes). Carrinho e pagamento ficam no loja.js.
   ===================================================================== */
(() => {
"use strict";
const L = window.Loja || {};
const calmo = matchMedia("(prefers-reduced-motion: reduce)").matches;
const TAU = Math.PI * 2;
const PROVA_SALVA = "quarks-prova";
const tocar = v => { v.muted = true; v.preload = "auto"; const p = v.play(); if (p && p.catch) p.catch(() => {}); };

/* ---------- blocos escondidos pelo painel ---------- */
function esconderBlocos(){
  document.querySelectorAll('.so-painel[data-c$=".mostrar"]').forEach(s => {
    const sec = s.closest("[data-sec]"); if (!sec) return;
    sec.hidden = /^\s*n(ã|a)o\s*$/i.test(s.textContent);
  });
}

/* ---------- órbita ---------- */
const ORBS = [];
const norm = a => { while (a > Math.PI) a -= TAU; while (a < -Math.PI) a += TAU; return a; };
function iniciarOrbitas(){
  document.querySelectorAll(".orbita").forEach(o => {
    if (o.dataset.ok) return; o.dataset.ok = "1";
    const nos = [...o.querySelectorAll(".orb-no")].filter(n => !n.hidden);
    const st = { o, nos, t:Math.PI / 2, v:+(o.dataset.vel || .14), alvo:null, frente:-1, pausaAte:0, hover:false, eles:[], W:0, H:0 };
    [...o.querySelectorAll(".orb-el")].forEach((e, k) => {
      const r = []; for (let j = 0; j < 7; j++) { const d = document.createElement("i"); d.className = "orb-rastro"; o.appendChild(d); r.push(d); }
      st.eles.push({ el:e, r:+(e.dataset.r || .6), v:+(e.dataset.v || 1), a:k * 2.1, hist:[], rastro:r });
    });
    o.addEventListener("mouseenter", () => st.hover = true);
    o.addEventListener("mouseleave", () => st.hover = false);
    nos.forEach((n, i) => { const b = n.querySelector("button") || n; b.addEventListener("click", () => { st.alvo = i; st.pausaAte = performance.now() + 6000; }); });
    if (nos.length) ORBS.push(st);
  });
}
function arco(cx, cy, rx, ry, tl, a0, a1){
  let s = ""; const n = 48;
  for (let k = 0; k <= n; k++) { const a = a0 + (a1 - a0) * k / n, x = rx * Math.cos(a), y = ry * Math.sin(a);
    const X = cx + x * Math.cos(tl) - y * Math.sin(tl), Y = cy + x * Math.sin(tl) + y * Math.cos(tl); s += (k ? "L" : "M") + X.toFixed(1) + " " + Y.toFixed(1); }
  return s;
}
function trilhas(st, cx, cy, rx, ry, tl){
  const ri = st.eles.length ? st.eles[0].r : 0;
  [st.o.querySelector(".orb-tras"), st.o.querySelector(".orb-frente")].forEach((sv, k) => {
    if (!sv) return;
    sv.setAttribute("viewBox", `0 0 ${st.W} ${st.H}`);
    const a0 = k ? 0 : Math.PI, a1 = k ? Math.PI : TAU;
    let h = `<path d="${arco(cx, cy, rx, ry, tl, a0, a1)}"/>`;
    if (ri) h += `<path class="in" d="${arco(cx, cy, rx * ri, ry * ri, tl, a0, a1)}"/>`;
    sv.innerHTML = h;
  });
}
/* o cartão ao lado da órbita mostra o item da frente (textos escondidos dentro de cada item: .orb-d) */
function cartao(st, i){
  const raiz = st.o.closest("[data-orb-raiz]") || document, n = st.nos[i]; if (!n) return;
  if (st.o.dataset.tinge && n.dataset.cor) { raiz.style.setProperty("--tinta", n.dataset.cor); raiz.style.setProperty("--tinta-clara", n.dataset.clara); }
  if (n.dataset.video) {
    const v = raiz.querySelector("[data-orb-video]");
    if (v && v.getAttribute("src") !== n.dataset.video) { v.setAttribute("poster", n.dataset.poster || ""); v.setAttribute("src", n.dataset.video); if (!calmo) tocar(v); }
    const rt = raiz.querySelector("[data-orb-rot]"); const tt = n.querySelector(".orb-d b"); if (rt && tt) rt.textContent = tt.textContent;
  }
  const c = raiz.querySelector("[data-orb-card]"), d = n.querySelector(".orb-d"); if (!c || !d) return;
  const txt = s => { const x = d.querySelector(s); return x && !x.hidden ? x.textContent.trim() : ""; };
  const img = n.querySelector(".fo img") || n.querySelector("button img"), link = d.querySelector("a");
  const esc = L.esc || (s => String(s));
  const pr = txt("em"), nota = txt("small");
  const fo = n.querySelector(".fo");
  c.innerHTML = `<span class="ic">${img ? `<img src="${esc(img.getAttribute("src"))}" alt="">` : (fo ? `<span class="ic-t${fo.classList.contains("r") ? " r" : ""}">${esc(fo.textContent)}</span>` : "")}</span><span class="tx"><b>${esc(txt("b"))}</b><span>${esc(txt("span"))}</span></span>` +
    (pr ? `<span class="pr">${esc(pr)}<small>${esc(nota)}</small></span>` : "") + `<span class="ir" aria-hidden="true">›</span>`;
  if (c.tagName === "A" && link) { c.setAttribute("href", link.getAttribute("href")); c.setAttribute("aria-label", txt("b")); }
}
function desenhar(st, dt, agora){
  const o = st.o; if (!o.offsetParent) return;
  const W = o.offsetWidth, H = o.offsetHeight; if (!W || !H) return;
  const cel = W < 460;
  const cx = W / 2, cy = H / 2, rx = W * +((cel && o.dataset.rxCel) || o.dataset.rx || .4), ry = rx * +((cel && o.dataset.ratioCel) || o.dataset.ratio || .4), tl = (+o.dataset.tilt || 0) * Math.PI / 180;
  if (st.W !== W || st.H !== H) { st.W = W; st.H = H; trilhas(st, cx, cy, rx, ry, tl); }
  const N = st.nos.length, passo = TAU / N;
  if (st.alvo !== null) {
    const d = norm(Math.PI / 2 - st.alvo * passo - st.t);
    st.t += calmo ? d : d * Math.min(1, dt * 3.5);
    if (Math.abs(d) < .003) st.alvo = null;
  } else if (!calmo) {
    const lento = st.hover || agora < st.pausaAte; st.t += (lento ? st.v * .12 : st.v) * dt;
  }
  let melhor = -1, md = -9;
  st.nos.forEach((n, i) => {
    const a = st.t + i * passo, x = rx * Math.cos(a), y = ry * Math.sin(a);
    const X = cx + x * Math.cos(tl) - y * Math.sin(tl), Y = cy + x * Math.sin(tl) + y * Math.cos(tl);
    const p = Math.sin(a), q = (p + 1) / 2, s = .62 + .42 * q;
    n.style.transform = `translate(${X.toFixed(1)}px,${Y.toFixed(1)}px) translate(-50%,-50%) scale(${s.toFixed(3)})`;
    n.style.zIndex = p > 0 ? (10 + Math.round(p * 10)) : (2 + Math.round(q * 2));
    n.style.opacity = (.66 + .34 * q).toFixed(2);
    n.style.filter = p < -.5 ? "saturate(.8)" : "none";
    if (p > md) { md = p; melhor = i; }
  });
  if (melhor !== st.frente) { st.frente = melhor; st.nos.forEach((n, i) => n.classList.toggle("na-frente", i === melhor)); cartao(st, melhor); }
  st.eles.forEach(e => {
    if (!calmo) e.a += e.v * dt;
    const x = rx * e.r * Math.cos(e.a), y = ry * e.r * Math.sin(e.a);
    const X = cx + x * Math.cos(tl) - y * Math.sin(tl), Y = cy + x * Math.sin(tl) + y * Math.cos(tl), p = Math.sin(e.a);
    e.el.style.transform = `translate(${X.toFixed(1)}px,${Y.toFixed(1)}px)`; e.el.style.zIndex = p > 0 ? 9 : 1;
    e.hist.unshift([X, Y, p]); if (e.hist.length > 40) e.hist.pop();
    e.rastro.forEach((r, j) => { const h = e.hist[Math.min(e.hist.length - 1, (j + 1) * 4)]; if (!h) return;
      r.style.transform = `translate(${h[0].toFixed(1)}px,${h[1].toFixed(1)}px) scale(${(1 - j * .12).toFixed(2)})`;
      r.style.opacity = calmo ? 0 : (.5 - j * .07).toFixed(2); r.style.zIndex = h[2] > 0 ? 9 : 1; });
  });
}
let ult = performance.now(), rodando = false;
function laco(t){ const dt = Math.min(.05, (t - ult) / 1000); ult = t; if (!document.hidden) ORBS.forEach(st => desenhar(st, dt, t)); requestAnimationFrame(laco); }

/* ---------- escolha da prova ---------- */
const V = window.Vitrine = { prova:"", aoTrocarProva:[] };
function escolherProva(id, rolar){
  const grupos = [...document.querySelectorAll(".pvt")]; if (!grupos.length) return;
  const validas = [...document.querySelectorAll(".pvt button[data-pv]")].map(b => b.dataset.pv);
  if (!validas.includes(id)) id = validas[0];
  V.prova = id;
  document.querySelectorAll(".pvt button[data-pv]").forEach(b => { const on = b.dataset.pv === id; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
  document.querySelectorAll(".pvp[data-pv]").forEach(p => {
    p.hidden = p.dataset.pv !== id;
    p.querySelectorAll("video").forEach(v => { if (p.hidden) v.pause(); else if (!calmo) tocar(v); });
  });
  document.querySelectorAll("[data-pv-nome]").forEach(s => { const b = document.querySelector(`.pvt button[data-pv="${id}"] b`); if (b) s.textContent = b.textContent; });
  try { localStorage.setItem(PROVA_SALVA, id); } catch(e) {}
  V.aoTrocarProva.forEach(fn => { try { fn(id); } catch(e) { console.error(e); } });
  if (rolar) { const alvo = document.querySelector(".pvp:not([hidden])"); if (alvo && alvo.getBoundingClientRect().top < 0) alvo.scrollIntoView({ behavior: calmo ? "auto" : "smooth", block:"start" }); }
}
V.escolherProva = escolherProva;
function iniciarProvas(){
  let id = (location.hash || "").replace("#", "");
  if (!document.querySelector(`.pvt button[data-pv="${id}"]`)) { try { id = localStorage.getItem(PROVA_SALVA) || ""; } catch(e) { id = ""; } }
  escolherProva(id, false);
  document.addEventListener("click", e => { const b = e.target.closest(".pvt button[data-pv]"); if (b) escolherProva(b.dataset.pv, true); });
}

/* ---------- ciclo da trilha ---------- */
function iniciarCiclos(){
  document.querySelectorAll(".ciclo").forEach(c => {
    const nos = [...c.querySelectorAll(".c-no")].filter(n => !n.hidden), meio = c.querySelector(".c-meio"); if (!nos.length || !meio) return;
    const raiz = c.closest("[data-sec]") || document;
    let i = 0, pausa = 0;
    const raio = () => c.style.setProperty("--R", (c.offsetWidth * .4) + "px");
    nos.forEach((n, k) => { const a = -90 + k * 360 / nos.length; n.style.setProperty("--a", a + "deg"); const b = n.querySelector("b"); if (b) b.textContent = k + 1; });
    function mostra(k){
      i = k; nos.forEach((n, j) => n.classList.toggle("on", j === k));
      raiz.querySelectorAll(".tela-sinc .t-img").forEach(im => im.classList.toggle("on", +im.dataset.n === k));
      const t = nos[k].querySelector("[data-f='f0']"), x = nos[k].querySelector("[data-f='f1']");
      meio.querySelector(".c-n").textContent = `Etapa ${k + 1} de ${nos.length}`;
      meio.querySelector(".c-t").textContent = t ? t.textContent : "";
      meio.querySelector(".c-x").textContent = x ? x.textContent : "";
      meio.classList.remove("troca"); void meio.offsetWidth; meio.classList.add("troca");
    }
    nos.forEach((n, k) => n.addEventListener("click", () => { pausa = Date.now() + 9000; mostra(k); }));
    raio(); if ("ResizeObserver" in window) new ResizeObserver(raio).observe(c);
    mostra(0);
    if (!calmo) setInterval(() => { if (!c.offsetParent || document.hidden || Date.now() < pausa) return; mostra((i + 1) % nos.length); }, 3200);
  });
}

/* ---------- cabeçalho: transparente no céu, roxo depois de rolar ---------- */
function cabecalho(){
  const t = document.querySelector(".topo"); if (!t) return;
  const ver = () => t.classList.toggle("rolou", scrollY > 12);
  addEventListener("scroll", ver, { passive:true }); ver();
}

function iniciar(){
  esconderBlocos();
  iniciarOrbitas();
  if (ORBS.length && !rodando) { rodando = true; requestAnimationFrame(laco); }
  iniciarProvas();
  iniciarCiclos();
}
cabecalho();
if (L.aoCarregar) L.aoCarregar(iniciar);
else document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", iniciar) : iniciar();
})();
