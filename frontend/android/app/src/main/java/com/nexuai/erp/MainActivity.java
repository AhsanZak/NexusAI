package com.nexuai.erp;

import android.os.Build;
import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.CapConfig;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        if (isEmulator()) {
            config = emulatorConfig();
        }
        super.onCreate(savedInstanceState);
    }

    private CapConfig emulatorConfig() {
        try (InputStream input = getAssets().open("capacitor.config.json")) {
            ByteArrayOutputStream buffer = new ByteArrayOutputStream();
            byte[] chunk = new byte[4096];
            int read;
            while ((read = input.read(chunk)) != -1) {
                buffer.write(chunk, 0, read);
            }
            String json = buffer.toString(StandardCharsets.UTF_8.name()).replace("://192.168.100.19", "://127.0.0.1");
            File file = new File(getCacheDir(), "capacitor.config.json");
            try (FileOutputStream output = new FileOutputStream(file)) {
                output.write(json.getBytes(StandardCharsets.UTF_8));
            }
            return CapConfig.loadFromFile(this, getCacheDir().getAbsolutePath());
        } catch (Exception ignored) {
            return null;
        }
    }

    private boolean isEmulator() {
        String fingerprint = Build.FINGERPRINT == null ? "" : Build.FINGERPRINT;
        String model = Build.MODEL == null ? "" : Build.MODEL;
        String hardware = Build.HARDWARE == null ? "" : Build.HARDWARE;
        return fingerprint.startsWith("generic")
            || fingerprint.contains("emulator")
            || model.contains("Emulator")
            || model.contains("Android SDK built for")
            || "goldfish".equals(hardware)
            || "ranchu".equals(hardware);
    }
}
