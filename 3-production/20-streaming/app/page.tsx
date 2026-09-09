'use client';

// 調査依頼を送り、SSE のステージ進捗と最終レポートを表示する画面（提供コード）。
// ハンズオン対象はサーバ側の app/api/invoke/route.ts。
import { useState } from 'react';

interface StreamEvent {
  event: 'stage' | 'result' | 'error';
  stage?: string;
  report?: string;
  detail?: string;
  review?: { verdict: string };
}

const STAGE_LABELS: Record<string, string> = {
  research: '調査中…',
  review: '検証中…',
  revise: '指摘を反映中…',
};

export default function Home() {
  const [prompt, setPrompt] = useState('Acme と Globex の pricing と feature を比較して');
  const [stages, setStages] = useState<string[]>([]);
  const [report, setReport] = useState('');
  const [error, setError] = useState('');
  const [running, setRunning] = useState(false);

  async function run() {
    setStages([]);
    setReport('');
    setError('');
    setRunning(true);
    try {
      const res = await fetch('/api/invoke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, stream: true }),
      });
      if (!res.ok || !res.body) {
        setError(`HTTP ${res.status}: ${await res.text()}`);
        return;
      }

      // SSE (`data: {...}` 行) と素の JSON の両方を受けられる簡易パーサ
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let index: number;
        while ((index = buffer.indexOf('\n')) >= 0) {
          const line = buffer.slice(0, index).trim();
          buffer = buffer.slice(index + 1);
          if (!line) continue;
          const json = line.startsWith('data:') ? line.slice(5).trim() : line;
          handleEvent(json);
        }
      }
      if (buffer.trim()) handleEvent(buffer.trim());
    } finally {
      setRunning(false);
    }
  }

  function handleEvent(json: string) {
    let parsed: StreamEvent;
    try {
      parsed = JSON.parse(json) as StreamEvent;
    } catch {
      return; // ハートビート等の非 JSON 行は無視
    }
    if (parsed.event === 'stage' && parsed.stage) {
      setStages((prev) => [...prev, STAGE_LABELS[parsed.stage!] ?? parsed.stage!]);
    } else if (parsed.event === 'error') {
      setError(parsed.detail ?? 'unknown error');
    } else if (parsed.report) {
      setReport(parsed.report);
    }
  }

  return (
    <main>
      <h1>競合リサーチエージェント</h1>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={3}
        style={{ width: '100%' }}
      />
      <button onClick={run} disabled={running} style={{ marginTop: 8 }}>
        {running ? '実行中…' : '調査する'}
      </button>

      <ol>
        {stages.map((stage, i) => (
          <li key={i}>{stage}</li>
        ))}
      </ol>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {report && <pre style={{ whiteSpace: 'pre-wrap', background: '#f6f6f6', padding: 12 }}>{report}</pre>}
    </main>
  );
}
