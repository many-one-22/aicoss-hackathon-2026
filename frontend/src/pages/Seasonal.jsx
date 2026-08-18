/* 제철 — 하단 탭바의 '제철' 창. 이번 주 제철 식재료 전체 목록.
   각 항목 탭 시 산지·시세 상세로 이동. */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, ChevronLeft } from 'lucide-react'
import * as api from '../api/client.js'
import { imageForIngredient } from '../lib/categoryImage.js'
import PlaceholderImage from '../components/PlaceholderImage.jsx'

export default function Seasonal() {
  const [seasonal, setSeasonal] = useState([])
  const [loc, setLoc] = useState(null)
  const thisMonth = new Date().getMonth() + 1
  const [offset, setOffset] = useState(0) // 0=이번 달, 음수=과거 달
  const month = (((thisMonth - 1 + offset) % 12) + 12) % 12 + 1
  const canPrev = offset > -11 // 최대 1년 전까지
  const canNext = offset < 0 // 이번 달이면 다음 달(미래)로 못 감

  useEffect(() => {
    api.detectLocation().then(setLoc)
  }, [])

  useEffect(() => {
    if (!loc) return
    api.getSeasonal({ ...loc, month }).then(setSeasonal)
  }, [loc, month])

  const prevMonth = () => canPrev && setOffset((o) => o - 1)
  const nextMonth = () => canNext && setOffset((o) => o + 1)

  return (
    <div>
      <header className="sticky top-0 z-10 flex h-14 items-center border-b border-line bg-cream px-5">
        <span className="font-serif text-[20px] font-black text-green">제철 시세</span>
        <span className="ml-auto text-[12px] text-muted">KAMIS 실측 · 오늘 기준</span>
      </header>

      <div className="px-5 pb-1 pt-4">
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={prevMonth}
            disabled={!canPrev}
            aria-label="이전 달"
            className="grid h-9 w-9 place-items-center rounded-full text-muted transition disabled:opacity-25 active:bg-line/40"
          >
            <ChevronLeft size={22} />
          </button>
          <h1 className="text-center text-[20px] font-extrabold text-ink">
            {month}월, {loc ? loc.city : '남도'}의 제철
          </h1>
          <button
            onClick={nextMonth}
            disabled={!canNext}
            aria-label="다음 달"
            className="grid h-9 w-9 place-items-center rounded-full text-muted transition disabled:opacity-25 active:bg-line/40"
          >
            <ChevronRight size={22} />
          </button>
        </div>
        <p className="mt-1 text-center text-[13px] text-muted">
          {offset === 0
            ? '가장 맛있고 저렴한 때예요 · 탭하면 12개월 시세를 볼 수 있어요'
            : `${month}월 제철 식재료와 그달 시세예요`}
        </p>
      </div>

      <div className="flex flex-col gap-2.5 px-5 py-4">
        {seasonal.map((s) => {
          const buyNow = s.level === '저렴'
          const won = (s.current ?? 0).toLocaleString('ko-KR')
          return (
            <Link
              key={s.id}
              to={`/ingredient/${s.id}`}
              className="flex items-center gap-3 rounded-2xl border border-line bg-white p-3"
            >
              <PlaceholderImage
                src={imageForIngredient(s.item)}
                alt={s.item}
                label={s.item}
                className="h-16 w-16 shrink-0 rounded-xl text-[11px]"
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <b className="truncate text-[16px] font-bold text-ink">{s.item}</b>
                  <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-bold ${
                    s.level === '저렴'
                      ? 'bg-green/10 text-green'
                      : s.level === '비쌈'
                        ? 'bg-red-500/10 text-red-600'
                        : 'bg-line/60 text-muted'
                  }`}>
                    {s.level}
                  </span>
                </div>
                <span className="block text-[12px] text-muted">
                  {s.region} · {s.month === thisMonth ? '오늘' : `${s.month}월`} {won}원{s.unit ? `/${s.unit}` : ''}
                </span>
                <div className="mt-0.5 flex flex-wrap items-center gap-x-1.5 text-[12px] font-semibold">
                  <span
                    className={
                      s.vsAvgPct < 0 ? 'text-seasonink' : s.vsAvgPct > 0 ? 'text-terra' : 'text-muted'
                    }
                  >
                    {s.vsAvgPct < 0
                      ? `연평균比 ${Math.abs(s.vsAvgPct)}%↓`
                      : s.vsAvgPct > 0
                        ? `연평균比 ${s.vsAvgPct}%↑`
                        : '연평균 수준'}
                  </span>
                  {s.wowPct != null && (
                    <>
                      <span className="text-line">·</span>
                      <span
                        className={
                          s.wowPct < 0 ? 'text-seasonink' : s.wowPct > 0 ? 'text-terra' : 'text-muted'
                        }
                      >
                        {s.wowPct < 0
                          ? `전월比 ${Math.abs(s.wowPct)}%↓`
                          : s.wowPct > 0
                            ? `전월比 ${s.wowPct}%↑`
                            : '전월 보합'}
                      </span>
                    </>
                  )}
                </div>
              </div>
              <ChevronRight size={18} className="shrink-0 text-muted-soft" />
            </Link>
          )
        })}
        {seasonal.length === 0 && (
          <div className="rounded-2xl border border-dashed border-line bg-cream px-4 py-6 text-center text-[13px] text-muted">
            이번 달 제철 시세 데이터가 없어요
          </div>
        )}
      </div>
    </div>
  )
}
