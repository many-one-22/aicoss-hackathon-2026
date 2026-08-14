/* 제철 — 하단 탭바의 '제철' 창. 이번 주 제철 식재료 전체 목록.
   각 항목 탭 시 산지·시세 상세로 이동. */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import * as api from '../api/client.js'

export default function Seasonal() {
  const [seasonal, setSeasonal] = useState([])
  useEffect(() => {
    api.getSeasonal().then(setSeasonal)
  }, [])

  return (
    <div>
      <header className="sticky top-0 z-10 flex h-14 items-center border-b border-line bg-white px-5">
        <span className="text-[18px] font-bold text-ink">제철 달력</span>
        <span className="ml-auto text-[12px] text-muted">KAMIS 시세 연동</span>
      </header>

      <div className="px-5 pb-1 pt-4">
        <h1 className="text-[20px] font-extrabold text-ink">지금 남도의 제철</h1>
        <p className="mt-1 text-[13px] text-muted">가장 맛있고 저렴한 때예요 · 탭하면 산지·시세를 볼 수 있어요</p>
      </div>

      <div className="flex flex-col gap-2.5 px-5 py-4">
        {seasonal.map((s) => {
          const buyNow = s.delta < 0
          return (
            <Link
              key={s.id}
              to={`/ingredient/${s.id}`}
              className="flex items-center gap-3 rounded-2xl border border-line bg-white p-3"
            >
              <div
                className="grid h-16 w-16 shrink-0 place-items-center rounded-xl text-[11px] text-[#7C7466]"
                style={{ background: 'repeating-linear-gradient(45deg,#D8CFBE 0 12px,#CFC5B2 12px 24px)' }}
              >
                {s.short}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <b className="truncate text-[16px] font-bold text-ink">{s.name}</b>
                  {buyNow && (
                    <span className="shrink-0 rounded-full bg-terra/10 px-2 py-0.5 text-[11px] font-bold text-terra">
                      구매 적기
                    </span>
                  )}
                </div>
                <span className="block text-[12px] text-muted">
                  산지 {s.origin} · 제철 {s.season}
                </span>
                <span
                  className={`mt-0.5 block text-[12px] font-semibold ${
                    s.delta < 0 ? 'text-seasonink' : s.delta > 0 ? 'text-terra' : 'text-muted'
                  }`}
                >
                  {s.delta < 0
                    ? `지금 제철 · 평년比 ${Math.abs(s.delta)}%↓`
                    : s.delta > 0
                      ? `평년比 +${s.delta}%↑`
                      : '평년 수준'}
                </span>
              </div>
              <ChevronRight size={18} className="shrink-0 text-muted-soft" />
            </Link>
          )
        })}
      </div>
    </div>
  )
}
