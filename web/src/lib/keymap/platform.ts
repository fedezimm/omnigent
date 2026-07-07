// Platform-aware modifier labels and display glyphs for shortcut lists.

import type { KeymapDisplayContext } from "./types";

/** True on macOS / iOS — matches the handlers' `metaKey || ctrlKey` split. */
export function isMacPlatform(): boolean {
  if (typeof navigator === "undefined") return false;
  return /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent || "");
}

/** Modifier label shown in menu hints (⌘ on macOS, Ctrl elsewhere). */
export function modKeyLabel(): string {
  return isMacPlatform() ? "⌘" : "Ctrl";
}

export function altKeyLabel(): string {
  return isMacPlatform() ? "⌥" : "Alt";
}

export function defaultDisplayContext(isNativeShell: boolean): KeymapDisplayContext {
  return {
    modKey: modKeyLabel(),
    altKey: altKeyLabel(),
    shiftKey: "⇧",
    enterKey: "↵",
    upKey: "↑",
    downKey: "↓",
    isNativeShell,
  };
}
