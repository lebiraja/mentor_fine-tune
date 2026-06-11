import { useCallback, useRef, useState } from 'react';

const TTS_SAMPLE_RATE = 24000;

interface Playback {
  /** Queue a chunk of 24kHz int16 PCM for gapless playback. */
  enqueue: (pcm: ArrayBuffer) => void;
  /** Stop immediately and drop everything queued (barge-in). */
  flush: () => void;
  isPlaying: boolean;
  muted: boolean;
  setMuted: (muted: boolean) => void;
}

export function usePlayback(): Playback {
  const ctxRef = useRef<AudioContext | null>(null);
  const cursorRef = useRef(0);
  const sourcesRef = useRef(new Set<AudioBufferSourceNode>());
  const mutedRef = useRef(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [muted, setMutedState] = useState(false);

  const ensureContext = (): AudioContext => {
    if (!ctxRef.current || ctxRef.current.state === 'closed') {
      ctxRef.current = new AudioContext({ sampleRate: TTS_SAMPLE_RATE });
      cursorRef.current = 0;
    }
    if (ctxRef.current.state === 'suspended') void ctxRef.current.resume();
    return ctxRef.current;
  };

  const enqueue = useCallback((pcm: ArrayBuffer) => {
    if (mutedRef.current || pcm.byteLength < 2) return;
    const ctx = ensureContext();

    const int16 = new Int16Array(pcm);
    const buffer = ctx.createBuffer(1, int16.length, TTS_SAMPLE_RATE);
    const channel = buffer.getChannelData(0);
    for (let i = 0; i < int16.length; i++) channel[i] = int16[i] / 32768;

    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);

    const startAt = Math.max(ctx.currentTime + 0.02, cursorRef.current);
    cursorRef.current = startAt + buffer.duration;
    sourcesRef.current.add(source);
    setIsPlaying(true);

    source.onended = () => {
      sourcesRef.current.delete(source);
      if (sourcesRef.current.size === 0) setIsPlaying(false);
    };
    source.start(startAt);
  }, []);

  const flush = useCallback(() => {
    for (const source of sourcesRef.current) {
      source.onended = null;
      try {
        source.stop();
      } catch {
        // already stopped
      }
    }
    sourcesRef.current.clear();
    cursorRef.current = 0;
    setIsPlaying(false);
  }, []);

  const setMuted = useCallback(
    (value: boolean) => {
      mutedRef.current = value;
      setMutedState(value);
      if (value) flush();
    },
    [flush]
  );

  return { enqueue, flush, isPlaying, muted, setMuted };
}
