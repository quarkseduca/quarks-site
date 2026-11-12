// Imagens de compartilhamento (1200x630) de cada página gerada, em site/og/<pasta>.jpg (barra vira "--").
// Rode depois de scripts/gerar_paginas.py (que escreve scripts/og-paginas.json) e rode o gerador de novo
// para as páginas apontarem para as imagens:  node scripts/gerar_og.js && python3 scripts/gerar_paginas.py
// Só algumas páginas (ex.: no dia do gabarito):  node scripts/gerar_og.js gabarito-pism-2027 pism
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const RAIZ = path.join(__dirname, '..');
const SO = process.argv.slice(2);
const lista = JSON.parse(fs.readFileSync(path.join(__dirname, 'og-paginas.json'), 'utf8')).filter((x) => !SO.length || SO.includes(x.pasta));
if (!lista.length) { console.error('Nenhuma página com esse nome em og-paginas.json: ' + SO.join(', ')); process.exit(1); }
const TIPOS = { woff2: 'font/woff2', png: 'image/png', webp: 'image/webp', jpg: 'image/jpeg' };
const _cache = {};
// setContent não lê file://: tudo entra como data: URI
const url = (f) => _cache[f] || (_cache[f] = 'data:' + TIPOS[f.split('.').pop()] + ';base64,' + fs.readFileSync(path.join(RAIZ, f.replace(/^\//, ''))).toString('base64'));
const esc = (s) => String(s || '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const css = `@font-face{font-family:B;src:url(${url('site/fontes/BricolageGrotesque-800.woff2')})}
@font-face{font-family:F;src:url(${url('site/fontes/Figtree-500.woff2')});font-weight:500}
@font-face{font-family:F;src:url(${url('site/fontes/Figtree-700.woff2')});font-weight:700}
*{margin:0;box-sizing:border-box}body{width:1200px;height:630px;overflow:hidden;font-family:F;color:#fff;
background:radial-gradient(60% 90% at 90% 10%,rgba(143,116,231,.6),transparent 60%),linear-gradient(160deg,#7357DE 0%,#5B37AE 52%,#4B258D 100%);position:relative}
.orb{position:absolute;border-radius:50%;border:2px solid rgba(255,255,255,.18);width:1300px;height:520px;right:-520px;top:60px;transform:rotate(-12deg)}
.orb.b{width:820px;height:320px;right:-260px;top:200px;border-style:dashed;border-color:rgba(255,209,12,.45)}
.tx{position:absolute;left:72px;top:64px;width:640px}
.logo{height:40px}.selo{display:inline-block;margin-top:44px;font-weight:700;font-size:22px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);padding:8px 18px;border-radius:99px}
h1{font-family:B;font-size:60px;line-height:1;letter-spacing:-2px;margin-top:22px}
p{font-size:25px;line-height:1.4;opacity:.92;margin-top:20px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.vis{position:absolute;right:64px;top:115px;width:400px;height:400px}
.foto{width:400px;height:400px;border-radius:46% 54% 52% 48%/48% 46% 54% 52%;overflow:hidden;box-shadow:0 30px 60px -20px rgba(30,10,80,.6)}
.foto img{width:100%;height:100%;object-fit:cover}
.card{background:#fff;color:#292B2C;border-radius:32px;padding:34px 34px 30px;margin-top:60px;box-shadow:0 30px 60px -24px rgba(20,6,60,.6)}
.card small{display:block;font-weight:700;font-size:20px;color:#5E5A70;text-transform:uppercase;letter-spacing:1px}
.card b{display:block;font-family:B;font-size:80px;color:#3F2FA0;letter-spacing:-3px;line-height:1.05;margin-top:8px}
.card span{font-size:24px;color:#5E5A70;font-weight:700}
.sim{position:absolute;right:-6px;bottom:-6px;width:110px;height:110px;border-radius:50%;background:#FFD10C;display:grid;place-items:center}
.sim img{width:66px}.url{position:absolute;left:72px;bottom:48px;font-weight:700;font-size:22px;color:#FFD10C}`;
(async () => {
  const pasta = path.join(RAIZ, 'site', 'og'); fs.mkdirSync(pasta, { recursive: true });
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const x of lista) {
    const vis = x.valor
      ? `<div class="vis" style="top:150px"><div class="card"><small>Nota de corte</small><b>${esc(x.valor)}</b><span>${esc(x.unidade)}</span></div><div class="sim" style="top:-40px;right:-30px;bottom:auto"><img src="${url('site/img/symbol-purple-transparent.png')}"></div></div>`
      : x.quadro ? `<div class="vis" style="display:grid;place-items:center;width:470px;right:40px"><div style="width:470px;height:294px;border-radius:28px;overflow:hidden;box-shadow:0 30px 60px -20px rgba(30,10,80,.6)"><img style="width:100%;height:100%;object-fit:cover" src="${url(x.quadro)}"></div><div class="sim" style="right:-30px;bottom:20px"><img src="${url('site/img/symbol-purple-transparent.png')}"></div></div>`
      : x.foto ? `<div class="vis"><div class="foto"><img src="${url(x.foto)}"></div><div class="sim"><img src="${url('site/img/symbol-purple-transparent.png')}"></div></div>`
      : `<div class="vis" style="display:grid;place-items:center"><div class="sim" style="position:static;width:260px;height:260px"><img style="width:160px" src="${url('site/img/symbol-purple-transparent.png')}"></div></div>`;
    const html = `<!doctype html><meta charset="utf-8"><style>${css}</style><i class="orb"></i><i class="orb b"></i>
      <div class="tx"><img class="logo" src="${url('site/img/logo-white-text.png')}"><br>${x.selo ? `<span class="selo">${esc(x.selo)}</span>` : ''}
      <h1>${esc(x.titulo)}</h1><p>${esc(x.lead)}</p></div>${vis}<div class="url">quarksedu.com.br/${esc(x.pasta)}/</div>`;
    await pg.setContent(html, { waitUntil: 'load' }); await pg.evaluate(() => document.fonts.ready);
    await pg.screenshot({ path: path.join(pasta, x.pasta.replace(/\//g, '--') + '.jpg'), type: 'jpeg', quality: 82 });
  }
  await b.close(); console.log(lista.length + ' imagens em site/og/');
})();
