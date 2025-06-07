import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

export const runtime = 'edge'          // for Vercel Edge or keep undefined for Node

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

export async function POST(req: NextRequest) {
  const { prompt, shapes = [] } = await req.json()

  /* build messages                                                   */
  /* call openai.chat.completions.create({...})                       */
  /* parse assistantReply into an array called newShapes              */
  /* validate / coerce, then:                                         */

  return NextResponse.json({ shapes: newShapes })
}
