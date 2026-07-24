import { z } from "zod";
import { validationConstants as constants } from "@/lib/validationConstants";

const onlyDigits = (value: string) => value.replace(/\D+/g, "");

export const voteSchema = z.object({
  adult_first_name: z.string().trim().min(1, "Ingresa tu nombre").max(200),
  adult_last_name: z.string().trim().min(1, "Ingresa tu apellido").max(200),
  adult_cedula: z.string().trim().min(1, "Ingresa tu cédula").refine((value) => {
    const digits = onlyDigits(value);
    return digits.length >= constants.PARENT_CEDULA_MIN_DIGITS && digits.length <= constants.PARENT_CEDULA_MAX_DIGITS;
  }, "La cédula debe tener entre 7 y 8 dígitos").refine((value) => !onlyDigits(value).startsWith("0"), "La cédula no puede empezar con 0"),
  adult_email: z.string().trim().email("Ingresa un correo válido"),
  adult_phone: z.string().trim().min(1, "Ingresa un teléfono").refine((value) => {
    const digits = onlyDigits(value);
    return digits.length >= constants.PHONE_MIN_DIGITS && digits.length <= constants.PHONE_MAX_DIGITS;
  }, "El teléfono debe tener entre 8 y 15 dígitos"),
  video_choice: z.string().min(1, "Elegí un video para votar"),
  terms_accepted: z.boolean().refine((value) => value, "Debes aceptar los términos para votar"),
});

export type VoteFormValues = z.infer<typeof voteSchema>;
