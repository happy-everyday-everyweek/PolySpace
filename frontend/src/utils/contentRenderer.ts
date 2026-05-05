import MarkdownIt from 'markdown-it'
import katex from 'katex'
import hljs from 'highlight.js'

export interface ContentBlock {
  type: 'text' | 'html' | 'math' | 'card'
  content: string
  cardType?: 'task'
  mathDisplay?: boolean
}

export interface CardData {
  type: 'task'
  [key: string]: unknown
}

const md = new MarkdownIt({
  html: false,
  linkify: true,
  highlight(str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="code-block"><code class="hljs language-${lang}">${hljs.highlight(str, { language: lang }).value}</code></pre>`
      } catch { /* fallback */ }
    }
    return `<pre class="code-block"><code class="hljs">${md.utils.escapeHtml(str)}</code></pre>`
  },
})

function extractHtmlBlocks(content: string): ContentBlock[] {
  const blocks: ContentBlock[] = []
  const htmlCodeRegex = /```html\s*\n([\s\S]*?)```/gi
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = htmlCodeRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      blocks.push(...parseInlineContent(content.slice(lastIndex, match.index)))
    }
    blocks.push({ type: 'html', content: match[1].trim() })
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < content.length) {
    blocks.push(...parseInlineContent(content.slice(lastIndex)))
  }

  return blocks
}

function parseInlineContent(text: string): ContentBlock[] {
  const blocks: ContentBlock[] = []
  const mathRegex = /(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\(.*?\\\))/g
  const cardRegex = /:::card:task\s*\n([\s\S]*?):::/g

  const specialRegex = new RegExp(
    `${cardRegex.source}|${mathRegex.source}`, 'g'
  )

  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = specialRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      blocks.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }

    if (match[1]) {
      blocks.push({
        type: 'card',
        content: match[1].trim(),
        cardType: 'task',
      })
    } else if (match[0]) {
      const mathStr = match[0]
      const isDisplay = mathStr.startsWith('$$') || mathStr.startsWith('\\[')
      const formula = mathStr
        .replace(/^\$\$|\$\$$/g, '')
        .replace(/^\\\[|\\\]$/g, '')
        .replace(/^\\\(|\\\)$/g, '')
        .trim()
      blocks.push({ type: 'math', content: formula, mathDisplay: isDisplay })
    }

    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) {
    blocks.push({ type: 'text', content: text.slice(lastIndex) })
  }

  return blocks
}

export function parseContent(content: string): ContentBlock[] {
  return extractHtmlBlocks(content)
}

export function renderMarkdown(text: string): string {
  return md.render(text)
}

export function renderMath(formula: string, displayMode: boolean): string {
  try {
    return katex.renderToString(formula, {
      displayMode,
      throwOnError: false,
      trust: true,
    })
  } catch {
    return `<span class="math-error">${formula}</span>`
  }
}

export function parseCardData(raw: string): CardData {
  try {
    const data = JSON.parse(raw)
    return { type: 'task', ...data }
  } catch {
    const lines = raw.split('\n').filter(l => l.trim())
    const data: Record<string, string> = { type: 'task' }
    for (const line of lines) {
      const colonIdx = line.indexOf(':')
      if (colonIdx > 0) {
        const key = line.slice(0, colonIdx).trim()
        const val = line.slice(colonIdx + 1).trim()
        data[key] = val
      }
    }
    return data as CardData
  }
}
