/*
 * Toy Pile: live factory-space animation for the production page.
 *
 * Reads:  #toy-pile[data-capacity]                     -> factory spaces
 *         tr[data-toy-name|data-toy-icon|data-toy-color] -> one row per toy, each with
 *         an input[id*="units_to_manufacture"]
 * Call ToyPile.update() whenever the unit inputs change (updateCalculations() does this).
 */
(function () {
  'use strict';

  var COLORS = { line: '#dee2e6', muted: '#868e96', warn: '#e8590c', warnSoft: '#fff4e6' };
  var MAX_ICONS = 60;          // above this many spaces, one icon stands for several units
  var GRAVITY = 0.55;

  var panel, canvas, ctx, building, stacksEl, beacon, countEl, legendEl, perEl;
  var capacity = 1, items = [], geom = null, util = 0, smokeTimer = 0, nextId = 1;
  var started = false, lastW = 0, lastH = 0;
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function init() {
    if (started) return !!panel;
    started = true;
    panel = document.getElementById('toy-pile');
    if (!panel) return false;
    canvas   = panel.querySelector('canvas');
    ctx      = canvas.getContext('2d');
    building = panel.querySelector('.tp-building');
    stacksEl = panel.querySelector('.tp-stacks');
    beacon   = panel.querySelector('.tp-beacon');
    countEl  = panel.querySelector('.tp-count');
    legendEl = panel.querySelector('.tp-legend');
    perEl    = panel.querySelector('.tp-per');
    capacity = parseInt(panel.dataset.capacity, 10) || 1;

    document.querySelectorAll('tr[data-toy-name] input[id*="units_to_manufacture"]').forEach(function (input) {
      input.addEventListener('input', update);
    });
    // re-layout when the window is resized (or the panel appears at a wider width)
    if (window.ResizeObserver) new ResizeObserver(function () { update(); }).observe(building);
    else window.addEventListener('resize', update);

    requestAnimationFrame(draw);
    return true;
  }

  function readToys() {
    return Array.prototype.map.call(document.querySelectorAll('tr[data-toy-name]'), function (row) {
      var input = row.querySelector('input[id*="units_to_manufacture"]');
      return {
        name:  row.dataset.toyName,
        icon:  row.dataset.toyIcon,
        color: row.dataset.toyColor,
        n:     Math.max(0, parseInt(input && input.value, 10) || 0)
      };
    });
  }

  function update() {
    if (!init()) return;

    var rect = building.getBoundingClientRect();
    if (rect.width < 20 || rect.height < 40) { geom = null; return; }   // panel hidden on narrow screens

    var W = rect.width, H = rect.height;
    if (W !== lastW || H !== lastH) {
      var dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      lastW = W; lastH = H;
    }

    var toys  = readToys();
    var total = toys.reduce(function (s, t) { return s + t.n; }, 0);
    var N     = capacity;
    var over  = Math.max(0, total - N);

    // grid geometry: capacity slots fill the building, with headroom above the roofline for overflow
    var per      = N <= MAX_ICONS ? 1 : Math.ceil(N / MAX_ICONS);
    var capSlots = Math.ceil(N / per);
    var headroom = Math.min(60, H * 0.18);
    var usableH  = H - headroom - 4;
    var cols = Math.max(4, Math.ceil(Math.sqrt(capSlots * W / usableH)));
    var size = W / cols;
    while (Math.ceil(capSlots / cols) * size > usableH) { cols++; size = W / cols; }
    var capRows = Math.ceil(capSlots / cols);
    var maxSlots = capSlots + Math.floor(headroom / size) * cols;
    geom = { W: W, H: H, size: size, capY: H - 4 - capRows * size, over: over > 0 };

    // one token per icon, grouped by toy
    var want = [];
    toys.forEach(function (t) {
      var k = Math.round(t.n / per);
      for (var i = 0; i < k; i++) want.push(t);
    });
    want = want.slice(0, maxSlots);

    // reuse existing icons of the same toy so only the changed ones drop in or fade out
    var pool = {};
    items.forEach(function (it) { if (!it.dying) (pool[it.name] = pool[it.name] || []).push(it); });
    var next = [];
    want.forEach(function (t, i) {
      var list = pool[t.name] || [];
      var it = list.shift();
      if (!it) {
        it = { id: nextId++, name: t.name, icon: t.icon, color: t.color,
               x: 0, y: 0, vy: 0, rot: (Math.random() - 0.5) * 0.5, alpha: 1, fresh: true };
      }
      var col = i % cols, row = Math.floor(i / cols);
      var jitter = ((it.id * 9301 + 49297) % 233280) / 233280 - 0.5;
      it.tx = col * size + size / 2 + jitter * size * 0.18;
      it.ty = H - 4 - row * size - size / 2;
      it.overflow = i >= capSlots;
      if (it.fresh) {
        it.x = it.tx;
        it.y = reduced ? it.ty : -size - Math.random() * 40 - col * 4;
        it.fresh = false;
      }
      next.push(it);
    });
    Object.keys(pool).forEach(function (k) { pool[k].forEach(function (it) { it.dying = true; next.push(it); }); });
    items = next;

    // header, legend, alarms
    util = Math.min(1.3, total / N);
    countEl.innerHTML = total + ' <small>/ ' + N + '</small>';
    countEl.classList.toggle('over', over > 0);
    perEl.textContent = per > 1 ? 'Each icon = ' + per + ' units' : 'Each icon = 1 unit';
    building.classList.toggle('shake', over > 0 && !reduced);
    beacon.classList.toggle('on', over > 0);

    var rows = toys.filter(function (t) { return t.n > 0; }).map(function (t) {
      return '<div class="tp-legend-row"><span class="tp-swatch" style="background:' + t.color + '"></span>' +
             '<span>' + t.icon + ' ' + escapeHtml(t.name) + '</span><span>' + t.n + '</span></div>';
    });
    rows.push(over > 0
      ? '<div class="tp-legend-row" style="color:' + COLORS.warn + ';font-weight:600"><span>⚠</span><span>Over capacity</span><span>' + over + '</span></div>'
      : '<div class="tp-legend-row free"><span class="tp-swatch empty"></span><span>Empty space</span><span>' + (N - total) + '</span></div>');
    legendEl.innerHTML = rows.join('');
  }

  function draw() {
    requestAnimationFrame(draw);
    if (!geom) return;
    var W = geom.W, H = geom.H, size = geom.size, capY = geom.capY;
    ctx.clearRect(0, 0, W, H);

    // floor lines
    ctx.strokeStyle = COLORS.line; ctx.lineWidth = 1; ctx.globalAlpha = 0.6;
    for (var y = H - 4; y > capY + 1; y -= size) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    ctx.globalAlpha = 1;

    // capacity line
    var capColor = geom.over ? COLORS.warn : COLORS.muted;
    ctx.setLineDash([5, 4]); ctx.strokeStyle = capColor;
    ctx.beginPath(); ctx.moveTo(0, capY); ctx.lineTo(W, capY); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = capColor; ctx.font = '600 10px system-ui, sans-serif'; ctx.textAlign = 'right'; ctx.textBaseline = 'alphabetic';
    ctx.fillText(geom.over ? 'OVER CAPACITY' : 'CAPACITY', W - 4, capY - 4);

    // toys
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    items = items.filter(function (it) { return !(it.dying && it.alpha <= 0.02); });
    items.forEach(function (it) {
      if (it.dying) { it.alpha -= 0.08; it.vy += GRAVITY; it.y += it.vy * 0.4; }
      else if (reduced) { it.x = it.tx; it.y = it.ty; }
      else {
        it.x += (it.tx - it.x) * 0.18;
        if (it.y < it.ty) {
          it.vy += GRAVITY; it.y += it.vy;
          if (it.y >= it.ty) { it.y = it.ty; it.vy = Math.abs(it.vy) > 2 ? -it.vy * 0.32 : 0; }   // bounce
        } else if (it.y > it.ty + 0.5) { it.y += (it.ty - it.y) * 0.2; it.vy = 0; }
      }
      var r = size * 0.46;
      ctx.save();
      ctx.globalAlpha = Math.max(0, it.alpha);
      ctx.translate(it.x, it.y); ctx.rotate(it.rot);
      ctx.fillStyle   = it.overflow ? COLORS.warnSoft : it.color + '2e';
      ctx.strokeStyle = it.overflow ? COLORS.warn : it.color;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(-r, -r, r * 2, r * 2, r * 0.35); else ctx.rect(-r, -r, r * 2, r * 2);
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#000';
      ctx.font = Math.round(size * 0.56) + 'px "Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif';
      ctx.fillText(it.icon, 0, size * 0.03);
      ctx.restore();
    });

    // smoke: busier factory, faster puffs
    if (!reduced && util > 0 && --smokeTimer <= 0) {
      puff();
      smokeTimer = Math.max(8, 70 - util * 55);
    }
  }

  function puff() {
    var stacks = stacksEl.querySelectorAll('.tp-stack');
    var s = stacks[Math.floor(Math.random() * stacks.length)];
    var p = document.createElement('div');
    p.className = 'tp-puff' + (util > 1 ? ' hot' : '');
    p.style.left = (s.offsetLeft + 1) + 'px';
    p.style.top = (s.offsetTop - 10) + 'px';
    p.style.setProperty('--dx', (8 + Math.random() * 18) + 'px');
    stacksEl.appendChild(p);
    setTimeout(function () { p.remove(); }, 2700);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  window.ToyPile = { update: update };
})();