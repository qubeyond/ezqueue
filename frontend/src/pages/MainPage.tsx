import { useState, useEffect, KeyboardEvent } from 'react'
import { Logo } from '@/components/Logo'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { apiFetch, ensureToken, setAccessToken } from '@/lib/auth'
import type { TakeTicketResponse, RoomCreateResponse } from '@/types/api'

interface Props {
  onJoinAsUser: (roomId: string) => void
  onJoinAsAdmin: (roomId: string) => void
}

export function MainPage({ onJoinAsUser, onJoinAsAdmin }: Props) {
  const [roomInput, setRoomInput] = useState('')
  const [joinLoading, setJoinLoading] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [inlineError, setInlineError] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const roomFromQr = params.get('room')
    if (roomFromQr) {
      window.history.replaceState({}, '', '/')
      joinRoom(roomFromQr.trim().toUpperCase())
    }
  }, [])

  function clearError() {
    setInlineError('')
  }

  async function joinRoom(rId: string) {
    setJoinLoading(true)
    clearError()
    try {
      await ensureToken()
      const res = await apiFetch('/api/v1/queue/ticket', {
        method: 'POST',
        body: JSON.stringify({ room_id: rId }),
      })
      const data: TakeTicketResponse = await res.json()
      if (!res.ok) {
        setInlineError((data as { detail?: string }).detail || 'Комната не найдена')
        return
      }
      if (data.is_admin && data.access_token) {
        setAccessToken(data.access_token)
        onJoinAsAdmin(rId)
      } else {
        onJoinAsUser(rId)
      }
    } catch (e) {
      setInlineError((e as Error).message)
    } finally {
      setJoinLoading(false)
    }
  }

  async function handleJoin() {
    const rId = roomInput.trim().toUpperCase()
    if (!rId || rId.length < 4) {
      setInlineError('Введите корректный ID комнаты')
      return
    }
    await joinRoom(rId)
  }

  async function handleCreate() {
    setCreateLoading(true)
    clearError()
    try {
      await ensureToken()
      const res = await apiFetch('/api/v1/rooms', { method: 'POST' })
      const data: RoomCreateResponse = await res.json()
      if (!res.ok) {
        setInlineError((data as { detail?: string }).detail || 'Ошибка создания комнаты')
        return
      }
      setAccessToken(data.access_token)
      onJoinAsAdmin(data.room_id)
    } catch (e) {
      setInlineError((e as Error).message)
    } finally {
      setCreateLoading(false)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleJoin()
  }

  return (
    <div className="page-wrap centered">
      <div className="center-wrap">
        <Logo />

        <Card title="Войти в комнату">
          {inlineError && <div className="inline-error">{inlineError}</div>}
          <label className="field-label" htmlFor="input-room-id">ID комнаты</label>
          <input
            id="input-room-id"
            type="text"
            placeholder="6 символов"
            maxLength={6}
            autoComplete="off"
            value={roomInput}
            onChange={e => setRoomInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <Button variant="primary" loading={joinLoading} onClick={handleJoin}>
            {joinLoading ? 'Подключение...' : 'Войти в очередь'}
          </Button>
          <div className="divider">или</div>
          <Button variant="secondary" loading={createLoading} onClick={handleCreate}>
            {createLoading ? 'Создание...' : 'Создать комнату (администратор)'}
          </Button>
        </Card>
      </div>
    </div>
  )
}
