/* ⑦ 모바일 찜 목록 — 찜한 장소 리스트 + 취향 분석(태그 빈도) 기반 추천 3곳 */
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronLeft, Heart } from 'lucide-react'
import * as api from '../api/client.js'
import { useFavorites } from '../store/FavoritesContext.jsx'
import { recommendByFavorites, topTags } from '../lib/derive.js'
import RestaurantCard from '../components/RestaurantCard.jsx'

export default function Favorites() {
  const { ids } = useFavorites()
  const [all, setAll] = useState([])
  useEffect(() => {
    api.getRestaurants().then(setAll)
  }, [])

  const favRestaurants = useMemo(() => ids.map((id) => all.find((r) => r.id === id)).filter(Boolean), [ids, all])
  // 로딩(데이터/찜 변경)마다 한 번 랜덤 추출 — 재렌더로 깜빡이지 않게 메모이즈
  const recos = useMemo(() => recommendByFavorites(favRestaurants, all, 3), [favRestaurants, all])
  const tags = useMemo(() => topTags(favRestaurants, 3), [favRestaurants])

  return (
    <div>
      <header className="sticky top-0 z-10 flex h-14 items-center border-b border-line bg-white px-5">
        <Link to="/" aria-label="홈" className="grid h-9 w-9 place-items-center">
          <ChevronLeft size={22} />
        </Link>
        <span className="ml-1 text-[18px] font-bold text-ink">찜한 장소</span>
        <span className="ml-auto text-[13px] text-muted">{favRestaurants.length}곳</span>
      </header>

      {favRestaurants.length === 0 ? (
        <div className="flex flex-col items-center gap-3 px-8 py-16 text-center">
          <Heart size={52} className="text-muted/40" />
          <h3 className="font-brand text-[17px] font-bold text-ink">아직 찜한 장소가 없어요</h3>
          <p className="text-[13px] leading-relaxed text-muted">
            마음에 드는 식당에서 하트를 누르면
            <br />
            여기에 모이고, 취향 추천이 시작돼요
          </p>
          <Link to="/" className="mt-1.5 rounded-xl bg-terra px-6 py-3 text-[14px] font-bold text-white">
            둘러보러 가기
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-3 px-5 py-4">
          {/* 찜한 장소 */}
          <div className="flex items-baseline justify-between">
            <h2 className="font-brand text-[18px] font-extrabold text-ink">찜한 장소</h2>
            <span className="text-[12px] text-muted">{favRestaurants.length}곳</span>
          </div>
          {favRestaurants.map((r) => (
            <RestaurantCard key={r.id} restaurant={r} />
          ))}

          {/* 취향 분석 기반 추천 */}
          {recos.length > 0 && (
            <>
              <div className="flex items-baseline justify-between pt-2">
                <h2 className="font-brand text-[18px] font-extrabold text-ink">찜 취향 기반 추천</h2>
                <span className="text-[12px] text-muted">비슷한 곳 {recos.length}곳</span>
              </div>
              <div className="rounded-2xl bg-green px-4 py-3.5">
                <b className="block text-[15px] font-bold text-white">찜한 취향을 분석했어요</b>
                <span className="text-[12px] text-white/70">
                  {(tags.length ? tags.map((t) => `#${t}`).join(' ') : '#향토음식')} 키워드가 잘 맞아요
                </span>
              </div>
              {recos.map(({ r, why }) => (
                <RestaurantCard key={r.id} restaurant={r} why={why} />
              ))}
            </>
          )}
        </div>
      )}
    </div>
  )
}
