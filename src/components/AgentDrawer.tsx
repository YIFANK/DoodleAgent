// ================= app/components/AgentDrawer.tsx =================
'use client'

import { useEffect, useRef, useState } from 'react'
import {
  Tldraw,
  TLOnMountHandler,
  TLShapePartial,
  createShapeId,
} from 'tldraw'
import 'tldraw/tldraw.css'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Loader2, SquarePen } from 'lucide-react'

/**
 * AgentDrawer – fully autonomous doodling component.
 *
 * Behaviour:
 * 1. Immediately calls /api/generate to obtain an initial batch of shapes.
 * 2. Renders shapes to the canvas.
 * 3. Every `cycleMs` milliseconds, sends a snapshot of current shapes back to
 *    /api/generate. The LLM returns *additional* shapes to extend the doodle.
 * 4. Stops when /api/generate returns an empty array.
 */
export default function AgentDrawer({ cycleMs = 4000 }: { cycleMs?: number }) {
  const editorRef = useRef<TLOnMountHandler['editor']>()
  const timerRef = useRef<NodeJS.Timeout>()
  const [running, setRunning] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleMount: TLOnMountHandler = ({ editor }) => {
    editorRef.current = editor
  }

  /** Serialize the minimal shape summary to keep token cost low */
  const getShapeSummary = () => {
    const editor = editorRef.current
    if (!editor) return []
    return editor.getCurrentPageShapes().map((s) => ({
      id: s.id,
      type: s.type,
      x: s.x,
      y: s.y,
      w: 'w' in s.props ? (s.props as any).w : undefined,
      h: 'h' in s.props ? (s.props as any).h : undefined,
      color: (s.props as any).color,
    }))
  }

  /** Calls /api/generate with the current canvas summary */
  const requestLLMShapes = async () => {
    if (!editorRef.current) return

    try {
      setLoading(true)
      setError(null)

      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shapes: getShapeSummary() }),
      })

      if (!res.ok) throw new Error(`LLM request failed: ${res.statusText}`)
      const data = (await res.json()) as { shapes: any[] }

      if (!Array.isArray(data.shapes)) throw new Error('No shapes array in response')
      if (data.shapes.length === 0) {
        // Nothing more to draw – stop the loop
        setRunning(false)
        clearInterval(timerRef.current!)
        return
      }

      const newShapes: TLShapePartial[] = data.shapes.map((s: any) => ({
        id: s.id ?? createShapeId(),
        type: s.type ?? 'rectangle',
        x: s.x ?? 0,
        y: s.y ?? 0,
        props: {
          w: s.w ?? 120,
          h: s.h ?? 80,
          color: s.color ?? 'black',
          dash: s.dash ?? 'solid',
          size: s.size ?? 'm',
          fill: s.fill ?? 'solid',
        },
      }))

      editorRef.current.createShapes(newShapes)
    } catch (err: any) {
      console.error(err)
      setError(err.message)
      setRunning(false)
      clearInterval(timerRef.current!)
    } finally {
      setLoading(false)
    }
  }

  /** Toggle loop */
  const toggleRun = () => {
    if (running) {
      clearInterval(timerRef.current!)
      setRunning(false)
    } else {
      setRunning(true)
      // Kick‑off immediately, then schedule repeatedly
      requestLLMShapes()
      timerRef.current = setInterval(requestLLMShapes, cycleMs)
    }
  }

  // Clean up interval on unmount
  useEffect(() => {
    return () => clearInterval(timerRef.current!)
  }, [])

  return (
    <div className="flex flex-col h-screen w-screen bg-muted">
      <Card className="m-4 w-max shadow-lg">
        <CardContent className="flex items-center gap-4 p-4">
          <Button onClick={toggleRun} disabled={loading} className="font-semibold">
            {running ? 'Stop' : loading ? <Loader2 className="animate-spin" /> : <SquarePen className="mr-1" />}{' '}
            {running ? 'Drawing…' : 'Start Doodle'}
          </Button>
          {error && <p className="text-sm text-red-500 ml-4">{error}</p>}
        </CardContent>
      </Card>

      <Tldraw className="flex-1 rounded-2xl shadow-inner m-4" onMount={handleMount} autoFocus />
    </div>
  )
}

// ================= app/api/generate/route.ts =================
// Next.js (app router) edge‑optimised route that calls OpenAI to generate the
// next batch of shapes. It receives the *current* canvas summary (array of
// shape descriptors) and returns a JSON object `{ shapes: [...] }`.

import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

export const runtime = 'edge'

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

const SYSTEM_PROMPT = `You are an autonomous doodle agent working on an infinite canvas.
Your goal is to produce a sequence of minimal JSON commands that describe new shapes to
add. Think creatively – use rectangles, ellipses, or paths to produce colourful,
expressive compositions. Always respond with a *single line* of valid JSON with the
following shape array schema:
[
  {
    "type": "rectangle" | "ellipse" | "path",
    "x": number,
    "y": number,
    "w"?: number,
    "h"?: number,
    "color"?: string,
    "dash"?: string,
    "size"?: "s"|"m"|"l",
    "fill"?: string
  },
  ... (max 6 shapes per cycle)
]
Return an *empty array* when the composition feels complete.`

export async function POST(req: NextRequest) {
  const { shapes: currentShapes = [] } = (await req.json().catch(() => ({}))) as {
    shapes?: any[]
  }

  try {
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      temperature: 0.9,
      max_tokens: 300,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        {
          role: 'user',
          content: `Current canvas summary (${currentShapes.length} shapes): ${JSON.stringify(currentShapes)}\nNow reply with the next batch.`,
        },
      ],
    })

    const assistantReply = completion.choices[0].message?.content?.trim() ?? '[]'

    // First attempt: parse as‑is
    let newShapes: any[] | null = null
    try {
      newShapes = JSON.parse(assistantReply)
    } catch (_) {
      // Fallback – attempt to extract JSON from markdown/code block
      const match = assistantReply.match(/\[.*]/s)
      if (match) {
        newShapes = JSON.parse(match[0])
      }
    }

    if (!Array.isArray(newShapes)) {
      return NextResponse.json({ shapes: [] }, { status: 200 })
    }

    // Basic post‑processing: clamp count and coordinates
    const safeShapes = newShapes.slice(0, 10).map((s) => ({
      type: s.type ?? 'rectangle',
      x: typeof s.x === 'number' ? s.x : 0,
      y: typeof s.y === 'number' ? s.y : 0,
      w: typeof s.w === 'number' ? s.w : undefined,
      h: typeof s.h === 'number' ? s.h : undefined,
      color: typeof s.color === 'string' ? s.color : undefined,
      dash: typeof s.dash === 'string' ? s.dash : undefined,
      size: typeof s.size === 'string' ? s.size : undefined,
      fill: typeof s.fill === 'string' ? s.fill : undefined,
    }))

    return NextResponse.json({ shapes: safeShapes })
  } catch (err) {
    console.error(err)
    // On failure, gracefully return empty array so client can stop.
    return NextResponse.json({ shapes: [] }, { status: 200 })
  }
}
