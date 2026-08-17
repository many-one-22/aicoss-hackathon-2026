/* ① 모바일 홈 — 위치 자동감지 · 오늘의 추천 · 찜 기반 추천 · 이번 주 제철(가로 스크롤) */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { MapPin, Heart, ChevronRight, AlertTriangle } from 'lucide-react'
import * as api from '../api/client.js'
import { useFavorites } from '../store/FavoritesContext.jsx'
import { recommendByFavorites } from '../lib/derive.js'
import RestaurantCard from '../components/RestaurantCard.jsx'
import { useDragScroll } from '../hooks/useDragScroll.js'

export default function Home() {
  const { ids } = useFavorites()
  const seasonalDrag = useDragScroll()
  const [loc, setLoc] = useState({ city: '광주', region: '광주', label: '광주 · 자동감지' })
  const [today, setToday] = useState(null)
  const [seasonal, setSeasonal] = useState([])
  const [all, setAll] = useState([])
  const month = new Date().getMonth() + 1

  useEffect(() => {
    api.detectLocation().then(setLoc)
    api.getRestaurants().then(setAll)
  }, [])

  useEffect(() => {
    if (!loc.city) return
    api.getTodayRecommendation(loc).then(setToday)
    api.getSeasonal(loc).then(setSeasonal)
  }, [loc.city, loc.region, loc.lat, loc.lng])

  const favRestaurants = all.filter((r) => ids.includes(r.id))
  const recos = recommendByFavorites(favRestaurants, all, 3)

  return (
    <div>
      {/* 헤더 */}
      <header className="sticky top-0 z-10 flex h-14 items-center gap-2 border-b border-line bg-cream px-5">
        <span className="font-serif text-[20px] font-black text-green">남도식탁</span>
        <span className="ml-auto flex items-center gap-1 text-[12px] text-muted">
          <MapPin size={13} className="text-terra" fill="#C85227" />
          <b className="font-bold text-terra">{loc.city}</b> · 자동감지
        </span>
        <Link to="/favorites" aria-label="찜 목록" className="relative ml-1 grid h-9 w-9 place-items-center">
          <Heart size={22} className="text-terra" fill={ids.length ? '#C85227' : 'transparent'} />
          {ids.length > 0 && (
            <span className="absolute right-0 top-0 grid h-4 min-w-4 place-items-center rounded-full bg-terra px-1 text-[10px] font-bold text-white">
              {ids.length}
            </span>
          )}
        </Link>
      </header>

      {/* 검색 프롬프트 */}
      <div className="mx-5 mt-4 rounded-2xl border border-line bg-white px-4 py-3.5 text-[14px] text-ink">
        지금 {loc.city} 계시죠? 오늘은 이 집 어때요?
      </div>

      {/* 리드 */}
      <div className="px-5 pb-1 pt-4">
        <h1 className="text-[20px] font-extrabold tracking-tight text-ink">즐겨찾기와 저장된 장소로 취향 탐색</h1>
        <p className="mt-1 text-[13px] text-muted">위치와 다녀간 기록을 보고 쓸수록 더 잘 맞는 곳을 골라드려요</p>
      </div>

      {/* 오늘의 추천 */}
      {today && (
        <Link
          to={`/place/${today.restaurant.id}`}
          className="mx-5 mt-3 block overflow-hidden rounded-2xl border border-line bg-white shadow-card"
        >
          <div
            className="relative flex h-[150px] items-center justify-center text-[13px] text-[#7C7466]"
            style={{ background: 'repeating-linear-gradient(45deg,#D8CFBE 0 12px,#CFC5B2 12px 24px)' }}
          >
            <span className="absolute left-3.5 top-3.5 rounded-full bg-terra px-2.5 py-1 text-[12px] font-bold text-white">
              오늘의 추천
            </span>
            이미지
          </div>
          <div className="flex flex-col gap-1.5 px-4 pb-4 pt-3.5">
            <h3 className="text-[20px] font-extrabold text-ink">{today.restaurant.name}</h3>
            <span className="text-[13px] text-muted">
              {today.restaurant.city} · {today.restaurant.key} 전문
            </span>
            {today.allergy.groups.length > 0 && (
              <span className="mt-0.5 flex items-center gap-1 text-[12px] font-semibold text-allergyink">
                <AlertTriangle size={13} /> {today.allergy.groups.join(', ')} 포함
              </span>
            )}
            <span className="mt-1 rounded-xl bg-terra py-3 text-center text-[14px] font-bold text-white">
              가는 길 보기
            </span>
          </div>
        </Link>
      )}

      {/* 찜 기반 추천 / 안내 */}
      {recos.length > 0 ? (
        <>
          <div className="mx-5 mt-4 rounded-2xl bg-green px-4 py-3.5">
            <b className="block text-[15px] font-bold text-white">찜한 {ids.length}곳 취향으로 골랐어요</b>
            <span className="text-[12px] text-white/70">비슷한 향토 키워드로 다음 장소를 추천해요</span>
          </div>
          <div className="flex flex-col gap-2.5 px-5 pt-2.5">
            {recos.map(({ r, why }) => (
              <RestaurantCard key={r.id} restaurant={r} why={why} />
            ))}
          </div>
        </>
      ) : (
        <div className="mx-5 mt-4 rounded-2xl bg-green px-4 py-3.5">
          <b className="block text-[15px] font-bold text-white">마음에 드는 곳에 하트를 눌러보세요</b>
          <span className="text-[12px] text-white/70">찜한 장소가 쌓일수록 취향에 맞는 추천을 드려요</span>
        </div>
      )}

      {/* 이번 주 제철 (드래그 가로 스크롤) */}
      <div className="flex items-end justify-between px-5 pb-1.5 pt-5">
        <div>
          <span className="text-[12px] text-muted-soft">{loc.city} 기준 · 밀어서 더 보기</span>
          <h2 className="mt-0.5 text-[19px] font-extrabold text-ink">{month}월 지금 제철</h2>
        </div>
        <Link to="/seasonal" className="shrink-0 text-[12px] font-semibold text-terra">
          전체 보기 →
        </Link>
      </div>
      <div
        ref={seasonalDrag.ref}
        {...seasonalDrag.bind}
        className="no-scrollbar flex cursor-grab gap-3 select-none overflow-x-auto px-5 pb-4 active:cursor-grabbing"
      >
        {seasonal.map((s) => (
          <Link key={s.id} to={`/ingredient/${s.id}`} className="w-[150px] shrink-0">
            <div
              className="flex h-24 items-center justify-center rounded-xl text-[15px] font-bold text-[#5C5344]"
              style={{ background: 'repeating-linear-gradient(45deg,#D8CFBE 0 12px,#CFC5B2 12px 24px)' }}
            >
              {s.item}
            </div>
            <b className="mt-2 block text-[14px] font-bold text-ink">{s.item}</b>
            <span className="text-[12px] text-muted">
              {s.region} · {s.level === '저렴' ? '지금 저렴' : s.vsAvgPct < 0 ? `연평균比 ${Math.abs(s.vsAvgPct)}%↓` : s.vsAvgPct > 0 ? `연평균比 ${s.vsAvgPct}%↑` : '연평균 수준'}
            </span>
            <span className="mt-1 flex items-center gap-0.5 text-[12px] font-bold text-terra">
              시세 보기 <ChevronRight size={13} />
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}
