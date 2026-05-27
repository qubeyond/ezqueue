import type { Toast, ToastType } from '@/hooks/useToast'

interface Props {
  toasts: Toast[]
  onRemove: (id: number) => void
}

export function ToastContainer({ toasts, onRemove }: Props) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type as ToastType}`}>
          <span className="toast-msg">{t.msg}</span>
          <button className="toast-close" onClick={() => onRemove(t.id)}>&times;</button>
        </div>
      ))}
    </div>
  )
}
