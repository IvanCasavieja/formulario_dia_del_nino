import { z } from "zod";
import { validationConstants as constants } from "@/lib/validationConstants";

const onlyDigits = (value: string) => value.replace(/\D+/g, "");

export const registrationSchema = z.object({
  parent_first_name: z.string().trim().min(1, "Ingresa el nombre del padre o madre").max(200),
  parent_last_name: z.string().trim().min(1, "Ingresa el apellido").max(200),
  parent_cedula: z.string().trim().min(1, "Ingresa la cédula").refine((value) => {
    const digits = onlyDigits(value);
    return digits.length >= constants.PARENT_CEDULA_MIN_DIGITS && digits.length <= constants.PARENT_CEDULA_MAX_DIGITS;
  }, "La cédula debe tener entre 7 y 8 dígitos").refine((value) => !onlyDigits(value).startsWith("0"), "La cédula no puede empezar con 0"),
  parent_email: z.string().trim().email("Ingresa un correo válido"),
  parent_phone: z.string().trim().min(1, "Ingresa un teléfono").refine((value) => {
    const digits = onlyDigits(value);
    return digits.length >= constants.PHONE_MIN_DIGITS && digits.length <= constants.PHONE_MAX_DIGITS;
  }, "El teléfono debe tener entre 8 y 15 dígitos"),
  child_first_name: z.string().trim().min(1, "Ingresa el nombre del niño o niña").max(200),
  child_last_name: z.string().trim().min(1, "Ingresa el apellido del niño o niña").max(200),
  child_cedula: z.string().trim().min(1, "Ingresa la cédula del menor").refine((value) => {
    const digits = onlyDigits(value);
    return digits.length >= constants.CHILD_CEDULA_MIN_DIGITS && digits.length <= constants.CHILD_CEDULA_MAX_DIGITS;
  }, "La cédula del menor debe tener entre 7 y 8 dígitos").refine((value) => !onlyDigits(value).startsWith("0"), "La cédula del menor no puede empezar con 0"),
  // TEMP (R2 sin contratar, revertir a required cuando exista): .optional() para que
  // zod no bloquee el submit cuando no se elige video. RegistrationForm.tsx arma
  // valores dummy para estos 3 campos si no hay archivo seleccionado.
  video_content_type: z.string().refine((value) => constants.ALLOWED_VIDEO_MIME_TYPES.includes(value), "Formato no soportado").optional(),
  video_declared_size_bytes: z.number().int().positive().max(constants.MAX_VIDEO_SIZE_BYTES, "El video no puede superar 200 MB").optional(),
  video_declared_duration_seconds: z.number().positive().max(constants.MAX_VIDEO_DURATION_SECONDS + constants.MAX_VIDEO_DURATION_TOLERANCE_SECONDS, "El video no puede superar los 60 segundos").optional(),
  terms_accepted: z.boolean().refine((value) => value, "Debes aceptar los términos para participar"),
  terms_version: z.string().min(1),
});

export type RegistrationFormValues = z.infer<typeof registrationSchema>;
