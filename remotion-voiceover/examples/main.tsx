import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import {ExamplePreview} from './integration.js';
import {exampleProject} from './project.js';
import '../src/react/voice.css';
import './example.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <main className="example-page">
      <header className="example-header">
        <p className="example-brand">REMOTION VOICEOVER</p>
        <h1>跟着画面，录下你的声音</h1>
        <p>用这段 {exampleProject.durationInFrames / exampleProject.fps} 秒的短片试试配音。可以录制整片，也可以选择一段单独录制。</p>
      </header>
      <ol className="example-steps" aria-label="配音步骤">
        <li>选择录制范围</li>
        <li>允许麦克风并开始录音</li>
        <li>跟画面试听</li>
        <li>保存并使用</li>
      </ol>
      <ExamplePreview />
      <p className="example-note">录制前会倒计时 3 秒。录音后可反复试听、重新录制，或下载 WAV。</p>
    </main>
  </StrictMode>,
);
