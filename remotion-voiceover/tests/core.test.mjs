import test from 'node:test';
import assert from 'node:assert/strict';
import {defineVoiceoverProject, getVoiceCaptions, parseVoiceManifest, previewVoiceTracks,
  resolveVoiceSegments, voiceCoverage, voiceoverVolume, voiceSeconds} from '../dist/core/index.js';

const track = (scope, startFrame, durationInFrames, id = scope) =>
  ({id, scope, startFrame, durationInFrames, src: `narration/${id}.wav`, recordedAt: '2026-11-09'});

test('a project without scenes can record and play a continuous full-film voice', () => {
  const project = defineVoiceoverProject({fps: 24, durationInFrames: 240});
  const full = track('full', 0, 240);
  assert.deepEqual(resolveVoiceSegments([full], project), [{...full, from: 0, duration: 240, trimBefore: 0}]);
  assert.equal(voiceSeconds(full, project), '10.0');
  assert.equal(voiceCoverage([full], project), 1);
  assert.equal(voiceCoverage([], project), 0);
  assert.equal(parseVoiceManifest({version: 1, tracks: [full]}, project).tracks.length, 1);
});

for (const fps of [24, 30, 60, 29.97]) {
  test(`a short scene retake replaces the entire slot at ${fps} fps, preserving full source offsets`, () => {
    const second = Math.round(fps);
    const project = defineVoiceoverProject({fps, durationInFrames: second * 6, scenes: [
      {id: '开场', title: '开场', from: 0, durationInFrames: second},
      {id: 'chapter/b', title: '其他编号', from: second * 2, durationInFrames: second * 2},
    ]});
    const full = track('full', 0, second * 6);
    const retake = track('chapter/b', second * 2, Math.floor(second / 2), 'retake');
    const segments = resolveVoiceSegments([full, retake], project);
    assert.deepEqual(segments.map(item => [item.id, item.from, item.duration, item.trimBefore]), [
      ['full', 0, second * 2, 0],
      ['retake', second * 2, Math.floor(second / 2), 0],
      ['full', second * 4, second * 2, second * 4],
    ]);
    assert.equal(resolveVoiceSegments([full], project).length, 1, 'Scene gaps must not remove full-film narration');
    for (let i = 1; i < segments.length; i++) assert.ok(segments[i].from >= segments[i - 1].from + segments[i - 1].duration);
    parseVoiceManifest({version: 1, tracks: [full, retake]}, project);
  });
}

test('configuration validates frame bounds, overlaps, reserved IDs, and public paths', () => {
  assert.throws(() => defineVoiceoverProject({fps: 0, durationInFrames: 60}));
  assert.throws(() => defineVoiceoverProject({fps: 30, durationInFrames: 1.5}));
  assert.throws(() => defineVoiceoverProject({fps: 30, durationInFrames: 60, manifestSrc: '../outside.json'}));
  assert.throws(() => defineVoiceoverProject({fps: 30, durationInFrames: 60, scenes: [{id: 'full', title: 'bad', from: 0, durationInFrames: 60}]}));
  assert.throws(() => defineVoiceoverProject({fps: 30, durationInFrames: 60, scenes: [
    {id: 'a', title: 'a', from: 0, durationInFrames: 40}, {id: 'b', title: 'b', from: 30, durationInFrames: 30},
  ]}));
});

test('legacy version 1 manifests stay readable; duplicate or out-of-slot takes are rejected', () => {
  const project = defineVoiceoverProject({fps: 30, durationInFrames: 120, scenes: [{id: 'S02', title: 'existing', from: 30, durationInFrames: 60}]});
  const old = track('S02', 30, 45, 'S02-older-uuid');
  assert.deepEqual(parseVoiceManifest({version: 1, tracks: [old]}, project).tracks, [old]);
  assert.throws(() => parseVoiceManifest({version: 2, tracks: [old]}, project));
  assert.throws(() => parseVoiceManifest({tracks: [old, {...old, id: 'another'}]}, project));
  assert.throws(() => parseVoiceManifest({tracks: [{...old, startFrame: 0}]}, project));
  assert.throws(() => parseVoiceManifest({tracks: [{...old, durationInFrames: 100}]}, project));
});

test('optional subtitles are selected by scene ID or intersecting absolute time', () => {
  const project = defineVoiceoverProject({fps: 60, durationInFrames: 180, scenes: [
    {id: 'a', title: 'a', from: 0, durationInFrames: 90}, {id: 'b', title: 'b', from: 90, durationInFrames: 90},
  ], captions: [
    {startFrame: 10, endFrame: 70, text: 'first'},
    {startFrame: 100, endFrame: 150, text: 'second', sceneId: 'b'},
  ]});
  assert.deepEqual(getVoiceCaptions('a', project).map(cue => cue.text), ['first']);
  assert.deepEqual(getVoiceCaptions('b', project).map(cue => cue.text), ['second']);
  assert.equal(getVoiceCaptions('full', project).length, 2);
});

test('draft audition overlays only its scope and leaves the saved manifest untouched', () => {
  const full = track('full', 0, 120), scene = track('a', 30, 30), draft = {...scene, id: 'draft', src: 'blob:local'};
  const manifest = {version: 1, tracks: [full, scene]};
  assert.deepEqual(previewVoiceTracks(manifest, draft), [full, draft]);
  assert.deepEqual(previewVoiceTracks(manifest, {...full, id: 'draft'}), [{...full, id: 'draft'}]);
  assert.deepEqual(manifest.tracks, [full, scene]);
});

test('music stays ducked across adjacent takes and returns to normal in silent retake gaps', () => {
  const project = defineVoiceoverProject({fps: 60, durationInFrames: 360, scenes: [{id: 'middle', title: 'middle', from: 120, durationInFrames: 120}]});
  const full = track('full', 0, 360), complete = track('middle', 120, 120);
  for (const frame of [110, 119, 120, 121, 239, 240, 250]) assert.ok(Math.abs(voiceoverVolume(frame, [full, complete], project) - .2) < 1e-9);
  assert.equal(voiceoverVolume(200, [full, {...complete, durationInFrames: 30}], project), .75);
  assert.equal(voiceoverVolume(0, [], project), .75);
});
