/**
 * @fileoverview Live camera canvas that decodes JPEG or H.264 frames from the
 * gateway video WebSocket (`/ws/video/subscribe/:agentId/:cameraName`).
 */

// Effect for socket lifecycle; refs for canvas/decoder/ws; connected flag for UI.
import { useEffect, useRef, useState } from 'react'

/**
 * Props for {@link LiveVideoCanvas}.
 */
type LiveVideoCanvasProps = {
  /** Agent telemetry / video key; null disables the stream. */
  agentId: string | null
  /** Camera stream name (default front_camera). */
  cameraName?: string
  /** Optional wrapper className. */
  className?: string
}

/**
 * Control-plane JSON config messages from the video publisher.
 */
type StreamConfig = {
  /** Message type; `"config"` updates codec preferences. */
  type?: string
  /** Codec hint: `h264` (default) or `jpeg` / `jpg`. */
  codec?: string
}

/**
 * Renders a live video feed onto an HTML canvas via WebSocket binary frames.
 *
 * Frame format: first byte = flags (bit0 = keyframe), remaining bytes = payload.
 *
 * @param props - LiveVideoCanvas props.
 * @returns Wrapper with optional waiting label + canvas.
 */
export function LiveVideoCanvas({
  agentId,
  cameraName = 'front_camera',
  className,
}: LiveVideoCanvasProps) {
  // Canvas element for drawing decoded frames.
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  // WebCodecs VideoDecoder instance when H.264 path is used.
  const decoderRef = useRef<any>(null)
  // Active WebSocket for cleanup.
  const wsRef = useRef<WebSocket | null>(null)
  // Latest codec config from control messages (defaults to h264).
  const configRef = useRef<StreamConfig>({ codec: 'h264' })
  // UI flag: true after onopen until close/error.
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    // Resolve canvas + 2d context; bail if missing agent or canvas.
    const canvas = canvasRef.current
    if (!canvas || !agentId) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Match page protocol for secure contexts.
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // Subscribe URL includes agent id and camera name (URL-encoded).
    const wsUrl = `${protocol}//${window.location.host}/ws/video/subscribe/${encodeURIComponent(agentId)}/${encodeURIComponent(cameraName)}`
    // Open binary WebSocket.
    const ws = new WebSocket(wsUrl)
    // Prefer ArrayBuffer payloads for JPEG / H.264 bytes.
    ws.binaryType = 'arraybuffer'
    // Stash for cleanup.
    wsRef.current = ws

    /**
     * Decode a JPEG payload by creating an object URL and drawing to canvas.
     * @param bytes - Raw JPEG bytes (without the leading flags byte).
     */
    const drawJpeg = (bytes: Uint8Array) => {
      // Copy into a standalone ArrayBuffer for the Blob constructor.
      const jpegBytes = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer
      // Wrap as image/jpeg Blob.
      const blob = new Blob([jpegBytes], { type: 'image/jpeg' })
      // Create a temporary object URL for Image decoding.
      const url = URL.createObjectURL(blob)
      const img = new Image()
      // When decoded, resize canvas to natural size and paint.
      img.onload = () => {
        canvas.width = img.naturalWidth || canvas.width
        canvas.height = img.naturalHeight || canvas.height
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
        // Release the object URL to avoid leaks.
        URL.revokeObjectURL(url)
      }
      // Kick off decode.
      img.src = url
    }

    /**
     * Lazily create / return a WebCodecs H.264 VideoDecoder bound to this canvas.
     * @returns Decoder instance, or null if VideoDecoder is unavailable.
     */
    const ensureH264Decoder = () => {
      // Reuse existing decoder.
      if (decoderRef.current) return decoderRef.current
      // Feature-detect WebCodecs.
      const WebVideoDecoder = (window as any).VideoDecoder
      if (!WebVideoDecoder) return null

      // Construct decoder with frame → canvas draw callback.
      const decoder = new WebVideoDecoder({
        output: (frame: any) => {
          try {
            // Prefer display size, then coded size, then current canvas size.
            const w = frame.displayWidth || frame.codedWidth || canvas.width
            const h = frame.displayHeight || frame.codedHeight || canvas.height
            canvas.width = w
            canvas.height = h
            ctx.drawImage(frame, 0, 0, w, h)
          } finally {
            // Always close VideoFrame to free GPU memory.
            frame.close()
          }
        },
        error: () => {
          // Keep stream alive even if one chunk fails decode.
        },
      })

      // Configure baseline AVC profile optimized for low latency.
      decoder.configure({
        // Default baseline avc if publisher did not send a specific profile.
        codec: 'avc1.42E01E',
        optimizeForLatency: true,
      })
      // Cache for subsequent frames.
      decoderRef.current = decoder
      return decoder
    }

    // Connection lifecycle → UI connected flag.
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)

    // Handle control JSON or binary media frames.
    ws.onmessage = (evt) => {
      // Text frames are control/config JSON.
      if (typeof evt.data === 'string') {
        try {
          const cfg = JSON.parse(evt.data) as StreamConfig
          // Only store messages typed as config.
          if (cfg.type === 'config') configRef.current = cfg
        } catch {
          // ignore malformed control messages
        }
        return
      }

      // Binary frame: flags byte + payload.
      const raw = new Uint8Array(evt.data as ArrayBuffer)
      // Need at least flags + 1 payload byte.
      if (raw.length < 2) return

      // Bit 0 marks keyframes for H.264.
      const flags = raw[0]
      const keyframe = Boolean(flags & 0x01)
      // Remainder is codec payload.
      const payload = raw.slice(1)
      // Honor publisher codec, default h264.
      const codec = (configRef.current.codec || 'h264').toLowerCase()

      // JPEG path — decode via Image/Blob.
      if (codec === 'jpeg' || codec === 'jpg') {
        drawJpeg(payload)
        return
      }

      // H.264 path — require WebCodecs decoder.
      const decoder = ensureH264Decoder()
      if (!decoder) return

      // Feature-detect EncodedVideoChunk.
      const EncodedChunk = (window as any).EncodedVideoChunk
      if (!EncodedChunk) return
      try {
        // Wrap payload as a WebCodecs chunk (timestamp in microseconds).
        const chunk = new EncodedChunk({
          type: keyframe ? 'key' : 'delta',
          timestamp: performance.now() * 1000, // microseconds
          data: payload,
        })
        // Push into decoder; output callback draws frames.
        decoder.decode(chunk)
      } catch {
        // keep alive on decode errors
      }
    }

    // Cleanup: close socket and decoder when agent/camera changes or unmount.
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
  }, [agentId, cameraName])

  return (
    <div className={className}>
      {/* Waiting caption while the socket is not yet open. */}
      {!connected && (
        <div className="text-xs text-[var(--color-text-muted)] px-2 py-1">
          Waiting for video stream...
        </div>
      )}
      {/* Drawing surface; black letterbox until first frame. */}
      <canvas ref={canvasRef} className="w-full h-full object-contain bg-black" />
    </div>
  )
}
