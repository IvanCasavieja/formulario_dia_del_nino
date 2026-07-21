type ConsentCheckboxProps = {
  checked: boolean;
  onChange: (checked: boolean) => void;
  legalText?: string;
};

// PLACEHOLDER: legal team supplies the final terms & conditions / minor's image-use
// authorization copy. Swap it in via the `legalText` prop (or change the default
// below) - no other code needs to change when that happens.
const DEFAULT_LEGAL_TEXT =
  "[PLACEHOLDER] Acepto los términos y condiciones y autorizo el uso de la imagen y el " +
  "video del menor en la campaña. Este texto será reemplazado por el definitivo del " +
  "equipo legal de Tienda Inglesa.";

export function ConsentCheckbox({ checked, onChange, legalText = DEFAULT_LEGAL_TEXT }: ConsentCheckboxProps) {
  return (
    <label className="flex items-start gap-3 rounded-xl border border-line bg-bg p-4 text-sm text-ink-soft">
      <input
        type="checkbox"
        className="mt-1 h-4 w-4 rounded border-line text-brand accent-brand"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span>{legalText}</span>
    </label>
  );
}
