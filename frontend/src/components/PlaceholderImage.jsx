/* 이미지 — src가 있으면 실제 <img>, 없으면(또는 로드 실패하면) 대각선 해치 + 라벨 placeholder.
   로드 실패까지 placeholder로 처리해, 링크가 끊기거나 파일이 아직 없는 경우에도
   깨진 이미지 아이콘 대신 자연스러운 자리표시가 보이게 한다. */
import { useEffect, useState } from 'react'

export default function PlaceholderImage({ src, alt = '', label = '이미지', className = '', rounded = '' }) {
  const [failed, setFailed] = useState(false)

  // src가 바뀌면 실패 상태를 초기화 — 이전 이미지의 실패가 다음 이미지에 남지 않게
  useEffect(() => {
    setFailed(false)
  }, [src])

  if (src && !failed) {
    return (
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onError={() => setFailed(true)}
        className={`object-cover ${rounded} ${className}`}
      />
    )
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
