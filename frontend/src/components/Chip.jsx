/* 필터/카테고리 칩 */
export default function Chip({ active = false, children, onClick, className = '' }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`whitespace-nowrap rounded-full border px-3.5 py-1.5 text-[13px] font-medium transition-colors ${
        active
          ? 'border-green bg-green text-white'
          : 'border-line bg-white text-ink/80 hover:border-green hover:text-green'
      } ${className}`}
    >
      {children}
    </button>
  )
}
