import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'

export type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'danger'
  | 'success'
  | 'danger-solid'
  | 'success-solid'

interface Props extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'className'> {
  variant?: ButtonVariant
  size?: 'md' | 'sm'
  /** Растянуть на всю ширину контейнера (по умолчанию да). */
  fullWidth?: boolean
  /** Показать спиннер и заблокировать кнопку. */
  loading?: boolean
  children: ReactNode
  className?: string
}

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  {
    variant = 'secondary',
    size = 'md',
    fullWidth = true,
    loading = false,
    disabled,
    children,
    className = '',
    type = 'button',
    ...rest
  },
  ref,
) {
  const classes = [
    'btn',
    `btn-${variant}`,
    size === 'sm' && 'btn-sm',
    !fullWidth && 'btn-auto',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <button ref={ref} type={type} className={classes} disabled={disabled || loading} {...rest}>
      {loading && <span className="spinner" />}
      {children}
    </button>
  )
})
