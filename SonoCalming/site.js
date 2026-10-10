(() => {
  'use strict';
  const button = document.getElementById('menu');
  const nav = document.getElementById('links');
  if (button && nav) {
    button.addEventListener('click', () => {
      const isOpen = nav.classList.toggle('open');
      button.setAttribute('aria-expanded', String(isOpen));
    });
    nav.addEventListener('click', event => {
      if (event.target.closest('a')) {
        nav.classList.remove('open');
        button.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // The YouTube iframe is loaded only when somebody explicitly presses Play.
  // This keeps the catalogue fast and private by default.
  document.querySelectorAll('.js-player').forEach(preview => {
    preview.addEventListener('click', () => {
      const video = preview.dataset.video;
      const playlist = preview.dataset.playlist;
      if (video && !/^[a-zA-Z0-9_-]{11}$/.test(video)) return;
      if (!video && (!playlist || !/^[a-zA-Z0-9_-]+$/.test(playlist))) return;
      const src = video
        ? `https://www.youtube.com/embed/${video}?autoplay=1&rel=0&playsinline=1`
        : `https://www.youtube.com/embed/videoseries?list=${playlist}&autoplay=1&rel=0&playsinline=1`;
      const player = document.createElement('div');
      player.className = 'mediaPreview playingVideo';
      const iframe = document.createElement('iframe');
      iframe.src = src;
      iframe.title = preview.getAttribute('aria-label') || 'SonoCalming video';
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      iframe.referrerPolicy = 'strict-origin-when-cross-origin';
      iframe.allowFullscreen = true;
      player.appendChild(iframe);
      preview.replaceWith(player);
    }, { once: true });
  });

  const grid = document.getElementById('libraryGrid');
  if (grid) {
    const search = document.getElementById('librarySearch');
    const category = document.getElementById('libraryCategory');
    const year = document.getElementById('libraryYear');
    const type = document.getElementById('libraryType');
    const count = document.getElementById('libraryCount');
    const empty = document.getElementById('libraryEmpty');
    const cards = [...grid.querySelectorAll('.libraryCard')];
    const normalize = s => (s || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
    const update = () => {
      const q = normalize(search.value);
      let visible = 0;
      for (const card of cards) {
        const matches = (!q || normalize(card.dataset.title).includes(q))
          && (category.value === 'all' || card.dataset.cat === category.value || (category.value === 'Blue Room' && card.dataset.blueRoom === 'true'))
          && (year.value === 'all' || card.dataset.year === year.value)
          && (type.value === 'all' || card.dataset.type === type.value);
        card.hidden = !matches;
        if (matches) visible++;
      }
      count.textContent = `${visible} video${visible === 1 ? '' : 's'} found${visible === cards.length ? ' in the complete SonoCalming library' : ''}`;
      empty.hidden = visible !== 0;
    };
    search.addEventListener('input', update);
    category.addEventListener('change', update);
    year.addEventListener('change', update);
    type.addEventListener('change', update);
  }
})();
