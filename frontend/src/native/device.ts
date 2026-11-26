import { Camera, CameraResultType, CameraSource } from "@capacitor/camera";
import { Capacitor } from "@capacitor/core";
import { Directory, Encoding, Filesystem } from "@capacitor/filesystem";
import { Geolocation } from "@capacitor/geolocation";
import { LocalNotifications } from "@capacitor/local-notifications";
import { Share } from "@capacitor/share";

export function isNativeApp(): boolean {
  return Capacitor.isNativePlatform();
}

async function photoFile(source: CameraSource): Promise<File> {
  const photo = await Camera.getPhoto({
    source,
    quality: 85,
    resultType: CameraResultType.Uri,
    correctOrientation: true,
  });
  if (!photo.webPath) {
    throw new Error("The photo could not be read");
  }
  const response = await fetch(photo.webPath);
  const blob = await response.blob();
  const extension = photo.format || "jpeg";
  return new File([blob], `photo-${Date.now()}.${extension}`, {
    type: blob.type || `image/${extension}`,
  });
}

export function takePhoto(): Promise<File> {
  return photoFile(CameraSource.Camera);
}

export function pickGallery(): Promise<File> {
  return photoFile(CameraSource.Photos);
}

export function startMicrophone(): Promise<{ stop: () => Promise<File> }> {
  return navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
    const recorder = new MediaRecorder(stream);
    const chunks: Blob[] = [];
    const stopped = new Promise<File>((resolve, reject) => {
      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      });
      recorder.addEventListener("error", () => {
        reject(new Error("The microphone could not record"));
      });
      recorder.addEventListener("stop", () => {
        const type = recorder.mimeType || "audio/webm";
        const blob = new Blob(chunks, { type });
        resolve(new File([blob], `recording-${Date.now()}.webm`, { type }));
      });
    });
    recorder.start();
    return {
      stop: () => {
        if (recorder.state !== "inactive") {
          recorder.stop();
        }
        stream.getTracks().forEach((track) => track.stop());
        return stopped;
      },
    };
  });
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const value = String(reader.result || "");
      resolve(value.slice(value.indexOf(",") + 1));
    };
    reader.onerror = () => reject(new Error("The file could not be saved"));
    reader.readAsDataURL(blob);
  });
}

export async function saveBlob(name: string, blob: Blob): Promise<string> {
  const written = await Filesystem.writeFile({
    path: name,
    data: await blobToBase64(blob),
    directory: Directory.Documents,
  });
  return written.uri;
}

export async function readSavedBlob(name: string): Promise<Blob> {
  const stored = await Filesystem.readFile({
    path: name,
    directory: Directory.Documents,
  });
  const raw = String(stored.data);
  const response = await fetch(`data:application/octet-stream;base64,${raw}`);
  return response.blob();
}

export async function saveText(name: string, text: string): Promise<string> {
  const written = await Filesystem.writeFile({
    path: name,
    data: text,
    directory: Directory.Documents,
    encoding: Encoding.UTF8,
  });
  return written.uri;
}

export async function readSavedText(name: string): Promise<string> {
  const stored = await Filesystem.readFile({
    path: name,
    directory: Directory.Documents,
    encoding: Encoding.UTF8,
  });
  return String(stored.data);
}

export async function shareText(title: string, text: string): Promise<void> {
  try {
    await Share.share({ title, text, dialogTitle: title });
    return;
  } catch (reason) {
    const message = reason instanceof Error ? reason.message : "";
    if (/cancel/i.test(message)) {
      return;
    }
  }
  if (navigator.share) {
    await navigator.share({ title, text });
    return;
  }
  await navigator.clipboard.writeText(text);
}

export async function currentLocation(): Promise<{ latitude: number; longitude: number }> {
  if (isNativeApp()) {
    const position = await Geolocation.getCurrentPosition({ enableHighAccuracy: true });
    return { latitude: position.coords.latitude, longitude: position.coords.longitude };
  }
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("This browser cannot read the location"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({ latitude: position.coords.latitude, longitude: position.coords.longitude });
      },
      () => reject(new Error("Location permission was denied")),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  });
}

export async function notify(title: string, body: string): Promise<void> {
  if (isNativeApp()) {
    const permission = await LocalNotifications.requestPermissions();
    if (permission.display !== "granted") {
      throw new Error("Notifications are turned off for NexusAI");
    }
    await LocalNotifications.schedule({
      notifications: [
        {
          id: Date.now() % 2147483647,
          title,
          body,
          schedule: { at: new Date(Date.now() + 800) },
        },
      ],
    });
    return;
  }
  if (!("Notification" in window)) {
    throw new Error("This browser cannot show notifications");
  }
  if (Notification.permission !== "granted") {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      throw new Error("Notifications are turned off");
    }
  }
  new Notification(title, { body });
}
