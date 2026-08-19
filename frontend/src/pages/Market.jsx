/* ⑥ 전통시장 — 현재 위치 기준 시장/향토음식점 목록(가까운 순).
   카테고리 칩: 전통시장 / 향토음식점. */
import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import * as api from '../api/client.js'
import RestaurantCard from '../components/RestaurantCard.jsx'

const CATEGORIES = ['전통시장', '향토음식점']

export default function Market() {
  const navigate = useNavigate()
  const [loc, setLoc] = useState(null)
  const [markets, setMarkets] = useState([])
  const [restaurants, setRestaurants] = useState([])
  // 선택 카테고리를 URL(?cat=)에 저장 → 상세 진입 후 뒤로가기 시 그 탭으로 복원
  const [searchParams, setSearchParams] = useSearchParams()
  const catParam = searchParams.get('cat')
  const cat = CATEGORIES.includes(catParam) ? catParam : '전통시장'
  const setCat = (c) => setSearchParams({ cat: c }, { replace: true })

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
        <span className="font-brand text-[20px] font-black text-green">{cat}</span>
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
                onClick={() => navigate(`/market/${m.id}`, { state: { market: m } })}
                className="w-full rounded-2xl border border-line bg-white p-3.5 text-left active:bg-cream"
              >
                <div className="flex items-baseline gap-2">
                  <b className="block font-brand text-[16px] font-bold text-ink">{m.name}</b>
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
                  <span className="ml-auto flex items-center gap-0.5 text-[12px] font-bold text-green">
                    상세보기 <ChevronRight size={14} />
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
