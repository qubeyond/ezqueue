interface Props {
  roomId: string
  label: string
  onCopy: () => void
  action: React.ReactNode
}

export function RoomHeader({ roomId, label, onCopy, action }: Props) {
  return (
    <div className="page-header">
      <div>
        <div className="room-label">{label}</div>
        <div className="room-id" onClick={onCopy} title="Скопировать ID">
          {roomId}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {action}
      </div>
    </div>
  )
}
