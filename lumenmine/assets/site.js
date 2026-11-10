"use strict";

const media = window.lumenMineMedia;
if (media?.appStore) {
  try {
    const url = new URL(media.appStore);
    if (url.origin === "https://apps.apple.com") {
      for (const link of document.querySelectorAll("[data-app-store]")) {
        link.href = url.href;
        link.hidden = false;
      }
    }
  } catch {
    // Leave the store link hidden until a valid listing URL is configured.
  }
}

const trailer = document.querySelector("[data-trailer]");
if (trailer && /^[-\w]+\.mp4$/i.test(media?.trailer ?? "")) {
  trailer.src = new URL(media.trailer, document.currentScript.src).href;
  trailer.addEventListener("loadedmetadata", () => {
    trailer.closest("section").hidden = false;
  }, {once: true});
}
