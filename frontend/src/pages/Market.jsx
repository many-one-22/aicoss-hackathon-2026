/* ⑥ 모바일 전통시장 — 위치 기반 시장 목록 + 카테고리 칩 필터(전통시장/향토음식점/제철 산지) */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'
import * as api from '../api/client.js'
import RestaurantCard from '../components/RestaurantCard.jsx'

const CATEGORIES = ['전통시장', '향토음식점', '제철 산지']

export default function Market() {
  const [markets, setMarkets] = useState([])
  const [restaurants, setRestaurants] = useState([])
  const [cat, setCat] = useState('전통시장')

  useEffect(() => {
    api.getMarkets().then(setMarkets)
    api.getRestaurants().then(setRestaurants)
  }, [])

  const shownMarkets = markets.filter((m) => m.category === cat)
  const shownRestaurants = restaurants.slice(0, 5)
  const count = cat === '향토음식점' ? shownRestaurants.length : shownMarkets.length

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
          지도: {cat} 핀 · 현재 위치 기준
        </div>
        <span className="absolute left-5 top-3 rounded-full bg-white px-3 py-1 text-[12px] font-semibold text-ink shadow-card">
          여수 · 보성권 {count}곳
        </span>
      </div>

      {/* 리스트 */}
      <div className="flex flex-col gap-2.5 px-5 py-4">
        {cat === '향토음식점'
          ? shownRestaurants.map((r) => <RestaurantCard key={r.id} restaurant={r} />)
          : shownMarkets.map((m) => (
              <div key={m.id} className="rounded-2xl border border-line bg-white p-3.5">
                <b className="block text-[16px] font-bold text-ink">{m.name}</b>
                <span className="text-[12px] text-muted">
                  {m.city} · 점포 {m.stores}
                  {m.items ? ` · ${m.items.slice(0, 2).join('·')}` : ''}
                </span>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {m.parking && <Mk>주차 가능</Mk>}
                  {m.marketDays && m.marketDays !== '상설' && <Mk>장날 {m.marketDays}</Mk>}
                  {m.onnuri && <Mk>온누리</Mk>}
                  {m.tag && <Mk accent>{m.tag}</Mk>}
                </div>
              </div>
            ))}
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
