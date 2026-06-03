import { useState, useCallback } from 'react'

export interface ConfirmOptions {
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}

interface ConfirmState extends ConfirmOptions {
  resolve: (v: boolean) => void
}

export function useConfirm() {
  const [state, setState] = useState<ConfirmState | null>(null)

  const confirm = useCallback((opts: string | ConfirmOptions): Promise<boolean> => {
    const options: ConfirmOptions = typeof opts === 'string' ? { message: opts } : opts
    return new Promise(resolve => {
      setState({ ...options, resolve })
    })
  }, [])

  function onConfirm() {
    state?.resolve(true)
    setState(null)
  }

  function onCancel() {
    state?.resolve(false)
    setState(null)
  }

  return {
    confirm,
    dialogProps: state
      ? {
          message: state.message,
          confirmLabel: state.confirmLabel,
          cancelLabel: state.cancelLabel,
          danger: state.danger,
          onConfirm,
          onCancel,
        }
      : null,
  }
}
