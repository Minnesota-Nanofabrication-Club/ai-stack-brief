/* ===========================================================================
   GopherFab Brief — reading app
   Minnesota Nanofabrication Club

   Plain ES2018. No build step, no dependencies. Fetches ./briefs/index.json,
   then ./briefs/<date>.json, and renders one edition at a time.

   Route grammar (hash):
     #                        latest edition
     #2026-08-20              that edition, top
     #2026-08-20/pulse        that edition, scrolled to The Pulse
     #2026-08-20/foundations  that edition, scrolled to Foundations
     #2026-08-20/chips        that edition, scrolled to a layer section
     #2026-08-20/<item-id>    that edition, scrolled to one Pulse item
   =========================================================================== */

(function () {
  'use strict';

  /* ---------------------------------------------------------------- data -- */

  // Fixed vocabulary. Bottom of the cake to the top; never reorder or extend.
  var LAYERS = [
    { slug: 'energy',         name: 'Energy',         scope: 'Generation, grid, cooling, siting' },
    { slug: 'chips',          name: 'Chips',          scope: 'Silicon, process, litho, packaging, equipment' },
    { slug: 'infrastructure', name: 'Infrastructure', scope: 'Racks, optics, datacenters, clouds, supply chain' },
    { slug: 'models',         name: 'Models',         scope: 'Releases, training, architectures, evals' },
    { slug: 'applications',   name: 'Applications',   scope: 'AI deployed in the world, and the economics of it' }
  ];
  var LAYER_BY_SLUG = {};
  LAYERS.forEach(function (l) { LAYER_BY_SLUG[l.slug] = l; });

  var CONFIDENCE = {
    confirmed: { label: 'Confirmed', title: 'On the record from a primary source.' },
    reported:  { label: 'Reported',  title: 'Credible reporting, not primary-confirmed.' },
    rumored:   { label: 'Rumored',   title: 'Single-sourced or unconfirmed. Treat as weak.' }
  };

  var LS = { theme: 'gfb.theme', expand: 'gfb.expand' };

  var state = {
    index: null,        // parsed briefs/index.json
    edition: null,      // parsed briefs/<date>.json
    date: null,         // date of the loaded edition
    cache: {},          // date -> edition
    loading: false,
    suppressHash: false // set while we rewrite location.hash ourselves
  };

  /* ------------------------------------------------------------- helpers -- */

  function $(id) { return document.getElementById(id); }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function store(key, value) {
    try {
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, value);
    } catch (e) { /* private mode; preferences just won't persist */ }
  }

  function read(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  function isDate(s) { return typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s); }

  // Format an ISO date without letting the browser shift it by a timezone.
  function prettyDate(iso) {
    if (!isDate(iso)) return iso || '';
    var p = iso.split('-');
    var d = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
    return d.toLocaleDateString('en-US', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC'
    });
  }

  function shortDate(iso) {
    if (!isDate(iso)) return iso || '';
    var p = iso.split('-');
    var d = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
  }

  // Today in America/Chicago — the editorial clock for this project.
  function todayCentral() {
    try {
      var parts = new Intl.DateTimeFormat('en-CA', {
        timeZone: 'America/Chicago', year: 'numeric', month: '2-digit', day: '2-digit'
      }).format(new Date());
      if (isDate(parts)) return parts;
    } catch (e) { /* fall through */ }
    return new Date().toISOString().slice(0, 10);
  }

  /* ------------------------------------------------- markdown (subset) -- */
  /* Supported, and nothing else: paragraphs, **bold**, *italic*, `code`,
     [links](url), "-"/"*" bullet lists, "1." numbered lists, ``` fences.
     HTML in the source is escaped BEFORE any formatting runs, so a stray
     <script> in a brief renders as text and can never execute. */

  var ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return ESCAPES[c]; });
  }

  // Only same-origin, http(s) and mailto targets survive. Everything else is
  // dropped, so javascript: and data: URLs in a brief cannot become links.
  function safeUrl(raw) {
    var u = String(raw || '').trim();
    if (/^(https?:\/\/|mailto:)/i.test(u)) return u;
    if (/^(#|\.?\/)/.test(u)) return u;
    return null;
  }

  // A sentinel that cannot appear in escaped source text. Code spans are parked
  // behind it while bold/italic/link formatting runs over everything else.
  var SENT = String.fromCharCode(1);

  function renderInline(escaped) {
    var codes = [];
    // Pull code spans out first so formatting never runs inside them.
    var out = escaped.replace(/`([^`]+)`/g, function (m, body) {
      codes.push(body);
      return SENT + (codes.length - 1) + SENT;
    });

    out = out.replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, function (m, text, href) {
      var url = safeUrl(href.replace(/&amp;/g, '&'));
      if (!url) return text;
      return '<a href="' + escapeHtml(url) + '" target="_blank" rel="noopener">' + text + '</a>';
    });

    out = out.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
    out = out.replace(/(^|[^*\w])\*([^*\n]+)\*(?![*\w])/g, '$1<em>$2</em>');

    return out.replace(new RegExp(SENT + '(\\d+)' + SENT, 'g'), function (m, i) {
      return '<code>' + codes[+i] + '</code>';
    });
  }

  function renderMarkdown(src) {
    if (!src) return '';
    var lines = String(src).replace(/\r\n?/g, '\n').split('\n');
    var html = '';
    var para = [];
    var list = null;      // { type: 'ul' | 'ol', items: [string] }
    var fence = null;     // array of raw code lines

    function flushPara() {
      if (!para.length) return;
      html += '<p>' + renderInline(escapeHtml(para.join(' '))) + '</p>';
      para = [];
    }
    function flushList() {
      if (!list) return;
      html += '<' + list.type + '>' + list.items.map(function (t) {
        return '<li>' + renderInline(escapeHtml(t)) + '</li>';
      }).join('') + '</' + list.type + '>';
      list = null;
    }
    function flushAll() { flushPara(); flushList(); }

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];

      if (fence) {
        if (/^\s*```/.test(line)) {
          html += '<div class="scroll-x"><pre><code>' + escapeHtml(fence.join('\n')) + '</code></pre></div>';
          fence = null;
        } else { fence.push(line); }
        continue;
      }
      if (/^\s*```/.test(line)) { flushAll(); fence = []; continue; }

      if (!line.trim()) { flushAll(); continue; }

      var bullet = line.match(/^\s*[-*]\s+(.*)$/);
      var number = line.match(/^\s*\d+[.)]\s+(.*)$/);

      if (bullet) {
        flushPara();
        if (!list || list.type !== 'ul') { flushList(); list = { type: 'ul', items: [] }; }
        list.items.push(bullet[1]);
        continue;
      }
      if (number) {
        flushPara();
        if (!list || list.type !== 'ol') { flushList(); list = { type: 'ol', items: [] }; }
        list.items.push(number[1]);
        continue;
      }
      // Indented continuation of the current list item.
      if (list && /^\s{2,}\S/.test(line)) {
        list.items[list.items.length - 1] += ' ' + line.trim();
        continue;
      }

      flushList();
      para.push(line.trim());
    }

    if (fence) html += '<div class="scroll-x"><pre><code>' + escapeHtml(fence.join('\n')) + '</code></pre></div>';
    flushAll();
    return html;
  }

  function mdBlock(src, cls) {
    var d = el('div', 'md' + (cls ? ' ' + cls : ''));
    d.innerHTML = renderMarkdown(src);
    // Any table or wide element a brief sneaks in still scrolls in its own box.
    Array.prototype.forEach.call(d.querySelectorAll('table'), function (t) {
      var wrap = el('div', 'scroll-x');
      t.parentNode.insertBefore(wrap, t);
      wrap.appendChild(t);
    });
    return d;
  }

  /* --------------------------------------------------------------- theme -- */

  function currentTheme() {
    var t = read(LS.theme);
    return (t === 'light' || t === 'dark') ? t : 'system';
  }

  function applyTheme(mode) {
    var root = document.documentElement;
    if (mode === 'light' || mode === 'dark') {
      root.setAttribute('data-theme', mode);
      store(LS.theme, mode);
    } else {
      root.removeAttribute('data-theme');
      store(LS.theme, null);
    }
    var label = mode === 'system' ? 'System' : (mode === 'light' ? 'Light' : 'Dark');
    $('theme-state').textContent = label;
    $('btn-theme').setAttribute('aria-label',
      'Colour theme: ' + (mode === 'system' ? 'follow system' : mode) + '. Activate to change.');
  }

  function cycleTheme() {
    var order = ['system', 'light', 'dark'];
    applyTheme(order[(order.indexOf(currentTheme()) + 1) % order.length]);
  }

  /* ------------------------------------------------------------ toggles -- */

  function allDetails() {
    return Array.prototype.slice.call(document.querySelectorAll('#edition details.deeper'));
  }

  function expandPreference() { return read(LS.expand) === 'open'; }

  function setAllDetails(open, persist) {
    allDetails().forEach(function (d) { d.open = open; });
    if (persist) store(LS.expand, open ? 'open' : 'closed');
    syncExpandButton();
  }

  function syncExpandButton() {
    var all = allDetails();
    var btn = $('btn-expand');
    if (!all.length) {
      btn.disabled = true;
      btn.textContent = 'Expand all';
      btn.setAttribute('aria-pressed', 'false');
      return;
    }
    btn.disabled = false;
    var openCount = all.filter(function (d) { return d.open; }).length;
    var allOpen = openCount === all.length;
    btn.textContent = allOpen ? 'Collapse all' : 'Expand all';
    btn.setAttribute('aria-pressed', allOpen ? 'true' : 'false');
    btn.title = openCount + ' of ' + all.length + ' deeper blocks open';
  }

  function makeDeeper(md, label, layerSlug) {
    var d = el('details', 'deeper');
    if (layerSlug) d.style.setProperty('--layer-c', 'var(--' + layerSlug + ')');
    var s = el('summary');
    s.appendChild(el('span', 'deeper__caret', '›'));
    s.appendChild(el('span', null, label || 'Go deeper'));
    d.appendChild(s);
    var body = el('div', 'deeper__body');
    body.appendChild(mdBlock(md));
    d.appendChild(body);
    d.addEventListener('toggle', syncExpandButton);
    if (expandPreference()) d.open = true;
    return d;
  }

  /* ------------------------------------------------------------- render -- */

  function renderSources(sources, label) {
    if (!Array.isArray(sources) || !sources.length) return null;
    var wrap = el('div', 'sources');
    wrap.appendChild(el('p', 'sources__label', label || 'Sources'));
    var ol = el('ol', 'sources__list');
    sources.forEach(function (s) {
      var li = el('li');
      var url = safeUrl(s && s.url);
      var title = (s && s.title) || url || 'Untitled source';
      if (url) {
        var a = el('a', null, title);
        a.href = url;
        a.target = '_blank';
        a.rel = 'noopener';
        li.appendChild(a);
      } else {
        li.appendChild(el('span', null, title));
      }
      var bits = [];
      if (s && s.publisher) bits.push(s.publisher);
      if (s && s.date) bits.push(s.date);
      if (bits.length) li.appendChild(el('span', 'sources__pub', bits.join(', ')));
      ol.appendChild(li);
    });
    wrap.appendChild(ol);
    return wrap;
  }

  function renderConfidence(value) {
    var key = String(value || '').toLowerCase();
    var meta = CONFIDENCE[key];
    if (!meta) { key = 'reported'; meta = CONFIDENCE.reported; }
    var chip = el('span', 'chip chip--' + key, meta.label);
    chip.title = meta.title;
    chip.setAttribute('aria-label', 'Confidence: ' + meta.label + '. ' + meta.title);
    return chip;
  }

  function renderItem(item, layerSlug) {
    var art = el('article', 'item');
    art.id = item.id || '';
    art.style.setProperty('--layer-c', 'var(--' + layerSlug + ')');
    art.style.setProperty('--layer-t', 'var(--' + layerSlug + '-tint)');

    var h = el('h4', 'item__title');
    h.appendChild(document.createTextNode(item.title || 'Untitled'));
    h.appendChild(document.createTextNode(' '));
    h.appendChild(renderConfidence(item.confidence));
    art.appendChild(h);

    if (item.dek) art.appendChild(el('p', 'item__dek', item.dek));

    if (item.why_it_matters) {
      var why = el('p', 'item__why');
      why.appendChild(el('b', null, 'Why it matters'));
      why.appendChild(document.createTextNode(item.why_it_matters));
      art.appendChild(why);
    }

    if (item.fab_angle) {
      var fab = el('p', 'item__fab');
      fab.appendChild(el('b', null, 'Fab angle'));
      fab.appendChild(document.createTextNode(item.fab_angle));
      art.appendChild(fab);
    }

    if (item.deeper_md) art.appendChild(makeDeeper(item.deeper_md, 'Go deeper', layerSlug));

    var src = renderSources(item.sources);
    if (src) art.appendChild(src);

    return art;
  }

  function renderPulse(pulse) {
    var host = $('pulse-layers');
    host.textContent = '';

    var present = layersPresent(pulse);
    LAYERS.forEach(function (def) {
      var block = present[def.slug];
      if (!block || !block.items || !block.items.length) return;   // absent layers simply aren't rendered

      var sec = el('section', 'layer');
      sec.id = 'layer-' + def.slug;
      sec.style.setProperty('--layer-c', 'var(--' + def.slug + ')');
      sec.style.setProperty('--layer-t', 'var(--' + def.slug + '-tint)');
      sec.setAttribute('aria-labelledby', 'layer-h-' + def.slug);

      var head = el('header', 'layer__head');
      head.appendChild(el('span', 'layer__rule'));
      var name = el('h3', 'layer__name', def.name);
      name.id = 'layer-h-' + def.slug;
      head.appendChild(name);
      head.appendChild(el('span', 'layer__count',
        block.items.length + (block.items.length === 1 ? ' item' : ' items')));
      head.appendChild(el('p', 'layer__scope', def.scope));
      sec.appendChild(head);

      block.items.forEach(function (item) { sec.appendChild(renderItem(item, def.slug)); });
      host.appendChild(sec);
    });

    $('pulse-time').textContent = readTimeLabel(pulse && pulse.read_time_min);
  }

  function layersPresent(pulse) {
    var map = {};
    var arr = (pulse && Array.isArray(pulse.layers)) ? pulse.layers : [];
    arr.forEach(function (block) {
      if (block && LAYER_BY_SLUG[block.layer]) map[block.layer] = block;
    });
    return map;
  }

  function readTimeLabel(min) {
    var n = Number(min);
    if (!isFinite(n) || n <= 0) return '';
    return '· ' + n + ' min read';
  }

  function renderCake(pulse) {
    var host = $('cake-stack');
    host.textContent = '';
    var present = layersPresent(pulse);

    // Drawn as a real cake: applications on top, energy at the base.
    LAYERS.slice().reverse().forEach(function (def) {
      var block = present[def.slug];
      var count = block && block.items ? block.items.length : 0;
      var li = el('li');
      var band;

      if (count) {
        band = el('a', 'cake__band');
        band.href = '#' + state.date + '/' + def.slug;
        band.addEventListener('click', function (ev) {
          ev.preventDefault();
          goTo(def.slug, true);
        });
      } else {
        band = el('span', 'cake__band cake__band--empty');
        band.setAttribute('aria-disabled', 'true');
      }

      band.style.setProperty('--band', 'var(--' + def.slug + ')');
      band.style.setProperty('--band-tint', 'var(--' + def.slug + '-tint)');
      band.appendChild(el('span', 'cake__name', def.name));

      if (count) {
        var dots = el('span', 'cake__dots');
        dots.setAttribute('aria-hidden', 'true');
        for (var i = 0; i < Math.min(count, 5); i++) dots.appendChild(el('span', 'cake__dot'));
        band.appendChild(dots);
        band.appendChild(el('span', 'cake__count', count + (count === 1 ? ' item' : ' items')));
      } else {
        band.appendChild(el('span', 'cake__count', 'nothing today'));
      }

      li.appendChild(band);
      host.appendChild(li);
    });
  }

  function renderFoundations(f) {
    var host = $('foundations-body');
    host.textContent = '';
    if (!f) return;

    if (f.topic) host.appendChild(el('h3', 'fnd__topic', f.topic));
    if (f.subtitle) host.appendChild(el('p', 'fnd__subtitle', f.subtitle));

    if (f.tldr) {
      var tl = el('div', 'fnd__tldr');
      tl.appendChild(el('b', null, 'The whole idea'));
      tl.appendChild(el('p', null, f.tldr));
      host.appendChild(tl);
    }

    (Array.isArray(f.sections) ? f.sections : []).forEach(function (sec, i) {
      var s = el('section', 'fnd__section');
      s.id = 'fnd-' + (i + 1);
      if (sec.heading) {
        var h = el('h4', 'fnd__heading', sec.heading);
        s.appendChild(h);
      }
      if (sec.body_md) s.appendChild(mdBlock(sec.body_md));
      if (sec.deeper_md) s.appendChild(makeDeeper(sec.deeper_md, 'Go deeper'));
      host.appendChild(s);
    });

    if (Array.isArray(f.glossary) && f.glossary.length) {
      var g = el('div', 'glossary');
      g.appendChild(el('h3', null, 'Glossary'));
      var dl = el('dl');
      f.glossary.forEach(function (entry) {
        dl.appendChild(el('dt', null, entry.term || ''));
        dl.appendChild(el('dd', null, entry.definition || ''));
      });
      g.appendChild(dl);
      host.appendChild(g);
    }

    if (f.try_this) {
      var t = el('div', 'trythis');
      t.appendChild(el('h3', null, 'Try this'));
      t.appendChild(el('p', null, f.try_this));
      host.appendChild(t);
    }

    var src = renderSources(f.sources, 'Foundations sources');
    if (src) host.appendChild(src);

    $('foundations-time').textContent = readTimeLabel(f.read_time_min);
  }

  function renderEdition(ed) {
    document.title = 'GopherFab Brief — ' + shortDate(ed.date);

    var dateNode = $('edition-date');
    dateNode.textContent = prettyDate(ed.date);
    dateNode.setAttribute('datetime', ed.date || '');

    $('edition-window').textContent = ed.window ? 'News window ' + ed.window : '';

    var total = Number(ed.pulse && ed.pulse.read_time_min) + Number(ed.foundations && ed.foundations.read_time_min);
    $('edition-readtime').textContent = isFinite(total) && total > 0 ? total + ' min total' : '';

    $('edition-headline').textContent = ed.headline || '';

    renderCake(ed.pulse);
    renderPulse(ed.pulse);
    renderFoundations(ed.foundations);

    var gen = ed.generated_at ? new Date(ed.generated_at) : null;
    $('edition-generated').textContent = gen && !isNaN(gen.getTime())
      ? 'Compiled ' + gen.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' }) + ' local time.'
      : '';

    $('edition').hidden = false;
    syncExpandButton();
    updateArchiveCurrent();
    updateEditionNav();
    updateProgress();
  }

  /* -------------------------------------------------------------- notice -- */

  function showNotice(lines, isError) {
    var n = $('notice');
    n.textContent = '';
    n.className = 'notice' + (isError ? ' notice--error' : '');
    (Array.isArray(lines) ? lines : [lines]).forEach(function (html) {
      var p = el('p', 'notice__body');
      p.innerHTML = html;   // callers pass only strings we build here
      n.appendChild(p);
    });
    n.hidden = false;
  }

  function hideNotice() { $('notice').hidden = true; }

  /* --------------------------------------------------------------- fetch -- */

  function getJSON(url) {
    return fetch(url, { cache: 'no-cache' }).then(function (res) {
      if (!res.ok) {
        var err = new Error('HTTP ' + res.status);
        err.status = res.status;
        throw err;
      }
      return res.json();
    });
  }

  /* ------------------------------------------------------------- archive -- */

  function editionEntries() {
    return (state.index && Array.isArray(state.index.editions)) ? state.index.editions : [];
  }

  function renderArchive(filter) {
    var host = $('archive-list');
    host.textContent = '';
    var q = String(filter || '').trim().toLowerCase();
    var all = editionEntries();

    var matches = all.filter(function (e) {
      if (!q) return true;
      var hay = [e.date, e.headline, e.foundations_topic, e.foundations_slug]
        .concat(Array.isArray(e.layers) ? e.layers : [])
        .join(' ').toLowerCase();
      return hay.indexOf(q) !== -1;
    });

    $('archive-count').textContent = q
      ? matches.length + ' of ' + all.length + ' editions match. Filtering headlines, topics and layers from the index — item text only exists inside a loaded edition.'
      : all.length + ' editions. Filter matches headlines, foundations topics and layers from the index — item text only exists inside a loaded edition.';

    if (!matches.length) {
      host.appendChild(el('li', 'archive__empty', q ? 'Nothing matches “' + q + '”.' : 'No editions in the index yet.'));
      return;
    }

    matches.forEach(function (e) {
      var li = el('li', 'archive__item');
      var a = el('a', 'archive__link');
      a.href = '#' + e.date;
      if (e.date === state.date) a.setAttribute('aria-current', 'true');

      var d = el('span', 'archive__date');
      d.appendChild(el('span', null, shortDate(e.date)));
      if (e.item_count) d.appendChild(el('span', 'archive__items', e.item_count + ' items'));
      a.appendChild(d);

      if (e.headline) a.appendChild(el('p', 'archive__headline', e.headline));
      if (e.foundations_topic) a.appendChild(el('p', 'archive__topic', 'Foundations: ' + e.foundations_topic));

      a.addEventListener('click', function () { closeArchive(false); });
      li.appendChild(a);
      host.appendChild(li);
    });
  }

  function updateArchiveCurrent() {
    Array.prototype.forEach.call($('archive-list').querySelectorAll('.archive__link'), function (a) {
      if (a.getAttribute('href') === '#' + state.date) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
  }

  var archiveOpener = null;

  function openArchive() {
    archiveOpener = document.activeElement;
    $('archive').hidden = false;
    $('archive').setAttribute('aria-hidden', 'false');
    $('scrim').hidden = false;
    $('btn-archive').setAttribute('aria-expanded', 'true');
    $('archive-search').focus();
  }

  function closeArchive(restoreFocus) {
    $('archive').hidden = true;
    $('archive').setAttribute('aria-hidden', 'true');
    $('scrim').hidden = true;
    $('btn-archive').setAttribute('aria-expanded', 'false');
    if (restoreFocus !== false && archiveOpener && archiveOpener.focus) archiveOpener.focus();
    archiveOpener = null;
  }

  function archiveOpen() { return !$('archive').hidden; }

  /* ------------------------------------------------------ edition nav -- */

  function editionIndexOf(date) {
    var list = editionEntries();
    for (var i = 0; i < list.length; i++) if (list[i].date === date) return i;
    return -1;
  }

  // editions[] is newest-first, so index+1 is older and index-1 is newer.
  function neighbour(delta) {
    var i = editionIndexOf(state.date);
    if (i === -1) return null;
    var e = editionEntries()[i + delta];
    return e ? e.date : null;
  }

  function updateEditionNav() {
    var older = neighbour(1), newer = neighbour(-1);
    var bo = $('btn-older'), bn = $('btn-newer');
    bo.disabled = !older;
    bn.disabled = !newer;
    bo.title = older ? 'Older edition: ' + shortDate(older) + ' (left arrow)' : 'This is the oldest edition';
    bn.title = newer ? 'Newer edition: ' + shortDate(newer) + ' (right arrow)' : 'This is the newest edition';
  }

  /* -------------------------------------------------------------- routes -- */

  function parseHash() {
    var raw = location.hash.replace(/^#/, '');
    if (!raw) return { date: null, target: null };
    var parts = raw.split('/');
    if (isDate(parts[0])) return { date: parts[0], target: parts[1] || null };
    return { date: null, target: parts[0] || null };
  }

  function setHash(date, target) {
    var h = '#' + date + (target ? '/' + target : '');
    if (location.hash === h) return;
    state.suppressHash = true;
    if (history && history.replaceState) history.replaceState(null, '', h);
    else location.hash = h;
    // The hashchange event fires asynchronously; clear the guard after it.
    setTimeout(function () { state.suppressHash = false; }, 0);
  }

  function targetElement(target) {
    if (!target) return null;
    if (target === 'pulse') return $('pulse');
    if (target === 'foundations') return $('foundations');
    if (LAYER_BY_SLUG[target]) return $('layer-' + target);
    if (/^layer-/.test(target) && LAYER_BY_SLUG[target.slice(6)]) return $(target);
    // Anything else: an item id or a foundations section id.
    if (/^[A-Za-z0-9_-]+$/.test(target)) {
      var node = $(target);
      if (node && document.getElementById('edition').contains(node)) return node;
    }
    return null;
  }

  var spyPausedUntil = 0;

  function goTo(target, updateHash) {
    var node = targetElement(target);
    spyPausedUntil = Date.now() + 1400;
    if (!node) {
      window.scrollTo(0, 0);
      if (updateHash) setHash(state.date, null);
      return;
    }
    node.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' });
    if (node.classList.contains('item')) {
      node.classList.remove('item--target');
      void node.offsetWidth;              // restart the flash
      node.classList.add('item--target');
    }
    if (updateHash) setHash(state.date, target);
  }

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /* ------------------------------------------------------------ progress -- */

  var progressQueued = false;

  function updateProgress() {
    var doc = document.documentElement;
    var scrollable = doc.scrollHeight - window.innerHeight;
    var ratio = scrollable > 8 ? Math.min(1, Math.max(0, window.scrollY / scrollable)) : 0;
    $('progress-bar').style.width = (ratio * 100).toFixed(2) + '%';
    updateScrollHash();
  }

  function onScroll() {
    if (progressQueued) return;
    progressQueued = true;
    requestAnimationFrame(function () {
      progressQueued = false;
      updateProgress();
    });
  }

  // Keep the hash pointed at whatever section the reader is actually in, so the
  // URL in the address bar is always the link worth pasting into club chat.
  var lastScrollTarget = null;

  function updateScrollHash() {
    if (!state.date || $('edition').hidden || archiveOpen()) return;
    if (Date.now() < spyPausedUntil) return;
    var anchors = Array.prototype.slice.call(
      document.querySelectorAll('#edition .layer, #edition #foundations'));
    if (!anchors.length) return;

    var line = window.scrollY + Math.min(180, window.innerHeight * 0.3);
    var current = null;
    anchors.forEach(function (a) {
      if (a.getBoundingClientRect().top + window.scrollY <= line) current = a;
    });

    var target = null;
    if (current) target = current.id === 'foundations' ? 'foundations' : current.id.replace(/^layer-/, '');
    if (window.scrollY < 40) target = null;

    if (target === lastScrollTarget) return;
    lastScrollTarget = target;
    setHash(state.date, target);
  }

  /* ---------------------------------------------------------------- load -- */

  function loadEdition(date, target, note) {
    if (state.loading) return Promise.resolve();
    state.loading = true;

    var cached = state.cache[date];
    var work = cached ? Promise.resolve(cached) : getJSON('./briefs/' + date + '.json');

    return work.then(function (ed) {
      state.cache[date] = ed;
      state.edition = ed;
      state.date = ed.date && isDate(ed.date) ? ed.date : date;
      renderEdition(ed);
      if (note) showNotice(note); else hideNotice();
      lastScrollTarget = null;
      if (target) {
        // Wait a frame so layout is settled before scrolling.
        requestAnimationFrame(function () { goTo(target, false); setHash(state.date, target); });
      } else {
        window.scrollTo(0, 0);
        setHash(state.date, null);
      }
    }).catch(function (err) {
      var latest = state.index && state.index.latest;
      if (latest && latest !== date) {
        state.loading = false;
        return loadEdition(latest, null, [
          'There is no edition for <strong>' + escapeHtml(date) + '</strong> (the file <code>briefs/' +
          escapeHtml(date) + '.json</code> did not load). Showing the most recent edition, <strong>' +
          escapeHtml(shortDate(latest)) + '</strong>, instead.'
        ]);
      }
      $('edition').hidden = true;
      showNotice([
        '<strong>Could not load the edition for ' + escapeHtml(date) + '.</strong>',
        'The file <code>briefs/' + escapeHtml(date) + '.json</code> is missing or unreadable (' +
        escapeHtml(err.message || 'fetch failed') + '). If you are running this locally, serve the ' +
        'directory with <code>python3 scripts/serve.py</code> — opening index.html straight from disk ' +
        'blocks the fetch.'
      ], true);
    }).then(function () {
      state.loading = false;
    });
  }

  function boot() {
    var route = parseHash();

    getJSON('./briefs/index.json').then(function (idx) {
      state.index = idx;
      renderArchive('');

      var list = editionEntries();
      var latest = idx.latest || (list[0] && list[0].date);

      if (!latest) {
        showNotice([
          '<strong>No editions yet.</strong>',
          'The index loaded but lists no editions — the daily job has not produced a brief. ' +
          'Once <code>briefs/YYYY-MM-DD.json</code> exists and <code>scripts/build_index.py</code> has run, this page fills in.'
        ], true);
        updateEditionNav();
        return;
      }

      var wanted = route.date || latest;
      var note = null;

      if (!route.date) {
        var today = todayCentral();
        if (latest < today) {
          note = ['<strong>No edition for today yet.</strong> Showing the most recent one, from <strong>' +
                  escapeHtml(prettyDate(latest)) + '</strong>. The daily job usually lands mid-morning Central.'];
        }
      }
      return loadEdition(wanted, route.target, note);
    }).catch(function (err) {
      showNotice([
        '<strong>No editions yet — the daily job has not run.</strong>',
        '<code>briefs/index.json</code> could not be loaded (' + escapeHtml(err.message || 'fetch failed') +
        '). That file is generated by <code>scripts/build_index.py</code> and deployed alongside the site. ' +
        'Running locally? Use <code>python3 scripts/serve.py</code> rather than opening the file directly.'
      ], true);
      $('btn-older').disabled = true;
      $('btn-newer').disabled = true;
      $('btn-expand').disabled = true;
    });
  }

  /* -------------------------------------------------------------- events -- */

  function onHashChange() {
    if (state.suppressHash) return;
    var route = parseHash();
    if (!state.index) return;
    var date = route.date || state.date || state.index.latest;
    if (!date) return;
    if (date !== state.date) loadEdition(date, route.target, null);
    else goTo(route.target, false);
  }

  function wire() {
    applyTheme(currentTheme());
    syncExpandButton();

    $('btn-theme').addEventListener('click', cycleTheme);

    $('btn-expand').addEventListener('click', function () {
      var all = allDetails();
      var allOpen = all.length > 0 && all.every(function (d) { return d.open; });
      setAllDetails(!allOpen, true);
    });

    $('btn-archive').addEventListener('click', function () {
      if (archiveOpen()) closeArchive(); else openArchive();
    });
    $('btn-archive-close').addEventListener('click', function () { closeArchive(); });
    $('scrim').addEventListener('click', function () { closeArchive(); });

    $('archive-search').addEventListener('input', function () { renderArchive(this.value); });

    $('btn-older').addEventListener('click', function () { step(1); });
    $('btn-newer').addEventListener('click', function () { step(-1); });

    $('brand-home').addEventListener('click', function (ev) {
      ev.preventDefault();
      var latest = state.index && state.index.latest;
      if (latest && latest !== state.date) loadEdition(latest, null, null);
      else { window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? 'auto' : 'smooth' }); setHash(state.date, null); }
    });

    document.addEventListener('keydown', function (ev) {
      if (ev.metaKey || ev.ctrlKey || ev.altKey) return;
      var t = ev.target;
      var typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);

      if (ev.key === 'Escape' && archiveOpen()) { closeArchive(); return; }
      if (typing) return;

      if (ev.key === 'ArrowLeft') { step(1); }
      else if (ev.key === 'ArrowRight') { step(-1); }
    });

    window.addEventListener('hashchange', onHashChange);
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
  }

  function step(delta) {
    var date = neighbour(delta);
    if (!date) return;
    loadEdition(date, null, null);
  }

  wire();
  boot();
})();
