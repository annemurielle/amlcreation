"use strict";
// The original YouTube link remains available when JavaScript is disabled.
document.querySelectorAll(".video-facade[data-video]").forEach((facade) => {
  const link = facade.querySelector(".video-launch");
  if (!link) return;
  link.addEventListener("click", (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    const id = facade.dataset.video;
    if (!/^[A-Za-z0-9_-]{11}$/.test(id)) return;
    const iframe = document.createElement("iframe");
    iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`;
    iframe.title = facade.dataset.title || "Game video";
    iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    iframe.allowFullscreen = true;
    iframe.referrerPolicy = "strict-origin-when-cross-origin";
    facade.replaceChildren(iframe);
    iframe.focus();
  });
});
