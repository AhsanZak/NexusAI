import type { CapacitorConfig } from "@capacitor/cli";
import { KeyboardResize } from "@capacitor/keyboard";

const serverUrl = process.env.CAPACITOR_SERVER_URL ?? "http://192.168.100.19:5173";

const config: CapacitorConfig = {
  appId: "com.nexuai.erp",
  appName: "NexusAI",
  webDir: "dist",
  server: {
    url: serverUrl,
    cleartext: true,
    androidScheme: "http",
  },
  android: {
    allowMixedContent: true,
  },
  plugins: {
    Keyboard: {
      resize: KeyboardResize.Native,
      resizeOnFullScreen: true,
    },
  },
};

export default config;
