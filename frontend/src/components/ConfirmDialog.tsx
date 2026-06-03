import { useEffect, useRef } from 'react'
import { Modal, ModalActions } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'

interface Props {
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  message,
  confirmLabel = 'Подтвердить',
  cancelLabel = 'Отмена',
  danger = false,
  onConfirm,
  onCancel,
}: Props) {
  const cancelRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    cancelRef.current?.focus()
  }, [])

  return (
    <Modal onClose={onCancel} size="sm">
      <p className="modal-text">{message}</p>
      <ModalActions>
        <Button ref={cancelRef} variant="secondary" onClick={onCancel}>
          {cancelLabel}
        </Button>
        <Button variant={danger ? 'danger-solid' : 'primary'} onClick={onConfirm}>
          {confirmLabel}
        </Button>
      </ModalActions>
    </Modal>
  )
}
