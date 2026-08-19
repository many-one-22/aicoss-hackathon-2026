/* 제철 — 하단 탭바의 '제철' 창. 이번 주 제철 식재료 전체 목록.
   각 항목 탭 시 산지·시세 상세로 이동.
   [디자인] 크림 프레임 썸네일 · 가격 위계(이름/큰가격/등락칩) · 등락 배지 색 위계 ·
            원형 날짜 컨트롤 · 가이드 배너 · 미니 스파크라인. */
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, ChevronLeft, ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import * as api from '../api/client.js'
import { imageForIngredient } from '../lib/categoryImage.js'
import PlaceholderImage from '../components/PlaceholderImage.jsx'
import { LogoMark } from '../components/Logo.jsx'
import { CATEGORIES, categoryOf } from '../data/seasonalCategory.js'
import { useDragScroll } from '../hooks/useDragScroll.js'

/* 상태 태그(저렴/평균/비쌈) — 저렴은 딥그린, 비쌈은 테라코타, 그 외는 웜그레이. */
function StatusTag({ level }) {
  const cls =
    level === '저렴'
      ? 'bg-green/10 text-green'
      : level === '비쌈'
        ? 'bg-terra/10 text-terra'
        : 'bg-[#EFEAE0] text-muted-soft'
  return (
    <span className={`shrink-0 rounded-full px-2 py-0.5 font-brand text-[11px] font-bold ${cls}`}>
      {level}
    </span>
  )
}

