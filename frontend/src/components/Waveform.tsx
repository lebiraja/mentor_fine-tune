import { useEffect, useRef } from 'react';

interface WaveformProps {
  analyser: AnalyserNode | null;
  active: boolean;
}

/** A single thin amber line that breathes with the real mic signal. */
export function Waveform({ analyser, active }: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const data = new Uint8Array(analyser?.fftSize ?? 512);
    let frame = 0;

    const draw = () => {
      frame = requestAnimationFrame(draw);
      ctx.clearRect(0, 0, width, height);
      ctx.beginPath();

      if (analyser && active) {
        analyser.getByteTimeDomainData(data);
        const step = width / data.length;
        for (let i = 0; i < data.length; i++) {
          const y = height / 2 + ((data[i] - 128) / 128) * (height / 2) * 0.9;
          if (i === 0) ctx.moveTo(0, y);
          else ctx.lineTo(i * step, y);
        }
        ctx.strokeStyle = 'rgba(217, 160, 91, 0.7)';
      } else {
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.strokeStyle = 'rgba(217, 160, 91, 0.15)';
      }
      ctx.lineWidth = 1.5;
      ctx.stroke();
    };
    draw();

    return () => cancelAnimationFrame(frame);
  }, [analyser, active]);

  return <canvas ref={canvasRef} className="h-10 w-full" aria-hidden />;
}
