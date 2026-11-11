import {defineVoiceoverProject} from '../src/core/index.js';

// A different film: 60 fps, eight seconds, arbitrary scene IDs, optional captions.
export const exampleProject = defineVoiceoverProject({
  fps: 60,
  durationInFrames: 480,
  scenes: [
    {id: 'opening', title: '开场', from: 0, durationInFrames: 180},
    {id: 'conclusion', title: '结尾', from: 180, durationInFrames: 300},
  ],
  captions: [
    {startFrame: 0, endFrame: 170, text: '这是一个独立的接入示例。', sceneId: 'opening'},
    {startFrame: 180, endFrame: 470, text: '分镜编号和帧率由你的工程决定。', sceneId: 'conclusion'},
  ],
});

export const fullFilmOnlyProject = defineVoiceoverProject({fps: 24, durationInFrames: 240});
