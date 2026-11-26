function focusedField(): HTMLElement | null {
  const el = document.activeElement;
  if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
    return el;
  }
  return null;
}

function fitKeyboard() {
  const viewport = window.visualViewport;
  const height = viewport ? viewport.height : window.innerHeight;
  const offset = viewport ? viewport.offsetTop : 0;
  document.documentElement.style.setProperty("--app-height", `${Math.round(height)}px`);
  document.documentElement.style.setProperty("--vv-offset", `${Math.round(offset)}px`);
}

function revealField() {
  const field = focusedField();
  if (!field || field.closest(".composer")) {
    return;
  }
  field.scrollIntoView({ block: "nearest", inline: "nearest" });
}

function markKeyboard(open: boolean) {
  document.documentElement.classList.toggle("keyboard-open", open);
  fitKeyboard();
}

async function watchNativeKeyboard() {
  const { Capacitor } = await import("@capacitor/core");
  if (!Capacitor.isNativePlatform()) {
    return;
  }
  const { Keyboard } = await import("@capacitor/keyboard");
  const { StatusBar } = await import("@capacitor/status-bar");
  await StatusBar.setOverlaysWebView({ overlay: false });
  await Keyboard.addListener("keyboardDidShow", () => markKeyboard(true));
  await Keyboard.addListener("keyboardDidHide", () => markKeyboard(false));
}

export function watchKeyboard() {
  fitKeyboard();
  window.visualViewport?.addEventListener("resize", fitKeyboard);
  window.addEventListener("focusin", () => {
    window.setTimeout(revealField, 250);
  });
  void watchNativeKeyboard();
}
