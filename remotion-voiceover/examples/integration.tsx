import {useEffect, useRef, useState} from 'react';
import {Player, type PlayerRef} from '@remotion/player';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {VoiceRecorder, Voiceover, useVoiceover, useVoiceTracks} from '../src/react/index.js';
import type {VoiceTrack} from '../src/core/index.js';
import {exampleProject} from './project.js';

// Import 'remotion-voiceover/styles.css' in the consuming application's entry.
// Replace this component with your film and keep the Voiceover audio layer.
export const ExampleFilm = ({voiceTracks}: {voiceTracks?: VoiceTrack[]}) => {
  const frame = useCurrentFrame();
  const tracks = useVoiceTracks(exampleProject, voiceTracks);
  const caption = exampleProject.captions?.find(cue => frame >= cue.startFrame && frame < cue.endFrame);
  return <AbsoluteFill style={{background: '#0e141e', color: '#ddd', justifyContent: 'center', alignItems: 'center'}}>
    <h1 style={{fontSize: 70, transform: `translateY(${Math.sin(frame / 30) * 12}px)`}}>你的 Remotion 影片</h1>
    {caption && <div data-testid="example-caption" style={{position: 'absolute', left: 64, right: 64, bottom: 110,
      display: 'flex', justifyContent: 'center', pointerEvents: 'none'}}>
      <span style={{maxWidth: '100%', padding: '12px 24px', borderRadius: 8, background: 'rgba(0, 0, 0, .72)',
        color: '#fff', fontSize: 44, lineHeight: 1.5, textAlign: 'center', whiteSpace: 'pre-wrap'}}>{caption.text}</span>
    </div>}
    <Voiceover project={exampleProject} tracks={tracks}/>
  </AbsoluteFill>;
};

export const ExamplePreview = () => {
  const player = useRef<PlayerRef>(null);
  const [frame, setFrame] = useState(0);
  const voice = useVoiceover(exampleProject);
  useEffect(() => {
    const current = player.current;
    if (!current) return;
    const update: Parameters<PlayerRef['addEventListener']>[1] = event => {
      if (event.detail && 'frame' in event.detail) setFrame(Number(event.detail.frame));
    };
    current.addEventListener('frameupdate', update);
    return () => current.removeEventListener('frameupdate', update);
  }, []);
  const seek = (next: number) => {player.current?.seekTo(next); setFrame(next);};
  return <div className="example-preview">
    {voice.error && <p className="voice-error example-load-error" role="alert">{voice.error}</p>}
    <Player ref={player} component={ExampleFilm} inputProps={{voiceTracks: voice.tracks}}
      fps={exampleProject.fps} durationInFrames={exampleProject.durationInFrames}
      compositionWidth={1280} compositionHeight={720} style={{width: '100%'}}
      controls={!voice.busy} clickToPlay={!voice.busy}/>
    <VoiceRecorder project={exampleProject} player={player} frame={frame} manifest={voice.manifest}
      storage={voice.storage} currentSceneId={exampleProject.scenes?.find(scene => frame >= scene.from && frame < scene.from + scene.durationInFrames)?.id}
      onManifest={voice.setManifest} onBusy={voice.setBusy} onDraft={voice.setDraft} onSeek={seek}/>
  </div>;
};
