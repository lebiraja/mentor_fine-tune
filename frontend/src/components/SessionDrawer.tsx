import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Session } from '@/types/protocol';

interface SessionDrawerProps {
  open: boolean;
  onClose: () => void;
  currentSessionId: string | null;
  onSelect: (sessionId: string, persona?: string) => void;
  onNewConversation: () => void;
}

export function SessionDrawer({
  open,
  onClose,
  currentSessionId,
  onSelect,
  onNewConversation,
}: SessionDrawerProps) {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    if (open) {
      api.listSessions().then(setSessions).catch(() => setSessions([]));
    }
  }, [open]);

  const handleDelete = async (id: string) => {
    await api.deleteSession(id).catch(() => undefined);
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (id === currentSessionId) onNewConversation();
  };

  return (
    <>
      {open && (
        <button
          aria-label="Close conversations"
          className="fixed inset-0 z-20 bg-black/50"
          onClick={onClose}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-72 transform border-r border-room-line bg-room-soft transition-transform duration-200 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-full flex-col p-4">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm tracking-widest text-ink-dim uppercase">Conversations</h2>
            <button
              onClick={onClose}
              className="text-ink-faint hover:text-ink"
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          <button
            onClick={() => {
              onNewConversation();
              onClose();
            }}
            className="mb-3 rounded border border-room-line px-3 py-2 text-left text-sm text-ember hover:bg-room"
          >
            + New conversation
          </button>

          <div className="flex-1 space-y-1 overflow-y-auto">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`group flex items-center gap-2 rounded px-3 py-2 ${
                  session.id === currentSessionId ? 'bg-room' : 'hover:bg-room'
                }`}
              >
                <button
                  className="flex-1 truncate text-left hover:text-ink"
                  onClick={() => {
                    onSelect(session.id, session.persona);
                    onClose();
                  }}
                >
                  <span className="block truncate text-sm text-ink-dim">{session.title}</span>
                  {session.persona && (
                    <span className="text-xs text-ink-faint">{session.persona}</span>
                  )}
                </button>
                <button
                  onClick={() => void handleDelete(session.id)}
                  className="hidden text-xs text-ink-faint hover:text-ember group-hover:block"
                  aria-label={`Delete ${session.title}`}
                >
                  del
                </button>
              </div>
            ))}
            {sessions.length === 0 && (
              <p className="px-3 py-2 text-sm text-ink-faint">Nothing yet.</p>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
