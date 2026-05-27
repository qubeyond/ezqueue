import { useState, useEffect } from 'react'
import { MainPage } from '@/pages/MainPage'
import { UserPage } from '@/pages/UserPage'
import { AdminPage } from '@/pages/AdminPage'
import { ToastContainer } from '@/components/ToastContainer'
import { useToast } from '@/hooks/useToast'
import {
  ROOM_KEY,
  ROLE_KEY,
  ensureToken,
  apiFetch,
  setAccessToken,
  clearAccessToken,
} from '@/lib/auth'
import type { TakeTicketResponse } from '@/types/api'

type Page = 'main' | 'user' | 'admin'

export default function App() {
  const [page, setPage] = useState<Page>('main')
  const [roomId, setRoomId] = useState('')
  const [restoring, setRestoring] = useState(true)
  const { toasts, addToast, removeToast } = useToast()

  useEffect(() => {
    restoreSession().finally(() => setRestoring(false))
  }, [])

  async function restoreSession() {
    const savedRoom = localStorage.getItem(ROOM_KEY)
    const savedRole = localStorage.getItem(ROLE_KEY)
    if (!savedRoom || !savedRole) return

    try {
      await ensureToken()
    } catch (_) {
      goMain()
      return
    }

    if (savedRole === 'admin') {
      try {
        const res = await apiFetch('/api/v1/queue/ticket', {
          method: 'POST',
          body: JSON.stringify({ room_id: savedRoom }),
        })
        const data: TakeTicketResponse = await res.json()
        if (res.ok && data.is_admin && data.access_token) {
          setAccessToken(data.access_token)
          localStorage.setItem(ROLE_KEY, 'admin')
          setRoomId(savedRoom)
          setPage('admin')
          return
        }
      } catch (_) {}
      goMain()
      return
    }

    setRoomId(savedRoom)
    setPage('user')
  }

  function goMain() {
    clearAccessToken()
    setRoomId('')
    setPage('main')
    localStorage.removeItem(ROOM_KEY)
    localStorage.removeItem(ROLE_KEY)
  }

  function handleJoinAsUser(rId: string) {
    localStorage.setItem(ROOM_KEY, rId)
    localStorage.setItem(ROLE_KEY, 'user')
    setRoomId(rId)
    setPage('user')
  }

  function handleJoinAsAdmin(rId: string) {
    localStorage.setItem(ROOM_KEY, rId)
    localStorage.setItem(ROLE_KEY, 'admin')
    setRoomId(rId)
    setPage('admin')
  }

  function handleServed() {
    addToast('Вы были обслужены. Спасибо!', 'success')
    goMain()
  }

  function handleRoomClosed() {
    addToast('Комната закрыта', 'info')
    goMain()
  }

  if (restoring) return null

  return (
    <>
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      {page === 'main' && (
        <MainPage
          onJoinAsUser={handleJoinAsUser}
          onJoinAsAdmin={handleJoinAsAdmin}
        />
      )}
      {page === 'user' && (
        <UserPage
          roomId={roomId}
          onLeave={goMain}
          onServed={handleServed}
          onRoomClosed={handleRoomClosed}
          onToast={addToast}
        />
      )}
      {page === 'admin' && (
        <AdminPage
          roomId={roomId}
          onClose={goMain}
          onRoomClosed={handleRoomClosed}
          onToast={addToast}
        />
      )}
    </>
  )
}
