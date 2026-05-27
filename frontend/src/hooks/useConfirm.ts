import { useState, useCallback } from 'react'

export function useConfirm() {
  const [state, setState] = useState<{ message: string; resolve: (v: boolean) => void } | null>(null)

  const confirm = useCallback((message: string): Promise<boolean> => {
    return new Promise(resolve => {
      setState({ message, resolve })
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

  return { confirm, dialogProps: state ? { message: state.message, onConfirm, onCancel } : null }
}
