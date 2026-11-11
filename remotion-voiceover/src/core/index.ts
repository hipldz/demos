export type VoiceScope = string;
export type VoiceScene = {
  id: string;
  title: string;
  from: number;
  durationInFrames: number;
  recordable?: boolean;
};
export type VoiceCaption = {startFrame: number; endFrame: number; text: string; sceneId?: string};
export type VoiceoverProject = {
  fps: number;
  durationInFrames: number;
  scenes?: readonly VoiceScene[];
  captions?: readonly VoiceCaption[];
  /** A relative file path inside the consuming project's public directory. */
  manifestSrc?: string;
};
export type VoiceTrack = {
  id: string;
  scope: VoiceScope;
  src: string;
  startFrame: number;
  durationInFrames: number;
  recordedAt: string;
};
export type VoiceManifest = {version: 1; tracks: VoiceTrack[]};
export type VoiceSegment = VoiceTrack & {from: number; duration: number; trimBefore: number};
export type VoiceoverStorage = {
  load: () => Promise<VoiceManifest>;
  save: (scope: VoiceScope, wav: Blob) => Promise<VoiceManifest>;
  remove: (scope: VoiceScope) => Promise<VoiceManifest>;
};
export const EMPTY_VOICE_MANIFEST: VoiceManifest = {version: 1, tracks: []};
export const voiceManifestSrc = (project: VoiceoverProject) => project.manifestSrc ?? 'narration/manifest.json';

export const defineVoiceoverProject = (project: VoiceoverProject): VoiceoverProject => {
  if (!Number.isFinite(project.fps) || project.fps <= 0 ||
    !Number.isInteger(project.durationInFrames) || project.durationInFrames < 1) {
    throw new Error('配音配置需要有效的帧率和总帧数');
  }
  const scenes = [...(project.scenes ?? [])].sort((a, b) => a.from - b.from);
  const ids = new Set<string>();
  for (let i = 0; i < scenes.length; i++) {
    const scene = scenes[i];
    if (typeof scene.id !== 'string' || !scene.id.trim() || scene.id === 'full' || ids.has(scene.id) || typeof scene.title !== 'string' ||
      !Number.isInteger(scene.from) || scene.from < 0 || !Number.isInteger(scene.durationInFrames) ||
      scene.durationInFrames < 1 || scene.from + scene.durationInFrames > project.durationInFrames ||
      (i > 0 && scenes[i - 1].from + scenes[i - 1].durationInFrames > scene.from)) {
      throw new Error('分镜需要唯一编号、有效帧区间，且配音区间不能重叠');
    }
    ids.add(scene.id);
  }
  const captions = [...(project.captions ?? [])].sort((a, b) => a.startFrame - b.startFrame);
  for (const cue of captions) {
    if (!Number.isInteger(cue.startFrame) || cue.startFrame < 0 || !Number.isInteger(cue.endFrame) ||
      cue.endFrame <= cue.startFrame || cue.endFrame > project.durationInFrames || typeof cue.text !== 'string' ||
      (cue.sceneId !== undefined && !ids.has(cue.sceneId))) throw new Error('字幕包含无效时间或分镜编号');
  }
  const path = voiceManifestSrc(project);
  if (!path || path.startsWith('/') || path.includes('\\') || path.includes(':') ||
    path.split('/').some(part => !part || part === '.' || part === '..') || !path.endsWith('.json')) {
    throw new Error('manifestSrc 必须是 public 目录内的相对 JSON 路径');
  }
  return {...project, scenes, captions, manifestSrc: path};
};

export const isVoiceScope = (value: unknown, project: VoiceoverProject): value is VoiceScope =>
  typeof value === 'string' && (value === 'full' || (project.scenes ?? []).some(scene => scene.id === value));

export const getVoiceRange = (scope: VoiceScope, project: VoiceoverProject) => {
  if (scope === 'full') return {from: 0, durationInFrames: project.durationInFrames, title: '整片'};
  const scene = project.scenes?.find(item => item.id === scope);
  if (!scene) throw new Error('请选择有效分镜或整片录音');
  return scene;
};

export const getVoiceCaptions = (scope: VoiceScope, project: VoiceoverProject) => {
  if (scope === 'full') return [...(project.captions ?? [])];
  const range = getVoiceRange(scope, project);
  return (project.captions ?? []).filter(cue => cue.sceneId === scope ||
    (cue.sceneId === undefined && cue.startFrame < range.from + range.durationInFrames && cue.endFrame > range.from));
};

