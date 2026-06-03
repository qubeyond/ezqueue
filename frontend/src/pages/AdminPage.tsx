import { useEffect, useRef, useState } from 'react'
import { RoomHeader } from '@/components/RoomHeader'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { QrModal } from '@/components/QrModal'
import { Button } from '@/components/ui/Button'
import { Card, StatRow } from '@/components/ui/Card'
import { apiFetch, getAccessToken, ensureToken } from '@/lib/auth'
import { useTimer, fmtTime, fmtDuration } from '@/hooks/useTimer'
import { useConfirm } from '@/hooks/useConfirm'
import type { RoomStateResponse, QueueInfo, RoomStatsResponse, WsMessage } from '@/types/api'

interface Props {
  roomId: string
  onClose: () => void
  onRoomClosed: () => void
  onToast: (msg: string, type?: 'info' | 'success' | 'error') => void
}

export function AdminPage({ roomId, onClose, onRoomClosed, onToast }: Props) {
  const [queues, setQueues] = useState<QueueInfo[]>([])
  const [stats, setStats] = useState<{ completed: number; avg: number } | null>(null)
  const [loading, setLoading] = useState(true)
  const [showQr, setShowQr] = useState(false)
  const { confirm, dialogProps } = useConfirm()

  const closedRef = useRef(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const onRoomClosedRef = useRef(onRoomClosed)
  const onToastRef = useRef(onToast)
  onRoomClosedRef.current = onRoomClosed
  onToastRef.current = onToast

  const roomIdRef = useRef(roomId)
  roomIdRef.current = roomId

  function fetchStats() {
    apiFetch(`/api/v1/admin/stats/${roomIdRef.current}`)
      .then(r => r.ok ? r.json() : null)
      .then((d: RoomStatsResponse | null) => {
        if (d) setStats({ completed: d.completed, avg: d.avg_serve_seconds })
      })
      .catch(() => {})
  }

  function handleState(data: RoomStateResponse) {
    if (data.room_closed) {
      if (!closedRef.current) { closedRef.current = true; onRoomClosedRef.current() }
      return
    }
    setLoading(false)
    const ctx = data.admin_context
    if (ctx) setQueues(ctx.queues)
    fetchStats()
  }

  function fetchState() {
    apiFetch(`/api/v1/rooms/${roomIdRef.current}/state`)
      .then(r => r.ok ? r.json() : null)
      .then((d: RoomStateResponse | null) => { if (d) handleState(d) })
      .catch(() => {})
  }

  useEffect(() => {
    let destroyed = false

    function initWs() {
      if (destroyed) return
      if (wsRef.current) { wsRef.current.close(); wsRef.current = null }

      const token = getAccessToken()
      if (!token) { ensureToken().then(() => { if (!destroyed) initWs() }); return }

      const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
      const ws = new WebSocket(`${proto}//${location.host}/ws/room/${roomIdRef.current}?token=${encodeURIComponent(token)}`)
      wsRef.current = ws

      ws.onopen = () => {
        if (destroyed) { ws.close(); return }
        fetchState()
        pingTimer.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping')
        }, 25000)
      }

      ws.onclose = () => {
        if (pingTimer.current) { clearInterval(pingTimer.current); pingTimer.current = null }
        if (destroyed || closedRef.current) return
        reconnectTimer.current = setTimeout(() => {
          if (!destroyed && document.visibilityState !== 'hidden') initWs()
        }, 3000)
      }

      ws.onmessage = (event: MessageEvent<string>) => {
        if (destroyed || event.data === 'pong') return
        let msg: WsMessage
        try { msg = JSON.parse(event.data) as WsMessage } catch { return }
        if (msg.type === 'welcome' && msg.data) { handleState(msg.data); return }
        if (msg.type === 'update') {
          if (msg.data?.room_closed) {
            if (!closedRef.current) { closedRef.current = true; onRoomClosedRef.current() }
            return
          }
          fetchState()
        }
      }
    }

    initWs()

    return () => {
      destroyed = true
      if (wsRef.current) { wsRef.current.close(); wsRef.current = null }
      if (pingTimer.current) { clearInterval(pingTimer.current); pingTimer.current = null }
      if (reconnectTimer.current) { clearTimeout(reconnectTimer.current); reconnectTimer.current = null }
    }
  }, [])

  async function handleCloseRoom() {
    if (!await confirm({
      message: 'Закрыть комнату и завершить приём? Все ожидающие будут отключены.',
      confirmLabel: 'Закрыть',
      danger: true,
    })) return
    closedRef.current = true
    try { await apiFetch(`/api/v1/rooms/${roomId}`, { method: 'DELETE' }) } catch (_) {}
    onClose()
  }

  async function handleNext(queueLabel: string) {
    try {
      const res = await apiFetch('/api/v1/admin/next', {
        method: 'POST',
        body: JSON.stringify({ room_id: roomId, queue_label: queueLabel }),
      })
      if (!res.ok) onToast(((await res.json()) as { detail?: string }).detail || 'Ошибка', 'error')
    } catch (e) { onToast((e as Error).message, 'error') }
  }

  async function handleComplete(queueLabel: string) {
    try {
      const res = await apiFetch('/api/v1/admin/complete', {
        method: 'POST',
        body: JSON.stringify({ room_id: roomId, queue_label: queueLabel }),
      })
      if (!res.ok) onToast(((await res.json()) as { detail?: string }).detail || 'Ошибка', 'error')
    } catch (e) { onToast((e as Error).message, 'error') }
  }

  async function handleAddQueue() {
    try {
      const res = await apiFetch('/api/v1/admin/queue/add', { method: 'POST', body: JSON.stringify({ room_id: roomId }) })
      const d = await res.json() as { detail?: string; queue_label?: string }
      if (!res.ok) { onToast(d.detail || 'Ошибка', 'error'); return }
      onToast(`Очередь ${d.queue_label} добавлена`, 'success')
      fetchState()
    } catch (e) { onToast((e as Error).message, 'error') }
  }

  async function handleRemoveQueue(queueLabel: string) {
    if (!await confirm({
      message: `Удалить очередь ${queueLabel}? Ожидающие перейдут в другие очереди.`,
      confirmLabel: 'Удалить',
      danger: true,
    })) return
    try {
      const res = await apiFetch('/api/v1/admin/queue/remove', {
        method: 'DELETE',
        body: JSON.stringify({ room_id: roomId, queue_label: queueLabel }),
      })
      const d = await res.json() as { detail?: string; queue_label?: string }
      if (!res.ok) { onToast(d.detail || 'Ошибка', 'error'); return }
      onToast(`Очередь ${d.queue_label} удалена`, 'success')
      fetchState()
    } catch (e) { onToast((e as Error).message, 'error') }
  }

  const qrUrl = `${location.origin}/?room=${roomId}`

  function handleCopy() {
    navigator.clipboard.writeText(qrUrl).then(
      () => onToast('Ссылка на комнату скопирована', 'success'),
      () => onToast('Не удалось скопировать', 'error'),
    )
  }

  return (
    <div className="page-wrap">
      {dialogProps && <ConfirmDialog {...dialogProps} />}
      {showQr && <QrModal url={qrUrl} roomId={roomId} onClose={() => setShowQr(false)} />}
      <RoomHeader
        roomId={roomId}
        label="Комната"
        onCopy={handleCopy}
        onQr={() => setShowQr(true)}
        action={
          <Button variant="danger" size="sm" fullWidth={false} onClick={handleCloseRoom}>
            Закрыть
          </Button>
        }
      />

      <div className="page-content">
        {loading ? (
          <Card>
            <Button variant="secondary" loading disabled>Загрузка...</Button>
          </Card>
        ) : (
          queues.map(q => (
            <QueueCard
              key={q.label}
              queue={q}
              onNext={handleNext}
              onComplete={handleComplete}
              onRemove={handleRemoveQueue}
            />
          ))
        )}

        <div className="add-queue-row">
          <Button variant="secondary" onClick={handleAddQueue}>+ Добавить очередь</Button>
        </div>

        <Card title="Статистика сессии">
          <StatRow label="Всего обслужено">{stats?.completed ?? '—'}</StatRow>
          <StatRow label="Среднее время">{stats?.avg ? fmtDuration(stats.avg) : '—'}</StatRow>
        </Card>
      </div>
    </div>
  )
}

