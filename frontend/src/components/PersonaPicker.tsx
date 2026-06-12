import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Persona } from '@/types/protocol';

interface PersonaPickerProps {
  onBegin: (personaId: string) => void;
}

/** The opening screen: choose who you want to talk to, then begin. */
export function PersonaPicker({ onBegin }: PersonaPickerProps) {
  const [personas, setPersonas] = useState<Persona[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    api
      .listPersonas()
      .then((list) => {
        setPersonas(list);
        setSelected(list[0]?.id ?? null);
      })
      .catch(() => setPersonas([]));
  }, []);

  return (
    <main className="mx-auto flex h-full max-w-md flex-col items-center justify-center gap-8 px-6">
      <div className="text-center">
        <h1 className="font-serif text-3xl font-light tracking-wide text-ink">Clarity</h1>
        <p className="mt-3 text-sm text-ink-dim">who do you want to talk to?</p>
      </div>

      <div className="w-full space-y-1">
        {personas === null ? (
          <p className="text-center text-sm text-ink-faint">…</p>
        ) : personas.length === 0 ? (
          <p className="text-center text-sm text-ember-soft">
            Backend offline — start it and refresh.
          </p>
        ) : (
          personas.map((p) => {
            const active = p.id === selected;
            return (
              <button
                key={p.id}
                onClick={() => setSelected(p.id)}
                className={`flex w-full items-baseline gap-3 rounded-lg border px-4 py-3 text-left transition-colors ${
                  active
                    ? 'border-ember-soft bg-room-soft'
                    : 'border-transparent hover:bg-room-soft'
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 shrink-0 translate-y-1.5 rounded-full ${
                    active ? 'bg-ember' : 'bg-ink-faint'
                  }`}
                />
                <span className={`font-serif text-lg ${active ? 'text-ink' : 'text-ink-dim'}`}>
                  {p.name}
                </span>
                <span className="text-xs text-ink-faint">{p.tagline}</span>
              </button>
            );
          })
        )}
      </div>

      <button
        disabled={!selected}
        onClick={() => selected && onBegin(selected)}
        className="rounded-full border border-ember-soft px-10 py-3 text-ember transition-colors hover:bg-ember hover:text-room disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-ember"
      >
        begin
      </button>

      <p className="text-center text-xs text-ink-faint">Everything stays on this machine.</p>
    </main>
  );
}