export const parseVoiceManifest = (value: unknown, project: VoiceoverProject): VoiceManifest => {
  if (!value || typeof value !== 'object' || !('tracks' in value) || !Array.isArray(value.tracks) ||
    ('version' in value && value.version !== 1)) throw new Error('配音清单格式不正确');
  const scopes = new Set<string>();
  const ids = new Set<string>();
  const tracks = value.tracks.map((entry: unknown): VoiceTrack => {
    if (!entry || typeof entry !== 'object') throw new Error('配音条目格式不正确');
    const t = entry as Record<string, unknown>;
    if (typeof t.id !== 'string' || !t.id || ids.has(t.id) || !isVoiceScope(t.scope, project) || scopes.has(t.scope) ||
      typeof t.src !== 'string' || !t.src || typeof t.recordedAt !== 'string' ||
      !Number.isInteger(t.startFrame) || !Number.isInteger(t.durationInFrames) || Number(t.durationInFrames) < 1) {
      throw new Error('配音条目包含无效文件、时间或重复录制范围');
    }
    const range = getVoiceRange(t.scope, project);
    if (Number(t.startFrame) < range.from || Number(t.startFrame) + Number(t.durationInFrames) > range.from + range.durationInFrames) {
      throw new Error('配音条目超出所选录制范围');
    }
    ids.add(t.id); scopes.add(t.scope);
    return {...t} as VoiceTrack;
  });
  return {version: 1, tracks};
};

/** A scene retake replaces its entire slot; a short retake leaves silence there. */
export const resolveVoiceSegments = (tracks: readonly VoiceTrack[], project: VoiceoverProject): VoiceSegment[] => {
  const full = tracks.find(track => track.scope === 'full');
  const overrides = (project.scenes ?? []).flatMap(scene => {
    const track = tracks.find(item => item.scope === scene.id);
    return track ? [{scene, track}] : [];
  });
  const boundaries = [...new Set([0, project.durationInFrames,
    ...overrides.flatMap(({scene}) => [scene.from, scene.from + scene.durationInFrames])])].sort((a, b) => a - b);
  const result: VoiceSegment[] = [];
  for (let i = 0; i < boundaries.length - 1; i++) {
    const start = boundaries[i], stop = boundaries[i + 1];
    const take = overrides.find(({scene}) => start >= scene.from && start < scene.from + scene.durationInFrames)?.track ?? full;
    if (!take) continue;
    const from = Math.max(start, take.startFrame);
    const end = Math.min(stop, take.startFrame + take.durationInFrames);
    if (end <= from) continue;
    const piece = {...take, from, duration: end - from, trimBefore: from - take.startFrame};
    const previous = result.at(-1);
    if (previous && previous.id === piece.id && previous.from + previous.duration === piece.from &&
      previous.trimBefore + previous.duration === piece.trimBefore) previous.duration += piece.duration;
    else result.push(piece);
  }
  return result;
};

export const voiceCoverage = (tracks: readonly VoiceTrack[], project: VoiceoverProject) => {
  const scenes = (project.scenes ?? []).filter(scene => scene.recordable !== false);
  const segments = resolveVoiceSegments(tracks, project);
  if (!scenes.length) return segments.length ? 1 : 0;
  return scenes.filter(scene => segments.some(segment => segment.from < scene.from + scene.durationInFrames &&
    segment.from + segment.duration > scene.from)).length;
};

export const voiceSeconds = (track: VoiceTrack, project: VoiceoverProject) => (track.durationInFrames / project.fps).toFixed(1);
export const voiceDurationLabel = (frames: number, fps: number) => {
  const seconds = frames / fps;
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round((seconds - minutes * 60) * 10) / 10;
  return minutes ? `${minutes} 分 ${remainder} 秒` : `${remainder} 秒`;
};

export const previewVoiceTracks = (manifest: VoiceManifest, draft: VoiceTrack | null) =>
  draft ? draft.scope === 'full' ? [draft] : [...manifest.tracks.filter(track => track.scope !== draft.scope), draft] : manifest.tracks;

/** Continuous ducking intervals avoid music bumps at scene cuts. */
export const voiceoverVolume = (frame: number, tracks: readonly VoiceTrack[], project: VoiceoverProject,
  options: {normal?: number; ducked?: number; fadeFrames?: number} = {}) => {
  const intervals = resolveVoiceSegments(tracks, project).reduce<{start: number; end: number}[]>((all, segment) => {
    const previous = all.at(-1);
    if (previous && previous.end >= segment.from) previous.end = Math.max(previous.end, segment.from + segment.duration);
    else all.push({start: segment.from, end: segment.from + segment.duration});
    return all;
  }, []);
  const fade = options.fadeFrames ?? Math.max(1, Math.round(project.fps * .2));
  const smooth = (value: number) => {const t = Math.min(1, Math.max(0, value)); return t * t * (3 - 2 * t);};
  const amount = Math.max(0, ...intervals.map(interval => fade > 0
    ? smooth((frame - interval.start + fade) / (2 * fade)) * (1 - smooth((frame - interval.end + fade) / (2 * fade)))
    : Number(frame >= interval.start && frame < interval.end)));
  const normal = options.normal ?? .75, ducked = options.ducked ?? .2;
  return normal + (ducked - normal) * amount;
};
