/* ⑥ 전통시장 — 현재 위치 기준 시장/향토음식점 목록(가까운 순).
   카테고리 칩: 전통시장 / 향토음식점. */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Navigation } from 'lucide-react'
import * as api from '../api/client.js'
import RestaurantCard from '../components/RestaurantCard.jsx'

const CATEGORIES = ['전통시장', '향토음식점']

/* 클릭 시 네이버 지도에서 해당 시장 '장소 화면'을 연다.
   (검색결과 + 출발/도착 버튼이 있는 그 페이지 — 사용자가 도착을 누르면 길찾기로 이어짐)
   시장명 + 지역으로 검색해 다른 지역 동명 시장과 헷갈리지 않게 한다. */
function openNaverPlace(target) {
  const { name, sido, city } = target
  const query = [name, sido, city].filter(Boolean).join(' ')
  const url = `https://map.naver.com/p/search/${encodeURIComponent(query)}`
  window.open(url, '_blank', 'noopener,noreferrer')
}

export default function Market() {
  const [loc, setLoc] = useState(null)
  const [markets, setMarkets] = useState([])
  const [restaurants, setRestaurants] = useState([])
  const [cat, setCat] = useState('전통시장')

  useEffect(() => {
    api.detectLocation().then((l) => {
      setLoc(l)
      api.getMarkets(l).then(setMarkets) // 가까운 순 시장
      api.getRestaurantsNear(l).then(setRestaurants) // 같은 권역·가까운 순 향토음식점(_distKm 포함)
    })
  }, [])

  const shownMarkets = markets
  const shownRestaurants = restaurants.slice(0, 200)

  return (
    <div>
      <header className="sticky top-0 z-10 flex h-14 items-center border-b border-line bg-cream px-5">
        <span className="font-serif text-[20px] font-black text-green">{cat}</span>
      </header>

      {/* 카테고리 칩 */}
      <div className="no-scrollbar flex gap-2 overflow-x-auto bg-cream px-5 pb-2 pt-4">
        {CATEGORIES.map((c) => (
          <button
            key={c}
            onClick={() => setCat(c)}
            className={`shrink-0 rounded-full border px-4 py-2 text-[13px] font-semibold ${
              c === cat ? 'border-green bg-green text-white' : 'border-line bg-white text-ink/80'
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      {/* 리스트 */}
      <div className="flex flex-col gap-2.5 px-5 pb-4 pt-2">
        {cat === '향토음식점'
          ? shownRestaurants.map((r) => <RestaurantCard key={r.id} restaurant={r} />)
          : shownMarkets.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => openNaverPlace(m)}
                className="w-full rounded-2xl border border-line bg-white p-3.5 text-left active:bg-cream"
              >
                <div className="flex items-baseline gap-2">
                  <b className="block text-[16px] font-bold text-ink">{m.name}</b>
                  {m._distKm != null && <span className="text-[12px] font-semibold text-terra">{m._distKm}km</span>}
                </div>
                <span className="text-[12px] text-muted">
                  {m.sido} {m.city}
                  {m.stores ? ` · 점포 ${m.stores}` : ''}
                  {m.items?.length ? ` · ${m.items.slice(0, 2).join('·')}` : ''}
                </span>
                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  {m.parking && <Mk>주차 가능</Mk>}
                  {m.openCycle && <Mk>{m.openCycle === '매일' ? '상설' : `장날 ${m.openCycle}`}</Mk>}
                  {(m.items || []).some((it) => it.includes('수산물')) && <Mk accent>수산물</Mk>}
                  <span className="ml-auto flex items-center gap-1 text-[12px] font-bold text-green">
                    <Navigation size={13} /> 길찾기
                  </span>
                </div>
              </button>
            ))}
        {(cat === '향토음식점' ? shownRestaurants : shownMarkets).length === 0 && (
          <div className="rounded-2xl border border-dashed border-line bg-cream px-4 py-6 text-center text-[13px] text-muted">
            근처에서 찾은 결과가 없어요
          </div>
        )}
      </div>
    </div>
  )
}

function Mk({ children, accent = false }) {
  return (
    <span
      className={`rounded-full px-2.5 py-1 text-[12px] font-medium ${
        accent ? 'bg-terra/10 text-terra' : 'border border-line bg-white text-ink/70'
      }`}
    >
      {children}
    </span>
  )
}
