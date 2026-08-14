/* ③ 모바일 검색 결과 없음 — 예외 UI + AI 챗봇 유도 + 근처 음식점 추천 */
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ChevronLeft, Search } from 'lucide-react'
import * as api from '../api/client.js'
import RestaurantCard from '../components/RestaurantCard.jsx'

export default function SearchEmpty() {
  const navigate = useNavigate()
  const [nearby, setNearby] = useState([])
  useEffect(() => {
    api.getRestaurants().then((all) => setNearby(all.slice(0, 2)))
  }, [])

  return (
    <div>
      <header className="sticky top-0 z-10 flex h-14 items-center justify-center border-b border-line bg-white px-12 text-[16px] font-bold text-ink">
        <button onClick={() => navigate(-1)} aria-label="뒤로" className="absolute left-3 grid h-9 w-9 place-items-center">
          <ChevronLeft size={22} />
        </button>
        검색 결과
      </header>

      <div className="flex flex-col items-center px-8 pb-4 pt-12 text-center">
        <Search size={44} className="text-muted-soft" strokeWidth={2.4} />
        <h2 className="mt-4 text-[20px] font-extrabold text-ink">검색 결과가 없어요</h2>
        <p className="mt-2 text-[14px] leading-relaxed text-muted">
          입력하신 조건에 맞는 정보를 찾지 못했어요. 대신 근처 맛집을 추천해드려요.
        </p>
        <Link
          to="/chat"
          className="mt-5 rounded-xl border-[1.5px] border-green bg-white px-6 py-3.5 text-[15px] font-bold text-green"
        >
          AI 챗봇에 물어보기
        </Link>
      </div>

      <div className="flex flex-col gap-2.5 px-5 pb-6 pt-6">
        <span className="text-[15px] font-bold text-ink">근처 음식점 추천</span>
        {nearby.map((r) => (
          <RestaurantCard key={r.id} restaurant={r} />
        ))}
      </div>
    </div>
  )
}
