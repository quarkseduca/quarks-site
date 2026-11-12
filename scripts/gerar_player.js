/* Imagem "aula ao vivo" do Preparatório PISM online (dono, 12/11/2026): um slide real do Quarks (motor de slides da gestão,
   Física PISM I, "Velocidade e unidades") com a câmera do professor no canto reservado (480x270 em 40,770, raio 28) e a
   moldura do Quarks Estúdio (gradiente roxo, como em quarks-gestao/slides/estudio/obs.html), mais o selo AO VIVO.
   Foto da câmera: site/img/camera-professor.jpg (ou .webp), enviada pelo dono. Sem ela, sai um aviso no lugar.
   Uso: node scripts/gerar_player.js   (precisa de ../quarks-gestao) → site/img/aovivo-pism.webp e site/img/aovivo-pism-1600.webp */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const RAIZ = path.join(__dirname, '..'), GESTAO = path.join(RAIZ, '..', 'quarks-gestao', 'slides');
const PARTE = path.join(GESTAO, 'partes', 'fisica', 'pism1', 'mu-1.html'), SLIDE = 'Relembrando';   // data-nome do slide, mostrado inteiro
const uri = (f) => 'data:' + ({ '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp' })[path.extname(f).toLowerCase()] + ';base64,' + fs.readFileSync(f).toString('base64');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const tmp = path.join(require('os').tmpdir(), 'quarks-slide.html');
  fs.writeFileSync(tmp, fs.readFileSync(PARTE, 'utf8').replace(/__VENDOR__/g, 'file://' + path.join(GESTAO, 'vendor') + '/'));
  await p.goto('file://' + tmp); await p.waitForTimeout(1500);
  // avança até o slide pedido e revela todas as etapas dele (cada seta mostra uma etapa ou passa de slide)
  const atual = () => p.evaluate(() => { const v = [...document.querySelectorAll('section.slide')].filter(s => getComputedStyle(s).visibility !== 'hidden' && getComputedStyle(s).display !== 'none' && s.getBoundingClientRect().width > 0 && getComputedStyle(s).opacity !== '0'); return v.length ? v[v.length - 1].dataset.nome : ''; });
  for (let i = 0; i < 60 && (await atual()) !== SLIDE; i++) { await p.keyboard.press('ArrowRight'); await p.waitForTimeout(200); }
  for (let i = 0; i < 12; i++) { await p.keyboard.press('ArrowRight'); await p.waitForTimeout(200); if ((await atual()) !== SLIDE) { await p.keyboard.press('ArrowLeft'); await p.waitForTimeout(400); break; } }
  await p.waitForTimeout(1200);
  await p.addStyleTag({ content: '[class*=atalho],.dica,.toast{display:none!important}' });
  const slide = await p.screenshot({ type: 'png' });
  const foto = ['camera-professor.jpg', 'camera-professor.jpeg', 'camera-professor.webp', 'camera-professor.png'].map(f => path.join(RAIZ, 'site', 'img', f)).find(f => fs.existsSync(f));
  const cam = foto ? `<img src="${uri(foto)}" style="width:100%;height:100%;object-fit:cover;object-position:50% 30%">`
                   : `<div style="width:100%;height:100%;display:grid;place-items:center;background:#E4DEFB;color:#4B39B3;font:800 30px Figtree,sans-serif;text-align:center">FOTO DO<br>PROFESSOR</div>`;
  const html = `<!doctype html><meta charset="utf-8"><style>
    @font-face{font-family:F;src:url(${uri(path.join(RAIZ, 'site/fontes/Figtree-700.woff2'))})}
    body{margin:0;width:1920px;height:1080px;position:relative;overflow:hidden}
    .s{position:absolute;inset:0;width:1920px;height:1080px}
    .cam{position:absolute;left:40px;top:770px;width:480px;height:270px;border-radius:28px;overflow:hidden;background:#292B2C}
    .mol{position:absolute;left:40px;top:770px;width:480px;height:270px;border-radius:28px;box-sizing:border-box;border:6px solid transparent;
      background:linear-gradient(135deg,#6551D1,#0F8B8D) border-box;-webkit-mask:linear-gradient(#000 0 0) padding-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude}
    .vivo{position:absolute;left:62px;top:790px;display:flex;align-items:center;gap:10px;background:rgba(41,43,44,.78);color:#fff;font:800 20px F,sans-serif;letter-spacing:.12em;padding:8px 16px 8px 14px;border-radius:999px}
    .vivo i{width:14px;height:14px;border-radius:50%;background:#FF4D5E;box-shadow:0 0 0 5px rgba(255,77,94,.3)}
  </style><img class="s" src="data:image/png;base64,${slide.toString('base64')}"><div class="cam">${cam}</div><div class="mol"></div><div class="vivo"><i></i>AO VIVO</div>`;
  await p.setContent(html, { waitUntil: 'load' }); await p.evaluate(() => document.fonts.ready);
  const png = path.join(require('os').tmpdir(), 'aovivo.png'); await p.screenshot({ path: png });
  await b.close();
  const { execFileSync } = require('child_process');
  execFileSync('python3', ['-c', `from PIL import Image
im=Image.open(${JSON.stringify(png)}).convert('RGB')
im.resize((1600,900),Image.LANCZOS).save(${JSON.stringify(path.join(RAIZ, 'site/img/aovivo-pism.webp'))},quality=86)
im.resize((960,540),Image.LANCZOS).save(${JSON.stringify(path.join(RAIZ, 'site/img/aovivo-pism-960.webp'))},quality=86)`]);
  console.log('ok', foto ? 'com a foto ' + path.basename(foto) : 'SEM FOTO (aviso no lugar da câmera)');
})();
