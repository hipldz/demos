export const recorderMimeType = () => [
  'audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus',
].find(type => MediaRecorder.isTypeSupported(type));

export const encodeMonoWave = (buffer: AudioBuffer, maxSeconds: number) => {
  const count = Math.min(buffer.length, Math.floor(maxSeconds * buffer.sampleRate));
  const data = new ArrayBuffer(44 + count * 2);
  const view = new DataView(data);
  const text = (at: number, value: string) => [...value].forEach((char, i) => view.setUint8(at + i, char.charCodeAt(0)));
  text(0, 'RIFF'); view.setUint32(4, data.byteLength - 8, true); text(8, 'WAVE'); text(12, 'fmt ');
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, buffer.sampleRate, true); view.setUint32(28, buffer.sampleRate * 2, true);
  view.setUint16(32, 2, true); view.setUint16(34, 16, true); text(36, 'data'); view.setUint32(40, count * 2, true);
  const channels = Array.from({length: buffer.numberOfChannels}, (_, i) => buffer.getChannelData(i));
  for (let i = 0; i < count; i++) {
    let sample = 0;
    for (const channel of channels) sample += channel[i] / channels.length;
    sample = Math.max(-1, Math.min(1, sample));
    view.setInt16(44 + i * 2, Math.round(sample * (sample < 0 ? 32768 : 32767)), true);
  }
  return {blob: new Blob([data], {type: 'audio/wav'}), seconds: count / buffer.sampleRate};
};

export const recordingToWave = async (blob: Blob, maxSeconds: number) => {
  const context = new AudioContext({sampleRate: 48000});
  try {return encodeMonoWave(await context.decodeAudioData(await blob.arrayBuffer()), maxSeconds);}
  finally {await context.close();}
};

export const microphoneError = (error: unknown) => {
  if (error instanceof DOMException) {
    if (error.name === 'NotAllowedError') return '麦克风权限未开启。请在地址栏允许麦克风，然后重新录制。';
    if (error.name === 'NotFoundError') return '没有找到麦克风，请连接或启用麦克风后重试。';
    if (error.name === 'NotReadableError') return '麦克风暂时无法使用，请检查是否被其他程序占用。';
  }
  return error instanceof Error ? error.message : '录音失败，请重新试一次。';
};
