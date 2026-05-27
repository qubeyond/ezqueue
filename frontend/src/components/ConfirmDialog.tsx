interface Props {
  message: string
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({ message, onConfirm, onCancel }: Props) {
  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,.35)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 10000,
      animation: 'fadeIn .15s ease-out',
      padding: '0 16px',
    }}>
      <div style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
        padding: '24px',
        width: '100%',
        maxWidth: 360,
        boxShadow: 'var(--shadow-lg)',
        animation: 'fadeIn .15s ease-out',
      }}>
        <p style={{ fontSize: '.95rem', lineHeight: 1.5, marginBottom: 20, color: 'var(--text)' }}>
          {message}
        </p>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className="btn btn-secondary"
            style={{ flex: 1 }}
            onClick={onCancel}
          >
            Отмена
          </button>
          <button
            className="btn btn-primary"
            style={{ flex: 1 }}
            onClick={onConfirm}
          >
            Подтвердить
          </button>
        </div>
      </div>
    </div>
  )
}
