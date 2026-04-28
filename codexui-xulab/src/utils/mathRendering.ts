import katex from 'katex'

export type InlineMathSegment =
  | { kind: 'text'; value: string }
  | { kind: 'math'; value: string; displayMode: boolean }

const MATH_TOKEN_PATTERN = /\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|\\\$\$[\s\S]+?\\\$\$|\\\$[^$\n]+?\\\$|\$\$[\s\S]+?\$\$|\$[^$\n]+\$/gu

function escapeMathHtml(value: string): string {
  return value
    .replace(/&/gu, '&amp;')
    .replace(/</gu, '&lt;')
    .replace(/>/gu, '&gt;')
    .replace(/"/gu, '&quot;')
    .replace(/'/gu, '&#39;')
}

function parseMathToken(token: string): { value: string; displayMode: boolean } | null {
  if (token.startsWith('\\[') && token.endsWith('\\]')) {
    const value = token.slice(2, -2).trim()
    return value ? { value, displayMode: true } : null
  }
  if (token.startsWith('\\(') && token.endsWith('\\)')) {
    const value = token.slice(2, -2).trim()
    return value ? { value, displayMode: false } : null
  }
  if (token.startsWith('\\$$') && token.endsWith('\\$$')) {
    const value = token.slice(3, -3).trim()
    return value ? { value, displayMode: true } : null
  }
  if (token.startsWith('\\$') && token.endsWith('\\$')) {
    const value = token.slice(2, -2).trim()
    return value ? { value, displayMode: false } : null
  }
  if (token.startsWith('$$') && token.endsWith('$$')) {
    const value = token.slice(2, -2).trim()
    return value ? { value, displayMode: true } : null
  }
  if (token.startsWith('$') && token.endsWith('$')) {
    const value = token.slice(1, -1).trim()
    return value ? { value, displayMode: false } : null
  }
  return null
}

function looksLikeMathContent(value: string, displayMode: boolean): boolean {
  const normalized = value.trim()
  if (!normalized) return false
  if (displayMode) return true
  if (/\\[A-Za-z]+/u.test(normalized)) return true
  if (/[=<>_^{}]/u.test(normalized)) return true
  if (!/\s/u.test(normalized) && /^[A-Za-z0-9.,+\-*/()[\]|]+$/u.test(normalized)) {
    return true
  }
  return false
}

function pushTextSegment(segments: InlineMathSegment[], value: string): void {
  if (!value) return
  const previous = segments.at(-1)
  if (previous?.kind === 'text') {
    previous.value += value
    return
  }
  segments.push({ kind: 'text', value })
}

export function splitTextByMathSegments(text: string): InlineMathSegment[] {
  const segments: InlineMathSegment[] = []
  let cursor = 0

  for (const match of text.matchAll(MATH_TOKEN_PATTERN)) {
    if (typeof match.index !== 'number') continue
    const parsed = parseMathToken(match[0])
    if (!parsed || !looksLikeMathContent(parsed.value, parsed.displayMode)) {
      continue
    }

    const start = match.index
    const end = start + match[0].length
    if (start > cursor) {
      pushTextSegment(segments, text.slice(cursor, start))
    }
    segments.push({
      kind: 'math',
      value: parsed.value,
      displayMode: parsed.displayMode,
    })
    cursor = end
  }

  if (cursor < text.length) {
    pushTextSegment(segments, text.slice(cursor))
  }

  return segments
}

export function renderMathToHtml(value: string, displayMode = false): string {
  try {
    return katex.renderToString(value, {
      displayMode,
      output: 'html',
      throwOnError: false,
      strict: 'ignore',
      trust: false,
    })
  } catch {
    const escaped = escapeMathHtml(value)
    return displayMode
      ? `<span class="math-render-fallback math-render-fallback-display">${escaped}</span>`
      : `<span class="math-render-fallback">${escaped}</span>`
  }
}
