import clsx from 'clsx'

export function Spinner({ className }: { className?: string }) {
  return (
    <div className={clsx('flex items-center justify-center p-8', className)}>
      <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