/* 등락률 칩 — 하락(저렴해짐)=그린, 상승(비싸짐)=테라코타, 보합=그레이. 화살표 아이콘 포함. */
function TrendChip({ label, pct }) {
  if (pct == null) return null
  const down = pct < 0
  const up = pct > 0
  const Icon = down ? ArrowDownRight : up ? ArrowUpRight : Minus
  const cls = down
    ? 'bg-season text-seasonink'
    : up
      ? 'bg-terra/10 text-terra'
      : 'bg-line/50 text-muted'
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold ${cls}`}>
      <span className="font-medium opacity-70">{label}</span>
      <Icon size={12} strokeWidth={2.4} />
      {pct === 0 ? '보합' : `${Math.abs(pct)}%`}
    </span>
  )
}

export default function Seasonal() {
  const [seasonal, setSeasonal] = useState([])
  const [loc, setLoc] = useState(null)
  const thisMonth = new Date().getMonth() + 1
  const thisYear = new Date().getFullYear()
  const [offset, setOffset] = useState(0) // 0=이번 달, 음수=과거 달
  const [cat, setCat] = useState('전체') // 카테고리 필터(채소/과일/해산물 등) — '전체'면 다 보임
  const catDrag = useDragScroll() // 칩이 화면보다 길면 드래그로 넘길 수 있게
  const month = (((thisMonth - 1 + offset) % 12) + 12) % 12 + 1
  const year = thisYear + Math.floor((thisMonth - 1 + offset) / 12)
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

  // 이번 목록에 실제로 존재하는 카테고리만 칩으로 보여준다(빈 칩 방지)
  const availableCats = useMemo(
    () => CATEGORIES.filter((c) => seasonal.some((s) => categoryOf(s.item) === c)),
    [seasonal],
  )
  const shown = useMemo(
    () => (cat === '전체' ? seasonal : seasonal.filter((s) => categoryOf(s.item) === cat)),
    [seasonal, cat],
  )
  // 목록이 새로 바뀌었는데 고른 카테고리가 더 이상 없으면(달이 바뀌는 등) 전체로 되돌림
  useEffect(() => {
    if (cat !== '전체' && seasonal.length && !availableCats.includes(cat)) setCat('전체')
  }, [availableCats, cat, seasonal.length])

  return (
    <div>
      <header className="sticky top-0 z-10 flex h-14 items-center gap-2 border-b border-line bg-cream px-5">
        <LogoMark size={28} className="shrink-0" />
        <span className="font-brand text-[18px] font-black text-green">제철 시세</span>
        <span className="ml-auto text-[12px] text-muted">KAMIS 실측 · 오늘 기준</span>
      </header>

      {/* 날짜 컨트롤러 — 원형 서브 버튼 */}
      <div className="px-5 pt-4">
        <div className="flex flex-col items-center leading-tight">
          <span className="text-[13px] font-semibold text-muted-soft">{year}년</span>
          <div className="mt-1 flex items-center justify-center gap-3">
            <button
              onClick={prevMonth}
              disabled={!canPrev}
              aria-label="이전 달"
              className="flex h-7 w-7 items-center justify-center rounded-full bg-white text-muted shadow-sm transition disabled:opacity-30 active:bg-cream"
            >
              <ChevronLeft size={16} />
            </button>
            <h1 className="text-center font-brand text-[24px] font-extrabold text-ink">
              {month}월, {loc ? loc.city : '남도'}의 제철
            </h1>
            <button
              onClick={nextMonth}
              disabled={!canNext}
              aria-label="다음 달"
              className="flex h-7 w-7 items-center justify-center rounded-full bg-white text-muted shadow-sm transition disabled:opacity-30 active:bg-cream"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* 가이드 배너 — 연한 아이보리 박스, 왼쪽에 동그란 물음표 아이콘 */}
      <div className="mx-5 mt-3 flex items-center justify-center gap-1.5 rounded-xl bg-[#F5F2EB] px-3.5 py-2 text-[11px] text-muted-soft">
        <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full bg-white text-[10px] font-bold leading-none text-muted-soft">
          ?
        </span>
        <span>
          {offset === 0
            ? '지금이 가장 맛있고 저렴한 때 · 탭하면 12개월 시세를 볼 수 있어요'
            : `${month}월 제철 식재료와 그달 시세예요`}
        </span>
      </div>

      {/* 카테고리 필터 — 이번 목록에 있는 카테고리만 칩으로 노출 */}
      {availableCats.length > 1 && (
        <div
          ref={catDrag.ref}
          {...catDrag.bind}
          className="no-scrollbar flex cursor-grab select-none gap-2 overflow-x-auto px-5 pb-1 pt-3 active:cursor-grabbing"
        >
          {['전체', ...availableCats].map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setCat(c)}
              className={`shrink-0 rounded-full border px-3.5 py-1.5 text-[13px] font-semibold transition ${
                cat === c
                  ? 'border-green bg-green text-white'
                  : 'border-line bg-white text-ink/80'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      )}

      {/* 리스트 */}
      <div className="flex flex-col gap-2.5 px-5 py-4">
        {shown.map((s) => {
          const won = Math.round(s.current ?? 0).toLocaleString('ko-KR')
          const timeLabel = s.month === thisMonth ? '오늘' : `${s.month}월`
          return (
            <Link
              key={s.id}
              to={`/ingredient/${s.id}`}
              className="flex items-center gap-3 rounded-2xl border border-line bg-white p-3 shadow-sm transition active:scale-[0.99] active:bg-cream"
            >
              {/* 썸네일 — 크림 프레임(제각각 크롭도 안정된 카드 룩) */}
              <div className="shrink-0 rounded-2xl bg-[#F5F2EB] p-1.5">
                <PlaceholderImage
                  src={imageForIngredient(s.item)}
                  alt={s.item}
                  label={s.item}
                  className="h-14 w-14 rounded-xl text-[11px]"
                />
              </div>

              <div className="min-w-0 flex-1">
                {/* 1열: 이름 + 상태 태그 */}
                <div className="flex items-center gap-1.5">
                  <b className="truncate font-brand text-[16px] font-bold text-ink">{s.item}</b>
                  <StatusTag level={s.level} />
                </div>
                {/* 2열: 큰 오늘 가격 + 단위 */}
                <div className="mt-0.5 flex items-baseline gap-1">
                  <span className="text-[19px] font-extrabold text-ink">{won}원</span>
                  {s.unit && <span className="text-[12px] text-muted-soft">/ {s.unit}</span>}
                  <span className="ml-1 text-[11px] text-muted-soft">
                    {s.region} · {timeLabel}
                  </span>
                </div>
                {/* 3열: 등락 칩 */}
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                  <TrendChip label="연평균" pct={s.vsAvgPct} />
                  <TrendChip label="전월" pct={s.wowPct} />
                </div>
              </div>
            </Link>
          )
        })}
        {shown.length === 0 && (
          <div className="rounded-2xl border border-dashed border-line bg-cream px-4 py-6 text-center text-[13px] text-muted">
            {seasonal.length === 0 ? '이번 달 제철 시세 데이터가 없어요' : `이번 달은 ${cat} 제철 품목이 없어요`}
          </div>
        )}
      </div>
    </div>
  )
}
