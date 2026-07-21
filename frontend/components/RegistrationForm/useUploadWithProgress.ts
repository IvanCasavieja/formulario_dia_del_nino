import { useCallback, useState } from "react";

export function useUploadWithProgress() {
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const upload = useCallback(async (url: string, file: File, contentType: string) => {
    setIsUploading(true);
    setProgress(0);

    return await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("PUT", url, true);
      // Must exactly match the video_content_type sent to POST /api/submissions - R2's
      // presigned URL signature is pinned to that Content-Type, so a mismatch here
      // fails the PUT with a signature error rather than uploading successfully.
      xhr.setRequestHeader("Content-Type", contentType);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          setProgress(Math.round((event.loaded / event.total) * 100));
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          reject(new Error(`No se pudo subir el video (${xhr.status})`));
        }
      };

      xhr.onerror = () => reject(new Error("Error de red al subir el video"));
      xhr.send(file);
    }).finally(() => {
      setIsUploading(false);
    });
  }, []);

  return { progress, isUploading, upload };
}
