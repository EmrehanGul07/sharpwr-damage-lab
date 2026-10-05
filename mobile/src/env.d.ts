/** Build-time values, set in vite.config.ts and by the Android workflow. */

/** Unique per build; data saved by another build is not reused (src/online.ts). */
declare const __APP_BUILD__: string;

interface ImportMetaEnv {
  /** "1" in GitHub preview builds: show a notice when a newer app version is published. */
  readonly VITE_PREVIEW_BUILD?: string;
}
