/* ② 모바일 장소상세 — 식당 ID 기반 동적 렌더 · 이름 옆 하트(찜) · 길찾기/전통시장/찜 액션 */
import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ChevronLeft, AlertTriangle, CheckCircle2 } from 'lucide-react'
import * as api from '../api/client.js'
import { allergyInfo, seasonalFor } from '../lib/derive.js'
import HeartButton from '../components/HeartButton.jsx'
import PlaceholderImage from '../components/PlaceholderImage.jsx'
import ChatFab from '../components/ChatFab.jsx'

export default function PlaceDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [r, setR] = useState(null)
  const [nearby, setNearby] = useState([])

  useEffect(() => {
    let live = true
    api.getRestaurant(id).then((res) => live && setR(res))
    return () => (live = false)
  }, [id])

  useEffect(() => {
    if (!r) return
    api.getRestaurants().then((all) =>
      setNearby(all.filter((x) => x.city === r.city && x.id !== r.id).slice(0, 2)),
    )
  }, [r])

  if (!r) return <div className="p-10 text-center text-muted">불러오는 중…</div>

  const allergy = allergyInfo(r)
  const season = seasonalFor(r)
  const mapUrl = `https://map.naver.com/v5/search/${encodeURIComponent(r.addr || r.name)}`

  return (
    <div>
      {/* 헤더 */}
      <header className="sticky top-0 z-10 flex h-14 items-center justify-center border-b border-line bg-white px-12 text-[16px] font-bold text-ink">
        <button
          onClick={() => (window.history.length > 1 ? navigate(-1) : navigate('/'))}
          aria-label="뒤로"
          className="absolute left-3 grid h-9 w-9 place-items-center"
        >
          <ChevronLeft size={22} />
        </button>
        <span className="truncate">{r.name}</span>
      </header>

      {/* 히어로 */}
      <div className="relative h-[260px]">
        <PlaceholderImage className="h-full w-full text-[13px]" />
        <span className="absolute bottom-4 left-4 rounded-full bg-terra px-2.5 py-1 text-[12px] font-bold text-white">
          오늘의 추천
        </span>
      </div>

      {/* 이름 + 하트 */}
      <div className="flex flex-col gap-1.5 px-5 pb-2 pt-4">
        <div className="flex items-center gap-2.5">
          <h1 className="min-w-0 flex-1 text-[24px] font-extrabold tracking-tight text-ink">{r.name}</h1>
          <HeartButton id={r.id} size={26} className="shrink-0" stop={false} />
        </div>
        <span className="text-[14px] text-muted">
          {r.city} · {r.region} · {r.key} 전문
        </span>
      </div>

      {/* 알레르기 */}
      {allergy.groups.length > 0 ? (
        <div className="mx-5 mb-3 flex flex-col gap-1.5 rounded-xl bg-allergy px-3.5 py-3">
          <b className="flex items-center gap-1 text-[14px] font-bold text-ink">
            <AlertTriangle size={15} className="text-terra" /> 알레르기 정보
          </b>
          <span className="text-[13px] text-allergyink">
            {allergy.groups.join(', ')} 포함 가능 · {allergy.items.join('·') || r.key} 사용
          </span>
        </div>
      ) : (
        <div className="mx-5 mb-3 flex flex-col gap-1.5 rounded-xl bg-tintgreen px-3.5 py-3">
          <b className="flex items-center gap-1 text-[14px] font-bold text-ink">
            <CheckCircle2 size={15} className="text-seasonink" /> 알레르기 정보
          </b>
          <span className="text-[13px] text-seasonink">주요 조개류·갑각류 특이사항 없음 (메뉴 확인 권장)</span>
        </div>
      )}

      {/* 제철 시세 */}
      {season && (
        <Link
          to={`/ingredient/${season.id}`}
          className="flex min-h-[90px] items-center justify-between gap-3 bg-season px-5 py-4"
        >
          <div>
            <b className="block text-[14px] font-bold text-ink">{season.label}</b>
            <span className="text-[12px] text-muted">지금이 가장 맛있고 저렴할 때예요</span>
          </div>
          <span className={`shrink-0 text-[14px] font-bold ${season.delta > 0 ? 'text-terra' : 'text-seasonink'}`}>
            연평균比 {Math.abs(season.delta)}%{season.delta > 0 ? '↑' : '↓'}
          </span>
        </Link>
      )}

      {/* 액션 */}
      <div className="flex gap-2.5 px-5 py-3.5">
        <a
          href={mapUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 rounded-xl bg-[#D5EBDE] py-3.5 text-center text-[15px] font-extrabold text-green active:bg-[#C2E0D0]"
        >
          길찾기
        </a>
        <Link
          to="/market"
          className="flex-1 rounded-xl border-[1.5px] border-green bg-white py-3.5 text-center text-[15px] font-bold text-green"
        >
          전통시장 보기
        </Link>
      </div>

      {/* 이 근처 다른 추천 */}
      {nearby.length > 0 && (
        <div className="flex flex-col gap-2.5 bg-cream px-5 pb-8 pt-4">
          <span className="text-[15px] font-bold text-ink">이 근처 다른 추천</span>
          <div className="flex gap-2.5">
            {nearby.map((n) => (
              <Link key={n.id} to={`/place/${n.id}`} className="flex min-w-0 flex-1 flex-col gap-1">
                <PlaceholderImage className="h-[90px] w-full rounded-lg" />
                <b className="truncate text-[13px] font-bold text-ink">{n.name}</b>
                <span className="text-[11px] text-muted">
                  {n.key} · {n.city}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      <ChatFab />
    </div>
  )
}
