import { useRef, useCallback, useEffect, useState } from 'react';

export function useVoiceProcessing() {
  const audioContextRef = useRef<AudioContext | null>(null);
  const isMutedRef = useRef(false);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    return () => {
      audioContextRef.current?.close();
    };
  }, []);

  const playAudioResponse = useCallback(async (audioData: ArrayBuffer) => {
    if (!audioContextRef.current || isMutedRef.current) return;

    try {
      setIsPlaying(true);
      const audioBuffer = await audioContextRef.current.decodeAudioData(audioData.slice(0));
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      source.onended = () => setIsPlaying(false);
      source.start(0);
    } catch (error) {
      console.error('Audio playback error:', error);
      // Fallback for raw PCM if decode fails
      try {
        const audioBuffer = audioContextRef.current.createBuffer(1, audioData.byteLength / 2, 16000);
        const channelData = audioBuffer.getChannelData(0);
        const view = new Int16Array(audioData);
        for (let i = 0; i < view.length; i++) {
          channelData[i] = view[i] / 32768.0;
        }
        const source = audioContextRef.current.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContextRef.current.destination);
        source.onended = () => setIsPlaying(false);
        source.start(0);
      } catch (fallbackError) {
        console.error('Fallback audio failed:', fallbackError);
        setIsPlaying(false);
      }
    }
  }, []);

  const setMuted = useCallback((muted: boolean) => {
    isMutedRef.current = muted;
  }, []);

  return {
    playAudioResponse,
    setMuted,
    isPlaying
  };
}
