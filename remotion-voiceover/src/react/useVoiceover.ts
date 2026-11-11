import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {EMPTY_VOICE_MANIFEST, previewVoiceTracks, type VoiceManifest, type VoiceoverProject,
  type VoiceoverStorage, type VoiceTrack} from '../core/index.js';
import {createHttpVoiceoverStorage} from './storage.js';

export const useVoiceover = (project: VoiceoverProject, options: {storage?: VoiceoverStorage; endpoint?: string} = {}) => {
  const storage = useMemo(() => options.storage ?? createHttpVoiceoverStorage(project, {endpoint: options.endpoint}),
    [project, options.storage, options.endpoint]);
  const [manifest, setManifest] = useState<VoiceManifest>(EMPTY_VOICE_MANIFEST);
  const [draft, setDraft] = useState<VoiceTrack | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(false);
  const generation = useRef(0);
  const refresh = useCallback(async () => {
    const request = ++generation.current;
    try {
      const value = await storage.load();
      if (mounted.current && generation.current === request) {setManifest(value); setError(null);}
    } catch (failure) {
      if (mounted.current && generation.current === request) setError(failure instanceof Error ? failure.message : '无法读取配音');
    }
  }, [storage]);
  useEffect(() => {
    mounted.current = true;
    void refresh();
    const onFocus = () => {void refresh();};
    window.addEventListener('focus', onFocus);
    return () => {mounted.current = false; generation.current++; window.removeEventListener('focus', onFocus);};
  }, [refresh]);
  const tracks = useMemo(() => previewVoiceTracks(manifest, draft), [manifest, draft]);
  return {manifest, draft, tracks, busy, error, storage, refresh, setManifest, setDraft, setBusy};
};
