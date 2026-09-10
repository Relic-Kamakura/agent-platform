// blocks.json（check_mermaid.sh が生成）の各ブロックを mermaid.parse に通す。
// jsdom で DOM を用意するのは、flowchart の解析が DOMPurify を要求するため。
import { readFileSync } from 'fs';
import { JSDOM } from 'jsdom';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { pretendToBeVisual: true });
global.window = dom.window;
global.document = dom.window.document;
Object.defineProperty(global, 'navigator', { value: dom.window.navigator, configurable: true });
for (const name of ['HTMLElement', 'Element', 'SVGElement', 'DOMParser', 'Node', 'NodeFilter']) {
  global[name] = dom.window[name];
}

const blocks = JSON.parse(readFileSync('./blocks.json', 'utf8'));
const mermaid = (await import('mermaid/dist/mermaid.core.mjs')).default;
mermaid.initialize({ startOnLoad: false });

let bad = 0;
for (const b of blocks) {
  try {
    await mermaid.parse(b.text);
    console.log(`OK   ${b.file}:${b.line}`);
  } catch (e) {
    bad++;
    console.log(`NG   ${b.file}:${b.line}  ${String(e.message || e).split('\n').slice(0, 2).join(' / ')}`);
  }
}
console.log(`\nMermaid の解析 NG: ${bad} 件（全 ${blocks.length} ブロック）`);
process.exit(bad ? 1 : 0);
