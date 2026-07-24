import { z } from "zod";

export const voteSchema = z.object({
  adult_first_name: z.string().trim().min(1, "Ingresa tu nombre").max(200),
  adult_last_name: z.string().trim().min(1, "Ingresa tu apellido").max(200),
  adult_email: z.string().trim().email("Ingresa un correo válido"),
  video_choice: z.string().min(1, "Elegí un video para votar"),
  terms_accepted: z.boolean().refine((value) => value, "Debes aceptar los términos para votar"),
});

export type VoteFormValues = z.infer<typeof voteSchema>;
