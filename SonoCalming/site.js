(()=>{
  const b=document.querySelector('#menu'),n=document.querySelector('#links');
  if(b&&n){
    b.addEventListener('click',()=>{const o=n.classList.toggle('open');b.setAttribute('aria-expanded',String(o))});
  }
  document.querySelectorAll('.js-player').forEach(btn=>{
    btn.addEventListener('click',()=>{
      if(btn.dataset.loaded==='1') return;
      const video=btn.dataset.video;
      const playlist=btn.dataset.playlist;
      const src=video
        ? `https://www.youtube.com/embed/${video}?autoplay=1&rel=0&playsinline=1`
        : `https://www.youtube.com/embed/videoseries?list=${playlist}&autoplay=1&rel=0&playsinline=1`;
      const iframe=document.createElement('iframe');
      iframe.src=src;
      iframe.title=btn.getAttribute('aria-label')||'SonoCalming player';
      iframe.allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      iframe.referrerPolicy='strict-origin-when-cross-origin';
      iframe.allowFullscreen=true;
      btn.innerHTML='';
      btn.appendChild(iframe);
      btn.dataset.loaded='1';
    });
  });
})();