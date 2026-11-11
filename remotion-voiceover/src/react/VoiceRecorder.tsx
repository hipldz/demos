import {useEffect, useId, useMemo, useRef, useState, type RefObject} from 'react';
import type {PlayerRef} from '@remotion/player';
import {getVoiceCaptions, getVoiceRange, parseVoiceManifest, voiceCoverage, voiceDurationLabel, voiceSeconds,
  type VoiceManifest, type VoiceoverProject, type VoiceoverStorage, type VoiceScope, type VoiceTrack} from '../core/index.js';
import {microphoneError, recorderMimeType, recordingToWave} from './audio.js';
import {createHttpVoiceoverStorage} from './storage.js';

type Phase = 'idle' | 'requesting' | 'countdown' | 'recording' | 'processing' | 'saving' | 'audition';
type Take = {scope: VoiceScope; startFrame: number; durationInFrames: number; wav: Blob; url: string; saved: boolean};
type Session = {
  recorder: MediaRecorder; stream: MediaStream; context: AudioContext; analyser: AnalyserNode;
  scope: VoiceScope; start: number; frames: number; chunks: Blob[]; cancelled: boolean;
  startedAt: number; raf: number; timer: ReturnType<typeof setTimeout> | null;
};
export type VoiceRecorderProps = {
  project: VoiceoverProject; player: RefObject<PlayerRef | null>; currentSceneId?: string; frame: number; manifest: VoiceManifest;
  storage?: VoiceoverStorage; assetUrl?: (src: string) => string;
  onManifest: (manifest: VoiceManifest) => void; onBusy: (busy: boolean) => void;
  onDraft: (track: VoiceTrack | null) => void; onSeek: (frame: number) => void;
};

const MicIcon = () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
  <rect x="8" y="2" width="8" height="13" rx="4"/><path d="M 5 10 v 2 a 7 7 0 0 0 14 0 v -2 M 12 19 v 3 M 8 22 h 8"/>
</svg>;

const defaultAssetUrl = (src: string) => /^(blob:|data:|https?:\/\/|\/)/.test(src) ? src : `/${src}`;

