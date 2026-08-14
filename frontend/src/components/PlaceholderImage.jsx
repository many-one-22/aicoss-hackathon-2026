/* 이미지 자리표시자 — 실제 이미지가 없을 때 대각선 해치 + 라벨 표시.
   restaurant.image 가 생기면 <img> 로 교체 지점. */
export default function PlaceholderImage({ label = '이미지', className = '', rounded = '' }) {
  return (
    <div
      className={`flex items-center justify-center text-[11px] text-[#7C7466] ${rounded} ${className}`}
      style={{ background: 'repeating-linear-gradient(45deg,#D8CFBE 0 12px,#CFC5B2 12px 24px)' }}
    >
      {label}
    </div>
  )
}
