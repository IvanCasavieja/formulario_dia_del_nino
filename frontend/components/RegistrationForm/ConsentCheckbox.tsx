import { useEffect, useRef, useState } from 'react';

type ConsentCheckboxProps = {
  checked: boolean;
  onChange: (checked: boolean) => void;
};

// PLACEHOLDER: legal team supplies the final consent copy and the full terms &
// conditions of the raffle (bases, minor's image-use authorization, dates).
// Swap the two constants below when that copy arrives - no other code needs to change.
const TERMS_BODY =
  '[PLACEHOLDER] Acá van las bases y condiciones definitivas del sorteo de Día del Niño: ' +
  'mecánica de participación, criterios de selección de ganadores, uso de los datos ' +
  'personales y de la imagen/video del menor, y vigencia de la promoción. Este texto ' +
  'será reemplazado por el definitivo del equipo legal de Tienda Inglesa.';

export function ConsentCheckbox({ checked, onChange }: ConsentCheckboxProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <>
      <label className="flex items-start gap-3 rounded-xl border border-line bg-bg p-4 text-sm text-ink-soft">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 rounded border-line text-blue accent-blue"
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
        />
        <span>
          [PLACEHOLDER] Acepto los{' '}
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="cursor-pointer font-medium text-blue underline underline-offset-2 hover:text-blue-deep"
          >
            términos y condiciones
          </button>{' '}
          y autorizo el uso de la imagen y el video del menor en la campaña. Este texto será
          reemplazado por el definitivo del equipo legal de Tienda Inglesa.
        </span>
      </label>

      <dialog
        ref={dialogRef}
        onClose={() => setOpen(false)}
        className="m-auto w-full max-w-lg rounded-2xl border border-line bg-surface p-0 shadow-xl backdrop:bg-ink/50 backdrop:backdrop-blur-sm"
      >
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <h2 className="font-display text-lg font-semibold text-ink">Términos y condiciones del sorteo</h2>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Cerrar"
            className="cursor-pointer rounded-full px-2 py-1 text-ink-soft transition hover:bg-bg hover:text-ink"
          >
            ✕
          </button>
        </div>
        <div className="max-h-[60vh] overflow-y-auto px-6 py-5 text-sm text-ink-soft">
          <p>{TERMS_BODY}</p>
        </div>
        <div className="flex justify-end border-t border-line px-6 py-4">
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="cursor-pointer rounded-full bg-blue px-5 py-2 font-display text-sm font-medium text-white transition hover:bg-blue-deep"
          >
            Entendido
          </button>
        </div>
      </dialog>
    </>
  );
}
