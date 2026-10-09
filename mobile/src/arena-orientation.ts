import { Capacitor } from "@capacitor/core";
import { ScreenOrientation } from "@capacitor/screen-orientation";

/** Real Android lock; the shared arena also renders a rotated landscape surface if the OS refuses. */
export const arenaOrientation = {
  async enter(): Promise<void> {
    if (Capacitor.isNativePlatform()) await ScreenOrientation.lock({ orientation: "landscape" });
    else {
      const orientation = window.screen.orientation as typeof window.screen.orientation & { lock?: (value: string) => Promise<void> };
      await orientation.lock?.("landscape");
    }
  },
  async leave(): Promise<void> {
    if (Capacitor.isNativePlatform()) await ScreenOrientation.unlock();
    else window.screen.orientation?.unlock?.();
  },
};
