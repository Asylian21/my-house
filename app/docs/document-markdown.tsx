'use client';

import { Fragment, type ReactNode } from 'react';
import type { LibraryDocument } from '@/lib/document-library';

type MarkdownContext = {
  documents: LibraryDocument[];
  onOpenDocument: (id: string) => void;
};

type Props = MarkdownContext & { content: string };

const hasControlCharacter = (value: string) => Array.from(value).some(character => character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127);

function localDocument(target: string, documents: LibraryDocument[]) {
  if (!target || target.startsWith('#') || /^[a-z][a-z\d+.-]*:/i.test(target) || target.startsWith('//')) return undefined;
  let path: string;
  try { path = decodeURIComponent(target.split(/[?#]/, 1)[0]); } catch { return undefined; }
  if (hasControlCharacter(path) || path.includes('\\') || path.split('/').includes('..')) return undefined;
  const filename = path.split('/').at(-1)?.replace(/:\d+(?::\d+)?$/, '');
  const matches = documents.filter(document => document.webUrl === path || document.filename === filename);
  return matches.length === 1 ? matches[0] : undefined;
}

function link(label: ReactNode, target: string, context: MarkdownContext) {
  const document = localDocument(target, context.documents);
  if (document) return <button type="button" className="dl-markdown-link" onClick={() => context.onOpenDocument(document.id)}>{label}</button>;
  if (/^https?:\/\//i.test(target) && !hasControlCharacter(target)) {
    try {
      const url = new URL(target);
      if (url.protocol === 'https:' || url.protocol === 'http:') return <a href={url.href} target="_blank" rel="noopener noreferrer">{label}</a>;
    } catch { /* A malformed destination remains readable text. */ }
  }
  return label;
}

function closing(text: string, start: number, open: string, close: string) {
  let depth = 1;
  for (let i = start; i < text.length; i++) {
    if (text[i] === '\\') { i++; continue; }
    if (text[i] === open) depth++;
    if (text[i] === close && --depth === 0) return i;
  }
  return -1;
}

function destination(value: string) {
  const trimmed = value.trim();
  if (trimmed.startsWith('<')) {
    const end = trimmed.indexOf('>');
    return end >= 0 ? trimmed.slice(1, end) : '';
  }
  return trimmed.replace(/\s+["'][^"']*["']\s*$/, '').replace(/\\([()\\])/g, '$1');
}

function inline(text: string, context: MarkdownContext, depth = 0, allowLinks = true): ReactNode[] {
  if (depth > 8) return [text];
  const result: ReactNode[] = [];
  let plain = '';
  const add = (node: ReactNode) => {
    if (plain) { result.push(plain); plain = ''; }
    result.push(<Fragment key={result.length}>{node}</Fragment>);
  };
  for (let i = 0; i < text.length;) {
    const char = text[i];
    if (char === '\\' && /[\\`*_{}[\]()#+.!|>~-]/.test(text[i + 1] ?? '')) {
      plain += text[i + 1]; i += 2; continue;
    }
    if (char === '`') {
      const marker = text.slice(i).match(/^`+/)![0];
      const end = text.indexOf(marker, i + marker.length);
      if (end >= 0) {
        add(<code>{text.slice(i + marker.length, end).replace(/\n/g, ' ')}</code>);
        i = end + marker.length; continue;
      }
    }
    if (allowLinks && (char === '[' || (char === '!' && text[i + 1] === '['))) {
      const image = char === '!';
      const labelStart = i + (image ? 2 : 1);
      const labelEnd = closing(text, labelStart, '[', ']');
      if (labelEnd >= 0 && text[labelEnd + 1] === '(') {
        const targetEnd = closing(text, labelEnd + 2, '(', ')');
        if (targetEnd >= 0) {
          const label = inline(text.slice(labelStart, labelEnd), context, depth + 1, false);
          add(image ? label : link(label, destination(text.slice(labelEnd + 2, targetEnd)), context));
          i = targetEnd + 1; continue;
        }
      }
    }
    if (allowLinks && char === '<') {
      const end = text.indexOf('>', i + 1);
      if (end >= 0 && /^https?:\/\//i.test(text.slice(i + 1, end))) {
        const target = text.slice(i + 1, end);
        add(link(target, target, context)); i = end + 1; continue;
      }
    }
    if ((char === '*' || char === '_') && !/\s/.test(text[i + 1] ?? ' ') && !(char === '_' && /[\p{L}\p{N}]/u.test(text[i - 1] ?? ''))) {
      const marker = text[i + 1] === char ? char + char : char;
      let end = text.indexOf(marker, i + marker.length);
      while (end >= 0 && (text[end - 1] === '\\' || /\s/.test(text[end - 1]))) end = text.indexOf(marker, end + marker.length);
      if (end > i + marker.length) {
        const body = inline(text.slice(i + marker.length, end), context, depth + 1, allowLinks);
        add(marker.length === 2 ? <strong>{body}</strong> : <em>{body}</em>);
        i = end + marker.length; continue;
      }
    }
    plain += char; i++;
  }
  if (plain) result.push(plain);
  return result;
}

function cells(line: string) {
  const value = line.trim().replace(/^\|/, '').replace(/(?<!\\)\|\s*$/, '');
  const parts: string[] = [];
  let cell = '', codeMarker = 0;
  for (let i = 0; i < value.length; i++) {
    if (value[i] === '\\' && value[i + 1] === '|') { cell += '\\|'; i++; continue; }
    if (value[i] === '`') {
      const run = value.slice(i).match(/^`+/)![0];
      if (!codeMarker) codeMarker = run.length;
      else if (codeMarker === run.length) codeMarker = 0;
      cell += run; i += run.length - 1; continue;
    }
    if (value[i] === '|' && !codeMarker) { parts.push(cell.trim()); cell = ''; }
    else cell += value[i];
  }
  parts.push(cell.trim());
  return parts;
}

const listItem = (line: string) => line.match(/^( {0,3})([-+*]|\d+[.)])\s+(.*)$/);
const fence = (line: string) => line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
const heading = (line: string) => line.match(/^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
const rule = (line: string) => /^ {0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$/.test(line);
const tableDivider = (line: string) => line.includes('|') && cells(line).every(cell => /^:?-{3,}:?$/.test(cell));
const startsBlock = (lines: string[], i: number) => !lines[i]?.trim() || Boolean(fence(lines[i]) || heading(lines[i]) || rule(lines[i]) || listItem(lines[i]) || /^ {0,3}>/.test(lines[i]) || (lines[i].includes('|') && tableDivider(lines[i + 1] ?? '')));

function blocks(lines: string[], context: MarkdownContext, depth = 0): ReactNode[] {
  if (depth > 8) return [<p key="text">{lines.join('\n')}</p>];
  const result: ReactNode[] = [];
  for (let i = 0; i < lines.length;) {
    if (!lines[i].trim()) { i++; continue; }
    const key = i;
    const code = fence(lines[i]);
    if (code) {
      const marker = code[1], content: string[] = [];
      i++;
      while (i < lines.length && !new RegExp(`^ {0,3}${marker[0]}{${marker.length},}\\s*$`).test(lines[i])) content.push(lines[i++]);
      if (i < lines.length) i++;
      result.push(<pre key={key} className="dl-markdown-code" style={{ maxWidth: '100%', overflowX: 'auto' }}><code>{content.join('\n')}</code></pre>);
      continue;
    }
    const title = heading(lines[i]);
    if (title) {
      const Heading = `h${title[1].length}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
      result.push(<Heading key={key}>{inline(title[2], context)}</Heading>); i++; continue;
    }
    if (rule(lines[i])) { result.push(<hr key={key}/>); i++; continue; }
    if (lines[i].includes('|') && tableDivider(lines[i + 1] ?? '')) {
      const headers = cells(lines[i]);
      const alignments = cells(lines[i + 1]).map((cell): 'center' | 'left' | 'right' | undefined => cell.startsWith(':') ? (cell.endsWith(':') ? 'center' : 'left') : cell.endsWith(':') ? 'right' : undefined);
      const rows: string[][] = [];
      i += 2;
      while (i < lines.length && lines[i].trim() && lines[i].includes('|') && !fence(lines[i]) && !heading(lines[i])) rows.push(cells(lines[i++]));
      // A scrollable table region needs keyboard focus for horizontal scrolling.
      // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex
      result.push(<div key={key} className="dl-markdown-table" role="region" aria-label="Tabuľka v dokumente" tabIndex={0} style={{ maxWidth: '100%', overflowX: 'auto' }}><table><thead><tr>{headers.map((cell, index) => <th key={index} scope="col" style={{ textAlign: alignments[index] }}>{inline(cell, context)}</th>)}</tr></thead><tbody>{rows.map((row, rowIndex) => <tr key={rowIndex}>{headers.map((_, index) => <td key={index} style={{ textAlign: alignments[index] }}>{inline(row[index] ?? '', context)}</td>)}</tr>)}</tbody></table></div>);
      continue;
    }
    if (/^ {0,3}>/.test(lines[i])) {
      const quoted: string[] = [];
      while (i < lines.length && /^ {0,3}>/.test(lines[i])) quoted.push(lines[i++].replace(/^ {0,3}> ?/, ''));
      result.push(<blockquote key={key}>{blocks(quoted, context, depth + 1)}</blockquote>); continue;
    }
    const item = listItem(lines[i]);
    if (item) {
      const ordered = /^\d/.test(item[2]), indent = item[1].length;
      const items: ReactNode[] = [];
      while (i < lines.length) {
        const next = listItem(lines[i]);
        if (!next || next[1].length !== indent || /^\d/.test(next[2]) !== ordered) break;
        const itemKey = i, body = [next[3]], contentIndent = next[0].length - next[3].length;
        i++;
        while (i < lines.length) {
          if (!lines[i].trim()) {
            let nextNonempty = i + 1;
            while (nextNonempty < lines.length && !lines[nextNonempty].trim()) nextNonempty++;
            if (nextNonempty === lines.length || !lines[nextNonempty].startsWith(' '.repeat(indent + 1))) break;
            body.push(''); i++; continue;
          }
          const following = listItem(lines[i]);
          if (following && following[1].length <= indent) break;
          if (lines[i].startsWith(' '.repeat(indent + 1))) {
            body.push(lines[i].slice(Math.min(contentIndent, lines[i].search(/\S/)))); i++; continue;
          }
          if (startsBlock(lines, i)) break;
          body.push(lines[i++]);
        }
        items.push(<li key={itemKey}>{blocks(body, context, depth + 1)}</li>);
        let after = i;
        while (after < lines.length && !lines[after].trim()) after++;
        const sibling = listItem(lines[after] ?? '');
        if (sibling && sibling[1].length === indent && /^\d/.test(sibling[2]) === ordered) i = after;
        else break;
      }
      result.push(ordered ? <ol key={key} start={parseInt(item[2], 10)}>{items}</ol> : <ul key={key}>{items}</ul>);
      continue;
    }
    const paragraph = [lines[i++]];
    while (i < lines.length && !startsBlock(lines, i)) paragraph.push(lines[i++]);
    result.push(<p key={key}>{inline(paragraph.join('\n'), context)}</p>);
  }
  return result;
}

/** Deliberate Markdown subset: source text is always rendered through React, never as HTML. */
export function DocumentMarkdown({ content, documents, onOpenDocument }: Props) {
  const lines = content.replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n').replace(/\t/g, '    ').split('\n');
  return <article className="dl-markdown" style={{ minWidth: 0, overflowWrap: 'anywhere' }}>{blocks(lines, { documents, onOpenDocument })}</article>;
}
