export type {
  KeyBinding,
  KeymapCommand,
  KeymapCommandId,
  KeymapDisplayContext,
  KeymapGroupId,
  KeymapKeyEvent,
  KeymapScope,
  KeymapShortcutGroup,
  ModifierRequirement,
  PlatformKeyBinding,
} from "./types";

export { altKeyLabel, defaultDisplayContext, isMacPlatform, modKeyLabel } from "./platform";

export {
  KEYMAP_COMMAND_IDS,
  KEYMAP_COMMANDS,
  getKeymapCommand,
  getShortcutGroups,
  PINNED_HOTKEY_CODES,
  PINNED_HOTKEY_DIGITS,
  resolveCommandDefaultBinding,
} from "./registry";

export {
  clearKeymapOverrides,
  getEffectiveBinding,
  isCommandOverridden,
  isPlatformBinding,
  readKeymapOverrides,
  writeKeymapOverride,
  type KeymapOverrides,
} from "./preferences";

export {
  matchesBinding,
  matchesCommand,
  pinnedSessionIndexFromEvent,
  resolveDefaultBinding,
} from "./matcher";
