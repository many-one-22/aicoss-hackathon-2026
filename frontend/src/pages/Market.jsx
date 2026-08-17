/* ⑥ 전통시장 — 현재 위치 기준 시장/향토음식점 목록(가까운 순).
   카테고리 칩: 전통시장 / 향토음식점. */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, MapPin } from 'lucide-react'
import * as api from '../api/client.js'
import RestaurantCard from '../components/RestaurantCard.jsx'

const CATEGORIES = ['전통시장', '향토음식점']

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
  const count = cat === '향토음식점' ? shownRestaurants.length : shownMarkets.length
  const areaLabel = loc ? `${loc.city} 기준` : '현재 위치 기준'

  return (
    <div>
      <header className="sticky top-0 z-10 flex h-14 items-center border-b border-line bg-white px-5">
        <span className="text-[18px] font-bold text-ink">전통시장</span>
        <Search size={20} className="ml-auto text-muted" />
      </header>

      {/* 카테고리 칩 */}
      <div className="no-scrollbar flex gap-2 overflow-x-auto bg-white px-5 pb-3 pt-1">
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

      {/* 지도 + 카운트 */}
      <div className="relative">
        <div className="flex h-[150px] items-center justify-center bg-season text-[12px] text-muted-soft">
          지도: {cat} 핀 · {areaLabel}
        </div>
        <span className="absolute left-5 top-3 flex items-center gap-1 rounded-full bg-white px-3 py-1 text-[12px] font-semibold text-ink shadow-card">
          <MapPin size={12} className="text-terra" fill="#C85227" />
          {loc ? loc.city : '남도'} 근처 {count}곳
        </span>
      </div>

      {/* 리스트 */}
      <div className="flex flex-col gap-2.5 px-5 py-4">
        {cat === '향토음식점'
          ? shownRestaurants.map((r) => <RestaurantCard key={r.id} restaurant={r} />)
          : shownMarkets.map((m) => (
              <div key={m.id} className="rounded-2xl border border-line bg-white p-3.5">
                <div className="flex items-baseline gap-2">
                  <b className="block text-[16px] font-bold text-ink">{m.name}</b>
                  {m._distKm != null && <span className="text-[12px] font-semibold text-terra">{m._distKm}km</span>}
                </div>
                <span className="text-[12px] text-muted">
                  {m.sido} {m.city}
                  {m.stores ? ` · 점포 ${m.stores}` : ''}
                  {m.items?.length ? ` · ${m.items.slice(0, 2).join('·')}` : ''}
                </span>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {m.parking && <Mk>주차 가능</Mk>}
                  {m.openCycle && <Mk>{m.openCycle === '매일' ? '상설' : `장날 ${m.openCycle}`}</Mk>}
                  {(m.items || []).some((it) => it.includes('수산물')) && <Mk accent>수산물</Mk>}
                </div>
              </div>
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
