/* Simulados abertos (dono, 22/11/2026): a faixa fina no topo (aparece sozinha enquanto houver inscrição aberta em prova.quarksedu.com.br)
   e o cartão grande (só quando a coordenação liga em Simulados > botão Aberto > "Cartão grande"; entra no lugar de <div data-sim-cartao>).
   Os dados vêm de https://prova.quarksedu.com.br/?a=pa_lista (gestão 34.5), sem nada de aluno. O mesmo arquivo está no site
   (quarks-site/site/) e na loja (testando-apostilas/loja/publicar/assets/); mudou um, copie no outro com o mesmo nome. */
(function () {
  'use strict';
  var API = 'https://prova.quarksedu.com.br/?a=pa_lista', URL = 'https://prova.quarksedu.com.br/';
  var MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function data(d) { var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d || ''); return m ? (+m[3]) + ' de ' + MESES[+m[2] - 1] : ''; }
  function onde(s) { return s.online && s.presencial ? 'online ou presencial' : s.online ? 'online' : 'presencial'; }
  function guardado(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }
  function guarda(k) { try { sessionStorage.setItem(k, '1'); } catch (e) { /* sem armazenamento */ } }

  var CSS = '.qsa-faixa{position:relative;z-index:41;background:#F1EEFD;color:#292B2C;font:14.5px/1.4 Figtree,system-ui,sans-serif}'
    + '.qsa-faixa .qsa-in{max-width:1280px;margin:0 auto;padding:9px 56px 9px 48px;display:flex;align-items:center;justify-content:center}'
    + '.qsa-faixa a{color:inherit;text-decoration:none;display:inline-flex;align-items:center;gap:12px;flex-wrap:wrap;justify-content:center}'
    + '.qsa-selo{display:inline-flex;align-items:center;gap:7px;background:#FFD10C;border-radius:999px;padding:3px 11px 3px 9px;font-weight:800;font-size:12.5px;text-transform:uppercase;letter-spacing:.03em}'
    + '.qsa-ir{font-weight:800;color:#4B39B3;text-decoration:underline;text-underline-offset:3px;white-space:nowrap}'
    + '.qsa-x{position:absolute;right:14px;top:50%;transform:translateY(-50%);width:30px;height:30px;border-radius:50%;border:0;background:transparent;color:#5E5A70;font-size:20px;line-height:1;cursor:pointer}'
    + '.qsa-x:hover{background:rgba(101,81,209,.12)}'
    + '.qsa-ponto{position:relative;display:inline-block;width:8px;height:8px;border-radius:50%;background:#292B2C;flex:none}'
    + '.qsa-ponto::after{content:"";position:absolute;inset:-4px;border-radius:50%;border:2px solid #292B2C;opacity:0;animation:qsa-onda 2.8s ease-out infinite}'
    + '@keyframes qsa-onda{0%{transform:scale(.5);opacity:.7}70%,100%{transform:scale(1.6);opacity:0}}'
    + '.qsa-curto{display:none}'
    + '@media (max-width:640px){.qsa-faixa{font-size:13.5px}.qsa-faixa .qsa-in{padding:8px 44px 8px 16px;justify-content:flex-start}.qsa-longo,.qsa-tx{display:none}.qsa-curto{display:inline}.qsa-faixa a{gap:8px;flex-wrap:nowrap;white-space:nowrap}.qsa-x{right:6px}}'
    + '.qsa-banda{padding:28px 0 40px}.qsa-banda .qsa-bi{max-width:1184px;margin:0 auto;padding:0 24px}'
    + '.qsa-card{background:#fff;color:#292B2C;border-radius:40px;padding:40px 44px;display:grid;grid-template-columns:1.35fr .9fr;gap:36px;align-items:center;position:relative;overflow:hidden;box-shadow:0 30px 60px -36px rgba(40,20,110,.55);font-family:Figtree,system-ui,sans-serif}'
    + '.qsa-card::before{content:"";position:absolute;right:-70px;top:50%;width:420px;height:420px;margin-top:-210px;border-radius:50%;background:#F1EEFD}'
    + '.qsa-card::after{content:"";position:absolute;right:120px;top:-40px;width:120px;height:120px;border-radius:50%;background:#FFD10C}'
    + '.qsa-card>*{position:relative;z-index:1}'
    + '.qsa-card h2{font-family:"Bricolage Grotesque",Figtree,sans-serif;font-weight:800;font-size:44px;line-height:1.04;letter-spacing:-.02em;margin:14px 0 12px;color:#292B2C}.qsa-card h2 em{font-style:normal;color:#6551D1}'
    + '.qsa-lead{font-size:17.5px;line-height:1.55;color:#4A4858;margin:0 0 18px;max-width:560px}'
    + '.qsa-chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 22px;padding:0;list-style:none}.qsa-chips li{background:#F1EEFD;color:#4B39B3;border-radius:999px;padding:7px 14px;font-weight:700;font-size:14px}'
    + '.qsa-btn{display:inline-block;background:#FFD10C;color:#292B2C;border-radius:999px;padding:14px 26px;font-weight:800;font-size:16px;text-decoration:none;animation:qsa-respira 4.5s ease-in-out infinite}'
    + '@keyframes qsa-respira{0%,100%{transform:scale(1)}50%{transform:scale(1.04)}}'
    + '.qsa-prox{margin-top:18px;font-size:14px;color:#5E5A70}.qsa-prox b{color:#292B2C}'
    + '.qsa-lado{max-width:300px;justify-self:center;width:100%}.qsa-folha{display:block;width:100%;height:auto;filter:drop-shadow(0 24px 34px rgba(40,20,110,.28));transform:rotate(-3deg)}'
    + '.qsa-enche{transform-box:fill-box;transform-origin:center;animation:qsa-enche 6s ease-in-out infinite}@keyframes qsa-enche{0%,25%{transform:scale(0)}45%,85%{transform:scale(1)}100%{transform:scale(0)}}'
    + '@media (max-width:900px){.qsa-card{grid-template-columns:1fr;padding:28px 22px;border-radius:30px;gap:8px}.qsa-card h2{font-size:31px}.qsa-lead{font-size:16px}.qsa-lado{order:-1;max-width:130px;justify-self:end;margin:-6px -4px -4px 0}.qsa-card::before{width:260px;height:260px;right:-80px;top:0;margin-top:-70px}.qsa-card::after{width:64px;height:64px;right:150px;top:-26px}.qsa-banda .qsa-bi{padding:0 16px}.qsa-btn{display:block;text-align:center}}'
    + '@media (prefers-reduced-motion:reduce){.qsa-ponto::after,.qsa-btn,.qsa-enche{animation:none!important}}';

  function folha() {
    var marc = [1, 3, 0, 4, 2, null], o = '';
    marc.forEach(function (m, i) {
      var y = 58 + i * 34; o += '<text x="36" y="' + (y + 5) + '" font-size="13" font-weight="800" fill="#4B39B3" font-family="Figtree,sans-serif">' + ('0' + (i + 1)).slice(-2) + '</text>';
      'ABCDE'.split('').forEach(function (L, j) { var x = 70 + j * 34;
        o += m === j ? '<circle cx="' + x + '" cy="' + y + '" r="11" fill="#6551D1"/>' : '<circle cx="' + x + '" cy="' + y + '" r="11" fill="#fff" stroke="#CFC6F5" stroke-width="2"/><text x="' + x + '" y="' + (y + 4) + '" text-anchor="middle" font-size="10" font-weight="700" fill="#8A82B8" font-family="Figtree,sans-serif">' + L + '</text>'; });
      if (m === null) o += '<circle class="qsa-enche" cx="172" cy="' + y + '" r="11" fill="#FFD10C"/>';
    });
    return '<svg class="qsa-folha" viewBox="0 0 260 280" role="img" aria-label="Ilustração de uma folha de respostas"><rect x="6" y="6" width="248" height="268" rx="26" fill="#fff"/><rect x="24" y="20" width="120" height="12" rx="6" fill="#F1EEFD"/><rect x="152" y="20" width="84" height="12" rx="6" fill="#FFD10C" opacity=".85"/>' + o + '</svg>';
  }

  function faixa(s, n) {
    if (guardado('qsa-faixa-fechada')) return;
    var f = document.createElement('div'); f.className = 'qsa-faixa'; f.setAttribute('role', 'region'); f.setAttribute('aria-label', 'Simulados abertos');
    var prox = n > 1 ? n + ' simulados com inscrições abertas · o próximo em ' + esc(data(s.data)) : esc(s.nome) + ' · ' + esc(data(s.data)) + ' · ' + onde(s) + ' · ' + (s.pago ? 'por Pix' : 'gratuito');
    f.innerHTML = '<div class="qsa-in"><a href="' + URL + '"><span class="qsa-selo"><i class="qsa-ponto"></i><span class="qsa-longo">Inscrições abertas</span><span class="qsa-curto">Simulados abertos</span></span>'
      + '<span class="qsa-tx"><b>Simulados do Quarks:</b> ' + prox + '</span><span class="qsa-ir">Inscrever-se →</span></a></div><button class="qsa-x" type="button" aria-label="Fechar o aviso">×</button>';
    f.querySelector('.qsa-x').onclick = function () { f.remove(); guarda('qsa-faixa-fechada'); };
    var topo = document.querySelector('[data-sim-faixa]') || document.querySelector('header'); if (topo && topo.parentNode) topo.parentNode.insertBefore(f, topo); else document.body.insertBefore(f, document.body.firstChild);
  }

  function cartao(s, n) {
    var alvo = document.querySelector('[data-sim-cartao]'); if (!alvo) return;
    var chips = [onde(s) === 'online ou presencial' ? 'Online ou presencial' : onde(s) === 'online' ? 'Online, de casa' : 'Presencial, no Quarks', s.pago ? 'Inscrição por Pix' : 'Gratuito', 'Nota por disciplina', 'Gabarito oficial'];
    alvo.innerHTML = '<section class="qsa-banda" aria-label="Simulados abertos"><div class="qsa-bi"><div class="qsa-card"><div>'
      + '<span class="qsa-selo"><i class="qsa-ponto"></i>Inscrições abertas</span>'
      + '<h2>Faça o simulado do Quarks <em>como num vestibular</em></h2>'
      + '<p class="qsa-lead">Qualquer pessoa pode se inscrever. É a mesma prova dos alunos do Quarks, e você sai com a nota por disciplina e o gabarito.</p>'
      + '<ul class="qsa-chips">' + chips.map(function (c) { return '<li>' + esc(c) + '</li>'; }).join('') + '</ul>'
      + '<a class="qsa-btn" href="' + URL + '">' + (n > 1 ? 'Ver os ' + n + ' simulados abertos' : 'Quero me inscrever') + '</a>'
      + '<p class="qsa-prox"><b>Próximo:</b> ' + esc(s.nome) + (s.prova && String(s.nome).indexOf(s.prova) < 0 ? ' (' + esc(s.prova) + ')' : '') + ' · ' + esc(data(s.data)) + (s.inicio ? ' às ' + esc(String(s.inicio).slice(0, 5)) : '') + (s.ate ? ' · inscrições até ' + esc(data(s.ate)) : '') + '</p>'
      + '</div><div class="qsa-lado">' + folha() + '</div></div></div></section>';
  }

  function iniciar() {
    if (!window.fetch) return;
    fetch(API, { credentials: 'omit' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      if (!j || !j.ok) return; var L = (j.simulados || []).filter(function (s) { return s.inscricoesAbertas; }); if (!L.length) return;
      var st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
      faixa(L[0], L.length); if (j.destaque && j.destaque.cartao) cartao(L[0], L.length);
    }).catch(function () { /* sem a lista, nada aparece */ });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
