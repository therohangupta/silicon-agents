import { useEffect, useRef, useState } from 'react'

type LiveVideoCanvasProps = {
  robotId: string | null
  cameraName?: string
  className?: string
}

type StreamConfig = {
  type?: string
  codec?: string
}

export function LiveVideoCanvas({
  robotId,
  cameraName = 'front_camera',
  className,
}: LiveVideoCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const decoderRef = useRef<any>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const configRef = useRef<StreamConfig>({ codec: 'h264' })
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !robotId) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/video/subscribe/${encodeURIComponent(robotId)}/${encodeURIComponent(cameraName)}`
    const ws = new WebSocket(wsUrl)
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws

    const drawJpeg = (bytes: Uint8Array) => {
      const blob = new Blob([bytes], { type: 'image/jpeg' })
      const url = URL.createObjectURL(blob)
      const img = new Image()
      img.onload = () => {
        canvas.width = img.naturalWidth || canvas.width
        canvas.height = img.naturalHeight || canvas.height
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
        URL.revokeObjectURL(url)
      }
      img.src = url
    }

    const ensureH264Decoder = () => {
      if (decoderRef.current) return decoderRef.current
      const WebVideoDecoder = (window as any).VideoDecoder
      if (!WebVideoDecoder) return null

      const decoder = new WebVideoDecoder({
        output: (frame: any) => {
          try {
            const w = frame.displayWidth || frame.codedWidth || canvas.width
            const h = frame.displayHeight || frame.codedHeight || canvas.height
            canvas.width = w
            canvas.height = h
            ctx.drawImage(frame, 0, 0, w, h)
          } finally {
            frame.close()
          }
        },
        error: () => {
          // Keep stream alive even if one chunk fails decode.
        },
      })

      decoder.configure({
        // Default baseline avc if publisher did not send a specific profile.
        codec: 'avc1.42E01E',
        optimizeForLatency: true,
      })
      decoderRef.current = decoder
      return decoder
    }

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)

    ws.onmessage = (evt) => {
      if (typeof evt.data === 'string') {
        try {
          const cfg = JSON.parse(evt.data) as StreamConfig
          if (cfg.type === 'config') configRef.current = cfg
        } catch {
          // ignore malformed control messages
        }
        return
      }

      const raw = new Uint8Array(evt.data as ArrayBuffer)
      if (raw.length < 2) return

      const flags = raw[0]
      const keyframe = Boolean(flags & 0x01)
      const payload = raw.slice(1)
      const codec = (configRef.current.codec || 'h264').toLowerCase()

      if (codec === 'jpeg' || codec === 'jpg') {
        drawJpeg(payload)
        return
      }

      const decoder = ensureH264Decoder()
      if (!decoder) return

      const EncodedChunk = (window as any).EncodedVideoChunk
      if (!EncodedChunk) return
      try {
        const chunk = new EncodedChunk({
          type: keyframe ? 'key' : 'delta',
          timestamp: performance.now() * 1000, // microseconds
          data: payload,
        })
        decoder.decode(chunk)
      } catch {
        // keep alive on decode errors
      }
    }

    return () => {
      ws.close()
      wsRef.current = null
      setConnected(false)
      if (decoderRef.current) {
        try {
          decoderRef.current.close()
        } catch {
          // ignore
        }
        decoderRef.current = null
      }
    }
  }, [robotId, cameraName])

  return (
    <div className={className}>
      {!connected && (
        <div className="text-xs text-[var(--color-text-muted)] px-2 py-1">
          Waiting for video stream...
        </div>
      )}
      <canvas ref={canvasRef} className="w-full h-full object-contain bg-black" />
    </div>
  )
}
