import React from 'react';

/** 简易 Markdown 渲染器（不依赖外部库） */
export function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split('\n');
  const nodes: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBuffer: string[] = [];
  let codeLang = '';

  const flushCode = () => {
    if (codeBuffer.length > 0) {
      nodes.push(
        <pre key={`code-${nodes.length}`} style={{
          background: '#f5f5f5',
          padding: 12,
          borderRadius: 8,
          fontSize: 13,
          lineHeight: 1.6,
          overflowX: 'auto',
          border: '1px solid #e8e8e8',
          fontFamily: "'SF Mono', 'Fira Code', monospace",
        }}>
          <code>{codeBuffer.join('\n')}</code>
        </pre>
      );
      codeBuffer = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith('```')) {
      if (inCodeBlock) {
        flushCode();
        inCodeBlock = false;
        codeLang = '';
      } else {
        flushCode();
        inCodeBlock = true;
        codeLang = line.slice(3).trim();
      }
      continue;
    }
    if (inCodeBlock) {
      codeBuffer.push(line);
      continue;
    }

    if (line.trim() === '') {
      nodes.push(<div key={`br-${nodes.length}`} style={{ height: 8 }} />);
      continue;
    }

    if (/^[-*_]{3,}$/.test(line.trim())) {
      nodes.push(<hr key={`hr-${nodes.length}`} style={{ border: 'none', borderTop: '1px solid #e8e8e8', margin: '12px 0' }} />);
      continue;
    }

    const hMatch = line.match(/^(#{1,4})\s+(.+)/);
    if (hMatch) {
      const level = hMatch[1].length;
      const content = inlineFormat(hMatch[2]);
      const size = level === 1 ? 20 : level === 2 ? 17 : level === 3 ? 15 : 14;
      nodes.push(
        <div key={`h-${nodes.length}`} style={{
          fontSize: size,
          fontWeight: 600,
          marginTop: level <= 2 ? 20 : 12,
          marginBottom: 8,
          color: '#1a1a2e',
        }}>
          {content}
        </div>
      );
      continue;
    }

    if (line.startsWith('> ')) {
      nodes.push(
        <blockquote key={`bq-${nodes.length}`} style={{
          borderLeft: '3px solid #f5642a',
          margin: '8px 0',
          padding: '6px 12px',
          background: '#fafafa',
          borderRadius: '0 6px 6px 0',
          color: '#475569',
          fontSize: 13,
        }}>
          {inlineFormat(line.slice(2))}
        </blockquote>
      );
      continue;
    }

    const ulMatch = line.match(/^[-*+]\s+(.+)/);
    if (ulMatch) {
      nodes.push(
        <div key={`li-${nodes.length}`} style={{ display: 'flex', gap: 8, padding: '2px 0', fontSize: 14, lineHeight: 1.6 }}>
          <span style={{ color: '#f5642a' }}>•</span>
          <span>{inlineFormat(ulMatch[1])}</span>
        </div>
      );
      continue;
    }

    const olMatch = line.match(/^\d+[.)]\s+(.+)/);
    if (olMatch) {
      nodes.push(
        <div key={`li-${nodes.length}`} style={{ display: 'flex', gap: 8, padding: '2px 0', fontSize: 14, lineHeight: 1.6 }}>
          <span style={{ color: '#94a3b8', minWidth: 20, textAlign: 'right' }}>
            {line.match(/^\d+/)?.[0]}.
          </span>
          <span>{inlineFormat(olMatch[1])}</span>
        </div>
      );
      continue;
    }

    nodes.push(
      <div key={`p-${nodes.length}`} style={{ fontSize: 14, lineHeight: 1.7, margin: '4px 0' }}>
        {inlineFormat(line)}
      </div>
    );
  }

  flushCode();
  return nodes;
}

/** 行内格式：粗体、斜体、行内代码、链接 */
function inlineFormat(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    const codeMatch = remaining.match(/`([^`]+)`/);
    if (codeMatch && codeMatch.index !== undefined) {
      if (codeMatch.index > 0) parts.push(remaining.slice(0, codeMatch.index));
      parts.push(
        <code key={`c-${key++}`} style={{
          background: '#f0f0f0',
          padding: '1px 5px',
          borderRadius: 4,
          fontSize: 13,
          fontFamily: "'SF Mono', monospace",
          color: '#e11d48',
        }}>
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.slice(codeMatch.index + codeMatch[0].length);
      continue;
    }

    const biMatch = remaining.match(/\*\*\*(.+?)\*\*\*/);
    if (biMatch && biMatch.index !== undefined) {
      if (biMatch.index > 0) parts.push(remaining.slice(0, biMatch.index));
      parts.push(<strong key={`b-${key++}`} style={{ fontWeight: 700, fontStyle: 'italic' }}>{biMatch[1]}</strong>);
      remaining = remaining.slice(biMatch.index + biMatch[0].length);
      continue;
    }

    const bMatch = remaining.match(/\*\*(.+?)\*\*/);
    if (bMatch && bMatch.index !== undefined) {
      if (bMatch.index > 0) parts.push(remaining.slice(0, bMatch.index));
      parts.push(<strong key={`b-${key++}`} style={{ fontWeight: 700 }}>{bMatch[1]}</strong>);
      remaining = remaining.slice(bMatch.index + bMatch[0].length);
      continue;
    }

    const iMatch = remaining.match(/\*(.+?)\*/);
    if (iMatch && iMatch.index !== undefined) {
      if (iMatch.index > 0) parts.push(remaining.slice(0, iMatch.index));
      parts.push(<em key={`i-${key++}`} style={{ fontStyle: 'italic' }}>{iMatch[1]}</em>);
      remaining = remaining.slice(iMatch.index + iMatch[0].length);
      continue;
    }

    parts.push(remaining);
    break;
  }

  return <>{parts}</>;
}
