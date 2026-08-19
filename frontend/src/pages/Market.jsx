/* ⑥ 음식점 — 현재 위치 기준 향토음식점 목록(같은 권역·가까운 순).
   전통시장 목록은 이 창에서 빼고, 제철 재료 상세의 '가까운 전통시장'에서 상세로 바로 들어간다. */
import { useEffect, useState } from 'react'
import * as api from '../api/client.js'
import RestaurantCard from '../components/RestaurantCard.jsx'
import { LogoMark } from '../components/Logo.jsx'

export default function Market() {
  const [restaurants, setRestaurants] = useState([])

  useEffect(() => {
    api.detectLocation().then((l) => {
      api.getRestaurantsNear(l).then(setRestaurants) // 같은 권역·가까운 순 향토음식점(_distKm 포함)
    })
  }, [])

  const shownRestaurants = restaurants.slice(0, 200)

  return (
    <div>
      <header className="sticky top-0 z-10 flex h-14 items-center gap-2 border-b border-line bg-cream px-5">
        <LogoMark size={28} className="shrink-0" />
        <span className="font-brand text-[18px] font-black text-green">향토음식점</span>
      </header>

      {/* 리스트 */}
      <div className="flex flex-col gap-2.5 px-5 pb-4 pt-4">
        {shownRestaurants.map((r) => (
          <RestaurantCard key={r.id} restaurant={r} />
        ))}
        {shownRestaurants.length === 0 && (
          <div className="rounded-2xl border border-dashed border-line bg-cream px-4 py-6 text-center text-[13px] text-muted">
            근처에서 찾은 결과가 없어요
          </div>
        )}
      </div>
    </div>
  )
}
