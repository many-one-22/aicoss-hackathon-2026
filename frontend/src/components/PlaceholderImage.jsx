/* 이미지 — src가 있으면 실제 <img>, 없으면 대각선 해치 + 라벨 placeholder. */
export default function PlaceholderImage({ src, alt = '', label = '이미지', className = '', rounded = '' }) {
  if (src) {
    return <img src={src} alt={alt} loading="lazy" className={`object-cover ${rounded} ${className}`} />
  }
  return (
    <div
      className={`flex items-center justify-center text-[11px] text-[#7C7466] ${rounded} ${className}`}
      style={{ background: 'repeating-linear-gradient(45deg,#D8CFBE 0 12px,#CFC5B2 12px 24px)' }}
    >
      {label}
    </div>
  )
}
