/* Páginas internas do site (geradas por scripts/gerar_paginas.py): contagem regressiva, linha do tempo,
   filtros (cursos e aprovados), aviso de arrastar nas tabelas largas e aparição suave ao rolar.
   Tudo funciona sem este arquivo (o conteúdo já vem no HTML); aqui só se melhora a experiência. */
(function () {
  'use strict';
  var d = document;
  var semAcento = function (s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };

  /* contagem regressiva: <div data-conta="2026-12-05T13:00:00-03:00"> */
  d.querySelectorAll('[data-conta]').forEach(function (el) {
    var alvo = new Date(el.getAttribute('data-conta')).getTime();
    var D = el.querySelector('[data-d]'), H = el.querySelector('[data-h]'), M = el.querySelector('[data-m]');
    function tique() {
      var r = alvo - Date.now();
      if (!(r > 0)) { el.classList.add('passou'); return; }
      var dias = Math.floor(r / 864e5), h = Math.floor(r % 864e5 / 36e5), m = Math.floor(r % 36e5 / 6e4);
      if (D) D.textContent = dias; if (H) H.textContent = h; if (M) M.textContent = m < 10 ? '0' + m : m;
      setTimeout(tique, 30000);
    }
    tique();
  });

  /* linha do tempo: marca o que já passou e o próximo passo */
  d.querySelectorAll('.pg-tempo').forEach(function (ol) {
    var hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    var prox = null;
    ol.querySelectorAll('li[data-dia]').forEach(function (li) {
      var p = li.getAttribute('data-dia').split('-');
      var dia = new Date(+p[0], +p[1] - 1, +p[2]);
      if (li.textContent.indexOf('05 e 06/12') > -1) dia.setDate(dia.getDate() + 1);   /* provas: dois dias */
      if (dia < hoje) li.classList.add('passou');
      else if (!prox) { prox = li; li.classList.add('prox'); }
    });
  });

  /* filtro de cursos (busca + área) e de aprovados (prova) */
  var tabela = d.querySelector('[data-tabela]'), busca = d.querySelector('[data-filtro]'), vazio = d.querySelector('[data-vazio]');
  var area = '';
  function filtra() {
    if (!tabela) return;
    var q = semAcento(busca ? busca.value.trim() : ''), n = 0;
    tabela.querySelectorAll('tbody tr').forEach(function (t) {
      var okA = !area || t.getAttribute('data-area') === area;
      if (t.classList.contains('grp')) { t.hidden = !!q || !okA; return; }
      var ok = okA && (!q || semAcento(t.getAttribute('data-busca')).indexOf(q) > -1);
      t.hidden = !ok; if (ok) n++;
    });
    if (vazio) vazio.style.display = n ? 'none' : 'block';
  }
  if (busca) busca.addEventListener('input', filtra);
  d.querySelectorAll('[data-chips]').forEach(function (grupo) {
    grupo.addEventListener('click', function (ev) {
      var b = ev.target.closest('button'); if (!b) return;
      grupo.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      var v = b.getAttribute('data-v');
      if (grupo.getAttribute('data-chips') === 'area') { area = v; filtra(); }
      else d.querySelectorAll('[data-aprov] figure').forEach(function (f) { f.hidden = !!v && f.getAttribute('data-prova') !== v; });
    });
  });

  /* tabelas largas no celular: mostra "arraste para o lado" só quando precisa */
  function mede() {
    d.querySelectorAll('.pg-tabw').forEach(function (w) {
      var t = w.querySelector('.pg-tab');
      w.classList.toggle('rola', !!t && t.scrollWidth > t.clientWidth + 4 && t.scrollLeft < 8);
    });
  }
  d.querySelectorAll('.pg-tabw .pg-tab').forEach(function (t) { t.addEventListener('scroll', mede, { passive: true }); });
  window.addEventListener('resize', mede); mede();

  /* aparição suave ao rolar */
  if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('vis'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    d.querySelectorAll('.pg-sec .pg-in > *').forEach(function (el) { el.classList.add('pg-rev'); io.observe(el); });
  }
})();