interface QueueCardProps {
  queue: QueueInfo
  onNext: (label: string) => Promise<void>
  onComplete: (label: string) => Promise<void>
  onRemove: (label: string) => Promise<void>
}

function QueueCard({ queue: q, onNext, onComplete, onRemove }: QueueCardProps) {
  const [actionLoading, setActionLoading] = useState(false)
  const elapsed = useTimer(q.elapsed_time ?? 0, q.status === 'serving')

  async function handleAction(fn: () => Promise<void>) {
    setActionLoading(true)
    try { await fn() } finally { setActionLoading(false) }
  }

  return (
    <Card className="queue-card">
      <div className="queue-card-head">
        <div className="queue-card-title">
          <span className="queue-card-name">Очередь {q.label}</span>
          <span className={`chip ${q.status}`}>
            {q.status === 'serving' ? 'Идёт приём' : 'Ожидание'}
          </span>
        </div>
        <Button
          variant="secondary"
          size="sm"
          fullWidth={false}
          className="queue-remove-btn"
          aria-label={`Удалить очередь ${q.label}`}
          onClick={() => handleAction(() => onRemove(q.label))}
        >
          ✕
        </Button>
      </div>

      <div className="adm-ticket-big">{q.current_ticket}</div>

      {q.status === 'serving' && (
        <div className={`timer-display${elapsed > 0 ? ' active' : ''}`}>
          {fmtTime(elapsed)}
        </div>
      )}

      <div className="queue-card-action">
        {q.status === 'serving' ? (
          <Button
            variant="danger-solid"
            loading={actionLoading}
            onClick={() => handleAction(() => onComplete(q.label))}
          >
            {!actionLoading && `Завершить · ${q.label}`}
          </Button>
        ) : (
          <Button
            variant="success-solid"
            loading={actionLoading}
            onClick={() => handleAction(() => onNext(q.label))}
          >
            {!actionLoading && `Вызвать следующего · ${q.label}`}
          </Button>
        )}
      </div>

      <div className="queue-line">
        {q.length === 0 ? (
          <span className="queue-empty">Очередь пуста</span>
        ) : (
          <span className="q-chip">{q.length} чел. ожидают</span>
        )}
      </div>
    </Card>
  )
}
