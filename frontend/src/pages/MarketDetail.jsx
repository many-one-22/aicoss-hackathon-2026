/* 전통시장 상세 — 시장 정보 + 길찾기(네이버) + 이 시장 근처 향토음식점.
   음식점 상세(PlaceDetail)와 같은 결의 레이아웃. 카드에서 넘어온 시장 객체(state)로 즉시
   렌더하고, id로 번들 데이터를 다시 조회해 갱신한다. */
import { useEffect, useState } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { ChevronLeft, Navigation, Store, Car, CalendarDays, MapPin } from 'lucide-react'
import * as api from '../api/client.js'
import RestaurantCard from '../components/RestaurantCard.jsx'
import ChatFab from '../components/ChatFab.jsx'

/* 이 시장의 네이버 '장소 화면'(길찾기·출발/도착 버튼 포함)을 연다.
   시장명 + 지역으로 검색해 동명 시장과 헷갈리지 않게 한다. */
function openNaverMarket(m) {
  const query = [m.name, m.sido, m.city].filter(Boolean).join(' ')
  window.open(
    `https://map.naver.com/p/search/${encodeURIComponent(query)}`,
    '_blank',
    'noopener,noreferrer',
  )
}

export default function MarketDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const passed = location.state?.market // 목록 카드에서 넘겨준 시장 객체
  const [m, setM] = useState(passed || null)
  const [nearby, setNearby] = useState([]) // 이 시장 근처 향토음식점

  useEffect(() => {
    let live = true
    api.getMarket(id).then((res) => live && res && setM(res))
    return () => (live = false)
  }, [id])

  useEffect(() => {
    if (!m) return
    // 이 시장 좌표 기준 같은 권역·가까운 순 향토음식점(_distKm 포함)
    api
      .getRestaurantsNear({ lat: m.lat, lng: m.lng, region: m.sido })
      .then((list) => setNearby(list.slice(0, 6)))
  }, [m])

  if (!m) return <div className="p-10 text-center text-muted">불러오는 중…</div>

  const isDaily = m.openCycle === '매일'

  return (
    <div>
      {/* 헤더 */}
      <header className="sticky top-0 z-10 flex h-14 items-center justify-center border-b border-line bg-white px-12 text-[16px] font-bold text-ink">
        <button
          onClick={() => (window.history.length > 1 ? navigate(-1) : navigate('/market'))}
          aria-label="뒤로"
          className="absolute left-3 grid h-9 w-9 place-items-center"
        >
          <ChevronLeft size={22} />
        </button>
        <span className="truncate font-brand">{m.name}</span>
      </header>

      {/* 히어로(시장은 사진 없음 → 초록 배너 + 아이콘) */}
      <div className="relative flex h-[180px] items-center justify-center bg-gradient-to-b from-[#D5EBDE] to-cream">
        <Store size={64} className="text-green/60" strokeWidth={1.5} />
        <span className="absolute bottom-4 left-4 rounded-full bg-green px-2.5 py-1 text-[12px] font-bold text-white">
          전통시장
        </span>
      </div>

      {/* 이름 + 위치 */}
      <div className="flex flex-col gap-1.5 px-5 pb-2 pt-4">
        <h1 className="font-brand text-[24px] font-extrabold tracking-tight text-ink">{m.name}</h1>
        <span className="text-[14px] text-muted">
          {m.sido} {m.city}
          {m._distKm != null && <span className="font-semibold text-terra"> · {m._distKm}km</span>}
        </span>
      </div>

      {/* 배지 */}
      <div className="flex flex-wrap gap-1.5 px-5 pb-1">
        {m.stores ? <Badge icon={<Store size={13} />}>점포 {m.stores}</Badge> : null}
        {m.openCycle && (
          <Badge icon={<CalendarDays size={13} />}>{isDaily ? '상설시장' : `장날 ${m.openCycle}`}</Badge>
        )}
        {m.parking && <Badge icon={<Car size={13} />}>주차 가능</Badge>}
        {(m.items || [])
          .filter((it) => it.includes('수산물'))
          .map((it) => (
            <Badge key={it} accent>
              {it}
            </Badge>
          ))}
      </div>

      {/* 주소 */}
      {m.addr && (
        <div className="mx-5 mt-3 flex items-start gap-2 rounded-xl border border-line bg-white px-3.5 py-3">
          <MapPin size={16} className="mt-0.5 shrink-0 text-green" />
          <span className="text-[13px] text-ink">{m.addr}</span>
        </div>
      )}

      {/* 취급 품목 */}
      {m.items?.length > 0 && (
        <div className="px-5 pt-3">
          <span className="font-brand text-[13px] font-bold text-ink">취급 품목</span>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {m.items.map((it) => (
              <span
                key={it}
                className="rounded-full border border-line bg-white px-2.5 py-1 text-[12px] text-ink/75"
              >
                {it}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 길찾기 */}
      <div className="px-5 py-4">
        <button
          type="button"
          onClick={() => openNaverMarket(m)}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#D5EBDE] py-3.5 text-[15px] font-extrabold text-green active:bg-[#C2E0D0]"
        >
          <Navigation size={17} /> 길찾기
        </button>
      </div>

      {/* 이 시장 근처 향토음식점 */}
      <div className="flex flex-col gap-2.5 bg-cream px-5 pb-8 pt-4">
        <span className="font-brand text-[15px] font-bold text-ink">이 시장 근처 향토음식점</span>
        {nearby.length > 0 ? (
          nearby.map((r) => <RestaurantCard key={r.id} restaurant={r} />)
        ) : (
          <div className="rounded-2xl border border-dashed border-line bg-white px-4 py-6 text-center text-[13px] text-muted">
            근처에서 찾은 향토음식점이 없어요
          </div>
        )}
      </div>

      <ChatFab />
    </div>
  )
}

function Badge({ children, icon = null, accent = false }) {
  return (
    <span
      className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-[12px] font-medium ${
        accent ? 'bg-terra/10 text-terra' : 'border border-line bg-white text-ink/70'
      }`}
    >
      {icon}
      {children}
    </span>
  )
}