export const VoiceRecorder = ({project, player, currentSceneId, frame, manifest, onManifest, onBusy, onDraft, onSeek,
  storage: providedStorage, assetUrl = defaultAssetUrl}: VoiceRecorderProps) => {
  const FPS = project.fps;
  const scenes = project.scenes ?? [];
  const recordable = scenes.filter(scene => scene.recordable !== false);
  const storage = useMemo(() => providedStorage ?? createHttpVoiceoverStorage(project), [providedStorage, project]);
  const scopeId = useId();
  const [scope, setScope] = useState<VoiceScope>(recordable[0]?.id ?? 'full');
  const [phase, setPhase] = useState<Phase>('idle');
  const [countdown, setCountdown] = useState(3);
  const [elapsed, setElapsed] = useState(0);
  const [level, setLevel] = useState(0);
  const [microphone, setMicrophone] = useState('系统默认麦克风');
  const [take, setTake] = useState<Take | null>(null);
  const [message, setMessage] = useState('选择镜头，跟着画面和字幕录音。');
  const [error, setError] = useState<string | null>(null);
  const session = useRef<Session | null>(null);
  const token = useRef(0);
  const mounted = useRef(true);
  const restoreMuted = useRef(false);
  const draftUrl = useRef<string | null>(null);
  const pending = useRef<{stream: MediaStream; context?: AudioContext} | null>(null);
  const scriptBox = useRef<HTMLDivElement>(null);
  const takeAudio = useRef<HTMLAudioElement>(null);
  const busy = phase !== 'idle';
  const selected = getVoiceRange(scope, project);
  const startFrame = selected.from;
  const durationFrames = selected.durationInFrames;
  const cues = getVoiceCaptions(scope, project);
  const activeCue = cues.find(cue => frame >= cue.startFrame && frame < cue.endFrame);
  const saved = manifest.tracks.find(track => track.scope === scope);
  const coverage = voiceCoverage(manifest.tracks, project);
  const nextScene = scope === 'full' ? undefined : recordable[recordable.findIndex(scene => scene.id === scope) + 1];

  useEffect(() => {onBusy(busy);}, [busy, onBusy]);
  useEffect(() => {
    const current = scenes.find(scene => scene.id === currentSceneId);
    if (!busy && scope !== 'full' && (!take || take.saved) && current && current.recordable !== false) {
      setScope(current.id);
      if (take?.saved && take.scope !== current.id) {
        setTake(null);
        if (draftUrl.current) URL.revokeObjectURL(draftUrl.current);
        draftUrl.current = null;
      }
    }
  }, [currentSceneId]);
  useEffect(() => {
    if (phase !== 'recording' && phase !== 'audition') return;
    const box = scriptBox.current;
    const active = box?.querySelector<HTMLElement>('[data-active="true"]');
    if (box && active) box.scrollTo({top: Math.max(0, active.offsetTop - 32), behavior: 'smooth'});
  }, [activeCue?.startFrame, phase]);
  const setStatus = (next: Phase) => {if (mounted.current) setPhase(next);};
  const restorePlayer = () => {
    player.current?.pause();
    if (restoreMuted.current) player.current?.mute(); else player.current?.unmute();
  };
  const release = (s: Session) => {
    cancelAnimationFrame(s.raf);
    if (s.timer) clearTimeout(s.timer);
    s.stream.getTracks().forEach(track => track.stop());
    if (s.context.state !== 'closed') void s.context.close().catch(() => undefined);
    if (pending.current?.stream === s.stream) pending.current = null;
    if (session.current === s) session.current = null;
    if (mounted.current) setLevel(0);
  };
  const stopRecording = () => {
    const s = session.current;
    if (!s || s.recorder.state === 'inactive') return;
    cancelAnimationFrame(s.raf);
    if (s.timer) clearTimeout(s.timer);
    setStatus('processing');
    s.recorder.stop();
    player.current?.pause();
  };
  const cancel = () => {
    token.current++;
    const s = session.current;
    if (s) {
      s.cancelled = true;
      if (s.recorder.state !== 'inactive') s.recorder.stop();
      release(s);
    }
    if (pending.current) {
      pending.current.stream.getTracks().forEach(track => track.stop());
      if (pending.current.context?.state !== 'closed') void pending.current.context?.close().catch(() => undefined);
      pending.current = null;
    }
    onDraft(null);
    restorePlayer();
    setStatus('idle');
    setMessage('已取消，可以重新录制。');
  };
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false; token.current++;
      const s = session.current;
      if (s) {s.cancelled = true; if (s.recorder.state !== 'inactive') s.recorder.stop(); release(s);}
      if (pending.current) {
        pending.current.stream.getTracks().forEach(track => track.stop());
        if (pending.current.context?.state !== 'closed') void pending.current.context?.close().catch(() => undefined);
      }
      if (draftUrl.current) URL.revokeObjectURL(draftUrl.current);
    };
  }, []);
  useEffect(() => {
    const onVisibility = () => {if (document.hidden && session.current?.recorder.state === 'recording') stopRecording();};
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, []);

  const record = async () => {
    const request = ++token.current;
    setError(null); onDraft(null); setElapsed(0); setCountdown(3);
    player.current?.pause();
    takeAudio.current?.pause();
    restoreMuted.current = player.current?.isMuted() ?? false;
    player.current?.mute();
    setStatus('requesting'); setMessage('请允许浏览器使用麦克风。');
    try {
      if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
        throw new Error('请用 Chrome 或 Edge，通过 localhost 或 HTTPS 打开录音页。');
      }
      const stream = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true}});
      if (request !== token.current || !mounted.current) {stream.getTracks().forEach(track => track.stop()); return;}
      pending.current = {stream};
      const context = new AudioContext();
      pending.current.context = context;
      await context.resume();
      if (request !== token.current || !mounted.current) return;
      const analyser = context.createAnalyser(); analyser.fftSize = 256;
      context.createMediaStreamSource(stream).connect(analyser);
      const mimeType = recorderMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? {mimeType, audioBitsPerSecond: 128000} : undefined);
      const s: Session = {recorder, stream, context, analyser, scope, start: startFrame, frames: durationFrames,
        chunks: [], cancelled: false, startedAt: 0, raf: 0, timer: null};
      session.current = s;
      setMicrophone(stream.getAudioTracks()[0]?.label || '麦克风已连接');
      recorder.ondataavailable = event => {if (event.data.size) s.chunks.push(event.data);};
      recorder.onerror = () => {setError('麦克风录音中断，请重新录制。'); cancel();};
      recorder.onstop = async () => {
        const blob = new Blob(s.chunks, {type: recorder.mimeType});
        release(s); restorePlayer();
        if (s.cancelled || request !== token.current || !mounted.current) return;
        try {
          const wave = await recordingToWave(blob, s.frames / FPS);
          if (request !== token.current || !mounted.current) return;
          if (wave.seconds < .1) throw new Error('录音太短，请再录一次。');
          if (draftUrl.current) URL.revokeObjectURL(draftUrl.current);
          const url = URL.createObjectURL(wave.blob); draftUrl.current = url;
          setTake({scope: s.scope, startFrame: s.start, durationInFrames: Math.min(s.frames, Math.floor(wave.seconds * FPS + 1e-6)), wav: wave.blob, url, saved: false});
          setMessage('录音完成。先试听，满意后保存。');
          setStatus('idle');
        } catch (err) {setError(microphoneError(err)); setStatus('idle');}
      };
      onSeek(s.start);
      setStatus('countdown'); setMessage('倒计时结束后开始朗读。');
      const meter = new Float32Array(analyser.fftSize);
      let lastUpdate = 0;
      const tick = (now: number) => {
        if (s.cancelled || session.current !== s) return;
        analyser.getFloatTimeDomainData(meter);
        if (now - lastUpdate > 60) {
          const rms = Math.sqrt(meter.reduce((sum, value) => sum + value * value, 0) / meter.length);
          setLevel(Math.min(1, rms * 5));
          if (s.startedAt) setElapsed(Math.min(s.frames / FPS, (now - s.startedAt) / 1000));
          lastUpdate = now;
        }
        if (s.startedAt) {
          const frameNow = s.start + Math.floor((now - s.startedAt) / 1000 * FPS);
          // The preview follows the recording clock, even if a 3D frame is slow.
          if (frameNow >= s.start + s.frames) {onSeek(s.start + s.frames - 1); stopRecording(); return;}
          if (player.current?.getCurrentFrame() !== frameNow) onSeek(frameNow);
        }
        s.raf = requestAnimationFrame(tick);
      };
      s.raf = requestAnimationFrame(tick);
      for (const count of [3, 2, 1]) {
        if (request !== token.current) return;
        setCountdown(count);
        await new Promise<void>(done => setTimeout(done, 1000));
      }
      if (request !== token.current) return;
      recorder.onstart = () => {
        s.startedAt = performance.now();
        setStatus('recording'); setMessage('正在录音，影片已静音。');
        s.timer = setTimeout(stopRecording, s.frames / FPS * 1000 + 100);
      };
      recorder.start(250);
    } catch (err) {
      if (request !== token.current || !mounted.current) return;
      const s = session.current; if (s) release(s);
      if (pending.current) {
        pending.current.stream.getTracks().forEach(track => track.stop());
        if (pending.current.context?.state !== 'closed') void pending.current.context?.close().catch(() => undefined);
        pending.current = null;
      }
      restorePlayer(); setError(microphoneError(err)); setStatus('idle');
    }
  };

  const audition = async () => {
    if (!take) return;
    takeAudio.current?.pause();
    setError(null); setStatus('audition'); setMessage('跟画面试听中。');
    restoreMuted.current = player.current?.isMuted() ?? false;
    player.current?.unmute();
    onDraft({id: 'draft', scope: take.scope, src: take.url, startFrame: take.startFrame,
      durationInFrames: take.durationInFrames, recordedAt: new Date().toISOString()});
    onSeek(take.startFrame);
    await new Promise<void>(done => requestAnimationFrame(() => requestAnimationFrame(() => done())));
    player.current?.play();
  };
  useEffect(() => {
    if (phase !== 'audition' || !take) return;
    if (frame >= take.startFrame + take.durationInFrames - 1) {
      onDraft(null); player.current?.pause();
      if (restoreMuted.current) player.current?.mute();
      setPhase('idle'); setMessage('试听完成，可以保存或重录。');
    }
  }, [frame, phase, take, onDraft]);

  const save = async () => {
    if (!take) return;
    setError(null); setStatus('saving');
    try {
      const value = await storage.save(take.scope, take.wav);
      onManifest(parseVoiceManifest(value, project));
      setTake({...take, saved: true}); setMessage('已保存到工程，配音已生效。');
    } catch (err) {setError(err instanceof Error ? err.message : '保存失败，可先下载 WAV 保留录音。');}
    finally {setStatus('idle');}
  };
  const remove = async () => {
    setStatus('saving'); setError(null);
    try {
      const value = await storage.remove(scope);
      onManifest(parseVoiceManifest(value, project)); setMessage('已从影片移除，原始录音仍保存在工程中。');
    } catch (err) {setError(err instanceof Error ? err.message : '移除失败');}
    finally {setStatus('idle');}
  };
  const discard = () => {
    onDraft(null); setTake(null);
    if (draftUrl.current) URL.revokeObjectURL(draftUrl.current);
    draftUrl.current = null; setMessage('选择镜头，跟着画面和字幕录音。');
  };
  const nextTake = () => {
    const previousScope = take?.scope;
    const advance = take?.saved && previousScope !== 'full';
    discard();
    if (advance) {
      const next = recordable[recordable.findIndex(scene => scene.id === previousScope) + 1];
      if (next) {setScope(next.id); onSeek(next.from);}
    }
  };

  return <div className="voice-recorder" data-testid="voice-recorder" data-phase={phase}>
    <div className="voice-intro"><strong>自己的声音，自己的影片</strong><p>{recordable.length ? '按片段录一段，满意后保存。' : '跟着画面录制，满意后保存。'}</p></div>
    <div className="voice-progress"><span>已配音 {coverage} / {recordable.length || 1} {recordable.length ? '段' : '整片'}</span><span>真人录音</span></div>
    <label className="voice-label" htmlFor={scopeId}>录制范围</label>
    <select id={scopeId} aria-label="录制范围" disabled={busy || Boolean(take && !take.saved)} value={scope}
      onChange={event => {discard(); setScope(event.target.value); onSeek(getVoiceRange(event.target.value, project).from);}}>
      <option value="full">整片 · {voiceDurationLabel(project.durationInFrames, FPS)}</option>
      {recordable.map(scene => <option key={scene.id} value={scene.id}>{scene.id} · {scene.title} · {voiceDurationLabel(scene.durationInFrames, FPS)}</option>)}
    </select>
    <div className="voice-script" ref={scriptBox} aria-label="朗读稿">
      {!cues.length && <div className="voice-silent-intro">此范围没有提词稿，可以直接跟画面录音。</div>}
      {scope === 'full' && cues.length > 0 && cues[0].startFrame > 0 && <div className="voice-silent-intro">第一句从 {(cues[0].startFrame / FPS).toFixed(1)} 秒开始。</div>}
      {cues.map((cue, index) => <p key={`${cue.startFrame}-${index}`} data-active={frame >= cue.startFrame && frame < cue.endFrame}
        className={frame >= cue.startFrame && frame < cue.endFrame ? 'current-line' : ''}>{cue.text}</p>)}
    </div>
    <div className="voice-microphone"><MicIcon/><span title={microphone}>{microphone}</span></div>
    <div className="voice-meter" role="meter" aria-label="麦克风电平" aria-valuenow={Math.round(level * 100)} aria-valuemin={0} aria-valuemax={100}>
      {Array.from({length:20},(_,i) => <span key={i} className={level * 20 > i ? i > 16 ? 'hot' : 'lit' : ''}/>)}
    </div>
    <div className="voice-status" role="status">
      {phase === 'countdown' ? <><span className="voice-countdown">{countdown}</span><span>{message}</span></> :
        phase === 'recording' ? <><span className="record-dot"/><strong>{elapsed.toFixed(1)} / {(durationFrames / FPS).toFixed(1)}s</strong><span>正在录音</span></> :
          <span>{phase === 'processing' ? '正在整理录音…' : phase === 'saving' ? '正在保存到工程…' : message}</span>}
    </div>
    {error && <div className="voice-error" role="alert">{error}</div>}
    {phase === 'recording' ? <button className="voice-button stop" onClick={stopRecording}>停止录音</button> :
      !busy ? <button className="voice-button primary" onClick={() => void record()}><MicIcon/>{take ? '重新录制' : '开始录音'}</button> : null}
    {busy && phase !== 'processing' && phase !== 'saving' && <button className="voice-button secondary" onClick={cancel}>{phase === 'audition' ? '停止试听' : '取消录音'}</button>}
    {take && !busy && <div className="voice-take" data-testid="voice-take">
      <div className="voice-take-heading"><span>{take.scope} · {(take.durationInFrames / FPS).toFixed(1)}s</span><span>{take.saved ? '已保存' : '尚未保存'}</span></div>
      <audio ref={takeAudio} controls src={take.url} preload="metadata" aria-label="仅试听录音" onPlay={() => player.current?.pause()}/>
      <button className="voice-button secondary" onClick={() => void audition()}>跟画面试听</button>
      <button className="voice-button primary" disabled={take.saved} onClick={() => void save()}>{take.saved ? '已保存并使用' : '保存并使用'}</button>
      <div className="voice-take-links"><a href={take.url} download={`${take.scope.replace(/[<>:"/\\|?*]/g, '_')}-voiceover.wav`}>下载 WAV</a><button onClick={nextTake}>{take.saved ? !nextScene ? '完成本次录音' : '录下一段' : '放弃这次'}</button></div>
    </div>}
    {saved && !take && !busy && <div className="voice-saved" data-testid="saved-voice">
      <div>这段已有配音 · {voiceSeconds(saved, project)}s</div>
      <div className="voice-take-links"><a href={assetUrl(saved.src)} download>下载录音</a><button onClick={() => void remove()}>移除配音</button></div>
    </div>}
    <p className="voice-local-note">录音只保存在当前电脑。保存后，预览与工程会使用你的配音。</p>
  </div>;
};
