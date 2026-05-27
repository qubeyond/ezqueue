import { useState, useEffect, useRef } from 'react'

export function useTimer(serverSeconds: number, running: boolean) {
  const [elapsed, setElapsed] = useState(running ? serverSeconds : 0)
  const startedAtRef = useRef<number | null>(running ? Date.now() - serverSeconds * 1000 : null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const serverSecondsRef = useRef(serverSeconds)
  serverSecondsRef.current = serverSeconds

  useEffect(() => {
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null }

    if (!running) {
      startedAtRef.current = null
      setElapsed(0)
      return
    }

    startedAtRef.current = Date.now() - serverSecondsRef.current * 1000

    intervalRef.current = setInterval(() => {
      if (startedAtRef.current !== null) {
        setElapsed(Math.floor((Date.now() - startedAtRef.current) / 1000))
      }
    }, 500)

    return () => {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null }
    }
  }, [running])

  return elapsed
}

export function fmtTime(s: number): string {
  return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0')
}

export function fmtDuration(s: number): string {
  return s < 60 ? `${s}с` : `${Math.floor(s / 60)}м ${s % 60}с`
}
