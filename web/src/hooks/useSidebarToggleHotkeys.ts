// ⌘⌥[ / ⌘⌥] (Ctrl+Alt+[ / Ctrl+Alt+] on Win/Linux) toggle the left
// (Conversations) and right (Workspace) sidebars. Siblings to the session-switch
// (⌘↑/↓) and approve (⌘↵) hotkeys; like them they fire even inside a focused
// text field, so a panel can be collapsed mid-compose.
//
// Why this chord: the bare ⌘[ / ⌘] are the browser's Back/Forward gestures, and
// single ⌘+punctuation combos (e.g. ⌘\) get swallowed by global hotkey utilities
// (Raycast/Rectangle/…) before the page ever sees them. Adding ⌥ dodges both —
// it's not a browser gesture and is essentially never grabbed system-wide — and
// it shares the ⌘⌥ chord with ChatPage's message-nav hotkey. Bind ONCE at the
// app shell, where the sidebar open-state lives.

import { useEffect, useRef } from "react";

import { matchesCommand } from "@/lib/keymap";

export interface SidebarToggleHandlers {
  /** Flip the left (Conversations) sidebar. Bound to ⌘/Ctrl + ⌥/Alt + [. */
  onToggleLeft: () => void;
  /** Flip the right (Workspace) sidebar. Bound to ⌘/Ctrl + ⌥/Alt + ]. */
  onToggleRight: () => void;
}

export function useSidebarToggleHotkeys(handlers: SidebarToggleHandlers): void {
  // Held in a ref so the bound handler always calls the latest closures without
  // re-registering each render.
  const latest = useRef(handlers);
  latest.current = handlers;

  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent): void => {
      // Ignore auto-repeat: holding the chord would flap the panel open/closed.
      if (e.repeat) return;
      if (matchesCommand("toggle-conversations-sidebar", e)) {
        e.preventDefault();
        e.stopPropagation();
        latest.current.onToggleLeft();
      } else if (matchesCommand("toggle-workspace-sidebar", e)) {
        e.preventDefault();
        e.stopPropagation();
        latest.current.onToggleRight();
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
}
