import {
  AudioOutlined,
  CameraOutlined,
  EnvironmentOutlined,
  NotificationOutlined,
  PictureOutlined,
  ShareAltOutlined,
} from "@ant-design/icons";
import { Button, Space, Typography } from "antd";
import { useState } from "react";

import {
  currentLocation,
  isNativeApp,
  notify,
  pickGallery,
  readSavedBlob,
  readSavedText,
  saveBlob,
  saveText,
  shareText,
  startMicrophone,
  takePhoto,
} from "../native/device";
import { useNarrow } from "../ui/useNarrow";

export function DeviceActions({
  busy,
  onFile,
  shareTitle,
  shareTextValue,
  onMessage,
}: {
  busy?: boolean;
  onFile?: (file: File) => void;
  shareTitle?: string;
  shareTextValue?: string;
  onMessage?: (message: string) => void;
}) {
  const narrow = useNarrow();
  const native = isNativeApp();
  const [recording, setRecording] = useState<{ stop: () => Promise<File> } | null>(null);
  const [working, setWorking] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  if (!narrow && !native) {
    return null;
  }

  async function run(action: () => Promise<string | void>) {
    setWorking(true);
    try {
      const next = await action();
      if (next) {
        setNote(next);
      }
    } catch (reason) {
      onMessage?.(reason instanceof Error ? reason.message : "The phone feature could not be used");
    } finally {
      setWorking(false);
    }
  }

  return (
    <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
      <Space className="device-actions" wrap>
        <Button
          icon={<CameraOutlined />}
          disabled={busy || working || !onFile}
          onClick={() =>
            void run(async () => {
              onFile?.(await takePhoto());
              return "Photo captured.";
            })
          }
        >
          Camera
        </Button>
        <Button
          icon={<PictureOutlined />}
          disabled={busy || working || !onFile}
          onClick={() =>
            void run(async () => {
              onFile?.(await pickGallery());
              return "Photo selected from the gallery.";
            })
          }
        >
          Gallery
        </Button>
        <Button
          icon={<AudioOutlined />}
          danger={recording !== null}
          disabled={busy || working}
          onClick={() =>
            void run(async () => {
              if (recording) {
                const file = await recording.stop();
                setRecording(null);
                const uri = await saveBlob(file.name, file);
                const saved = await readSavedBlob(file.name);
                await notify("Recording saved", file.name);
                return `Saved ${saved.size} bytes from the microphone at ${uri}`;
              }
              setRecording(await startMicrophone());
              return "Recording. Tap Record again to stop and save it.";
            })
          }
        >
          {recording ? "Stop" : "Record"}
        </Button>
        <Button
          icon={<ShareAltOutlined />}
          disabled={busy || working || !shareTextValue}
          onClick={() =>
            void run(async () => {
              await shareText(shareTitle || "NexusAI", shareTextValue || "");
            })
          }
        >
          Share
        </Button>
        <Button
          icon={<EnvironmentOutlined />}
          disabled={busy || working}
          onClick={() =>
            void run(async () => {
              const place = await currentLocation();
              const text = `${place.latitude.toFixed(5)}, ${place.longitude.toFixed(5)}`;
              await saveText("location.txt", text);
              const stored = await readSavedText("location.txt");
              return `Location ${stored}`;
            })
          }
        >
          Location
        </Button>
        <Button
          icon={<NotificationOutlined />}
          disabled={busy || working}
          onClick={() =>
            void run(async () => {
              await notify("NexusAI", "Notifications are on for this phone.");
              return "A notification was sent.";
            })
          }
        >
          Alerts
        </Button>
      </Space>
      {note ? <Typography.Text type="secondary">{note}</Typography.Text> : null}
    </Space>
  );
}
