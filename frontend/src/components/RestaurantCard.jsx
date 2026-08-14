/* 식당 리스트 카드 — 썸네일 + 이름/부제 + (선택)추천 이유/태그 + 하트.
   카드 클릭 → 장소상세로 이동. 하트 클릭은 이벤트 전파를 막아 이동하지 않음. */
import { Link } from 'react-router-dom'
import PlaceholderImage from './PlaceholderImage.jsx'
import HeartButton from './HeartButton.jsx'

export default function RestaurantCard({ restaurant: r, why = [], showHeart = true }) {
  return (
    <Link
      to={`/place/${r.id}`}
      className="flex items-center gap-3 rounded-2xl border border-line bg-white p-3"
    >
      <PlaceholderImage className="h-16 w-16 shrink-0 rounded-xl text-[10px]" />
      <div className="min-w-0 flex-1">
        <b className="block truncate text-[16px] font-bold text-ink">{r.name}</b>
        <span className="block truncate text-[12px] text-muted">
          {r.city} · {r.key}
        </span>
        {why.length > 0 ? (
          <span className="mt-0.5 block text-[11px] font-semibold text-terra">
            {why.map((w) => `#${w}`).join(' ')} 취향 매칭
          </span>
        ) : (
          <span className="mt-1 inline-block rounded-full bg-tintgreen px-2.5 py-0.5 text-[11px] font-semibold text-green">
            #{(r.tags || [])[0] || '향토'}
          </span>
        )}
      </div>
      {showHeart && <HeartButton id={r.id} size={22} className="shrink-0 self-start" />}
    </Link>
  )
}
