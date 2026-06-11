import { useCallback, useRef, useState } from 'react';

/** AudioWorklet that batches mic input into ~64ms Int16 PCM chunks. */
const WORKLET_SOURCE = `
class PCMCapture extends AudioWorkletProcessor {
  constructor() {
    super();
    this.chunks = [];
    this.length = 0;
  }
  process(inputs) {
    const channel = inputs[0]?.[0];
    if (channel) {
      this.chunks.push(new Float32Array(channel));
      this.length += channel.length;
      if (this.length >= 1024) {
        const all = new Float32Array(this.length);
        let offset = 0;
        for (const c of this.chunks) {
          all.set(c, offset);
          offset += c.length;
        }
        const pcm = new Int16Array(all.length);
        for (let i = 0; i < all.length; i++) {
          const s = Math.max(-1, Math.min(1, all[i]));
          pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }
        this.port.postMessage(pcm.buffer, [pcm.buffer]);
        this.chunks = [];
        this.length = 0;
      }
    }
    return true;
  }
}
registerProcessor('pcm-capture', PCMCapture);
`;

interface MicStream {
  isActive: boolean;
  error: string | null;
  start: () => Promise<void>;
  stop: () => void;
  /** Mic level analyser for the live waveform (null until started). */
  analyser: AnalyserNode | null;
}

export function useMicStream(onChunk: (pcm: ArrayBuffer) => void): MicStream {
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const onChunkRef = useRef(onChunk);
  onChunkRef.current = onChunk;

  const start = useCallback(async () => {
    if (ctxRef.current) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      const ctx = new AudioContext({ sampleRate: 16000 });
      const workletUrl = URL.createObjectURL(
        new Blob([WORKLET_SOURCE], { type: 'application/javascript' })
      );
      await ctx.audioWorklet.addModule(workletUrl);
      URL.revokeObjectURL(workletUrl);

      const source = ctx.createMediaStreamSource(stream);
      const node = new AudioWorkletNode(ctx, 'pcm-capture');
      node.port.onmessage = (e: MessageEvent<ArrayBuffer>) => onChunkRef.current(e.data);

      const analyserNode = ctx.createAnalyser();
      analyserNode.fftSize = 512;
      source.connect(analyserNode);
      source.connect(node);

      ctxRef.current = ctx;
      streamRef.current = stream;
      setAnalyser(analyserNode);
      setIsActive(true);
      setError(null);
    } catch {
      setError('Microphone unavailable — you can still type below.');
    }
  }, []);

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    void ctxRef.current?.close();
    streamRef.current = null;
    ctxRef.current = null;
    setAnalyser(null);
    setIsActive(false);
  }, []);

  return { isActive, error, start, stop, analyser };
}
