// Re-exports /shared/validationConstants.json directly rather than hand-copying the
// values - this is the single source of truth the backend also reads (see
// backend/app/shared_constants.py). Editing the JSON file updates both sides; nothing
// here should hardcode a limit that could silently drift from the server-side check.
// (Requires turbopack.root in next.config.ts, since /shared sits outside the
// auto-detected Next.js project root.)
import raw from "../../shared/validationConstants.json";

export const validationConstants = raw as {
  MAX_VIDEO_DURATION_SECONDS: number;
  MAX_VIDEO_DURATION_TOLERANCE_SECONDS: number;
  MAX_VIDEO_SIZE_BYTES: number;
  ALLOWED_VIDEO_MIME_TYPES: string[];
  ALLOWED_VIDEO_EXTENSIONS: string[];
  PARENT_CEDULA_MIN_DIGITS: number;
  PARENT_CEDULA_MAX_DIGITS: number;
  CHILD_CEDULA_MIN_DIGITS: number;
  CHILD_CEDULA_MAX_DIGITS: number;
  PHONE_MIN_DIGITS: number;
  PHONE_MAX_DIGITS: number;
};

// Mirrors backend/app/shared_constants.py's MIME_TYPE_TO_EXTENSION - some browsers
// (notably Safari/iOS for .mov) leave File.type empty, so content-type has to be
// inferable from the extension too, on both ends of the same PUT request.
export const EXTENSION_TO_MIME_TYPE: Record<string, string> = {
  ".mp4": "video/mp4",
  ".mov": "video/quicktime",
  ".webm": "video/webm",
};

export function resolveVideoContentType(file: File): string | null {
  if (file.type && validationConstants.ALLOWED_VIDEO_MIME_TYPES.includes(file.type)) {
    return file.type;
  }
  const name = file.name.toLowerCase();
  const extension = validationConstants.ALLOWED_VIDEO_EXTENSIONS.find((ext) => name.endsWith(ext));
  return extension ? EXTENSION_TO_MIME_TYPE[extension] ?? null : null;
}
