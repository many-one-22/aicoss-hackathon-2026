/* ④ 모바일 챗봇 — 위치 안내 → 질의 → 음식점 카드 동적 렌더. 말풍선 간격 여유 확보. */
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { RotateCw, AlertTriangle } from 'lucide-react'
import * as api from '../api/client.js'
import { allergyInfo } from '../lib/derive.js'
import { useRestaurantPhoto } from '../hooks/useRestaurantPhoto.js'
import PlaceholderImage from '../components/PlaceholderImage.jsx'
import { SEASONAL } from '../data/seasonal.js'
import { LogoMark } from '../components/Logo.jsx'

const greetingFor = (loc) => ({
  who: 'bot',
  text: '무엇을 도와드릴까요?',
})

/* 첫 화면 질문 예시 — 누르면 바로 전송된다.
   지금 제철인 재료 중 서로 다른 2개를 매번 새로 뽑아 '~들어간 음식'/'~시세'로 채운다
   (첫 로딩·'새 대화' 리롤마다 재료가 바뀜). */
function randomExamples() {
  const month = new Date().getMonth() + 1
  const items = [...new Set(SEASONAL.filter((s) => s.peak_months.includes(month)).map((s) => s.item))]
  const pool = items.length >= 2 ? items : ['감자', '전복']
  const shuffled = [...pool].sort(() => Math.random() - 0.5)
  const [a, b] = [shuffled[0], shuffled[1] ?? shuffled[0]]
  return [`${a} 들어간 음식 추천해줘`, `${b} 시세 어때?`]
}

export default function Chat() {
  const [loc, setLoc] = useState(null)
  const [messages, setMessages] = useState([greetingFor(null)])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [examples, setExamples] = useState(randomExamples)
  const [kbOffset, setKbOffset] = useState(0) // 열린 키보드 높이(px) — 입력창을 그만큼 띄운다
  const scrollRef = useRef(null)

  useEffect(() => {
    api.detectLocation().then((l) => {
      setLoc(l)
      setMessages((m) => (m.length === 1 && m[0].who === 'bot' ? [greetingFor(l)] : m))
    })
  }, [])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages])

  /* 모바일 키보드 대응 — position:fixed 요소는 키보드가 떠도 레이아웃 뷰포트 기준으로 그대로
     붙어 있어(특히 iOS Safari) 화면 밖(키보드 뒤)으로 가려진다. visualViewport로 실제 보이는
     높이를 추적해 입력창(예시 질문 포함)을 키보드 위로 밀어 올린다. */
  useEffect(() => {
    const vv = window.visualViewport
    if (!vv) return
    const update = () => {
      const offset = window.innerHeight - vv.height - vv.offsetTop
      setKbOffset(offset > 40 ? Math.round(offset) : 0) // 40px 미만은 주소창 접힘 등 노이즈로 무시
    }
    vv.addEventListener('resize', update)
    vv.addEventListener('scroll', update)
    update()
    return () => {
      vv.removeEventListener('resize', update)
      vv.removeEventListener('scroll', update)
    }
  }, [])

  // 키보드가 뜨면(입력창이 위로 밀리면) 방금 메시지가 가려지지 않게 다시 맨 아래로
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [kbOffset])

  async function send(text) {
    const q = (text ?? input).trim()
    if (!q || busy) return
    setInput('')
    setBusy(true)
    setMessages((m) => [...m, { who: 'user', text: q }, { who: 'typing' }])
    const res = await api.chatReply(q, loc || {})
    setMessages((m) => [...m.filter((x) => x.who !== 'typing'), ...res.messages])
    setBusy(false)
  }

  function reset() {
    setMessages([greetingFor(loc)])
    setInput('')
    setExamples(randomExamples())
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b border-line bg-cream px-5">
        <LogoMark size={28} className="shrink-0" />
        <span className="font-brand text-[18px] font-black text-green">큐레이터 AI</span>
      </header>

      {/* 메시지 (간격 여유 gap-4) */}
      <div ref={scrollRef} className="no-scrollbar flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-5 pb-40">
        {messages.map((m, i) => (
          <Bubble key={i} m={m} />
        ))}
      </div>

      {/* 입력 (하단 탭바 위 · 키보드가 뜨면 키보드 바로 위까지 따라 올라감) */}
      <div
        className="fixed left-1/2 z-20 w-full max-w-phone -translate-x-1/2 bg-cream px-4 pb-3 pt-3 transition-[bottom] duration-150"
        style={{ bottom: kbOffset > 0 ? kbOffset : 64 }}
      >
        {/* 질문 예시 — 아직 아무것도 안 물어봤을 때만 노출('새 대화'로 초기화하면 다시 보임) */}
        {!messages.some((m) => m.who === 'user') && (
          <div className="mb-2 flex flex-wrap gap-2">
            {examples.map((q) => (
              <button
                key={q}
                type="button"
                disabled={busy}
                onClick={() => send(q)}
                className="shrink-0 rounded-full border border-line bg-white px-3.5 py-2 text-[13px] font-medium text-ink/80 active:bg-cream disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        )}
        <div className="flex items-center gap-2">
          {/* 새 대화(리롤) — 대화·예시 질문을 초기화 */}
          <button
            type="button"
            onClick={reset}
            aria-label="새 대화 시작"
            className="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-line bg-white text-terra active:bg-cream"
          >
            <RotateCw size={20} />
          </button>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              send()
            }}
            className="flex flex-1 items-center gap-2 rounded-xl border border-line bg-white py-1.5 pl-4 pr-1.5"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="무엇이든 물어보세요"
              className="flex-1 bg-transparent py-2 text-[15px] text-ink outline-none placeholder:text-muted-soft"
            />
            <button type="submit" className="rounded-lg bg-terra px-4 py-2.5 text-[14px] font-bold text-white">
              전송
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

/* 봇 말풍선 안의 **강조** 표기를 굵은 글씨로 바꿔 준다. 그 외 마크다운은 지원하지 않는다. */
function RichText({ text = '' }) {
  return text.split(/\*\*(.+?)\*\*/g).map((part, i) =>
    i % 2 ? <b key={i} className="font-bold text-ink">{part}</b> : part,
  )
}

function Bubble({ m }) {
  if (m.who === 'user')
    return (
      <div className="ml-auto max-w-[80%] rounded-2xl rounded-br-md bg-green px-4 py-3 text-[15px] leading-relaxed text-white">
        {m.text}
      </div>
    )
  if (m.who === 'typing')
    return (
      <div className="mr-auto max-w-[80%] rounded-2xl rounded-bl-md bg-white px-4 py-3 text-[15px] italic text-muted shadow-card">
        답변 근거 데이터를 찾는 중…
      </div>
    )
  if (m.who === 'card' && m.restaurant)
    return (
      <div className="mr-auto w-[88%]">
        <ChatCard r={m.restaurant} />
      </div>
    )
  if (m.who === 'cards' && m.restaurants?.length)
    return <CardCarousel restaurants={m.restaurants} />
  if (m.who === 'price' && m.price)
    return (
      <div className="mr-auto w-[86%]">
        <PriceCard p={m.price} />
      </div>
    )
  return (
    <div className="mr-auto max-w-[80%] rounded-2xl rounded-bl-md bg-white px-4 py-3 text-[15px] leading-relaxed text-ink shadow-card">
      <RichText text={m.text} />
    </div>
  )
}

/* 챗봇 추천 카드 1장 — 세로 단일카드/가로 캐러셀 양쪽에서 재사용. 너비는 부모가 결정. */
function ChatCard({ r }) {
  const photoSrc = useRestaurantPhoto(r)
  const allergy = allergyInfo(r)
  return (
    <div className="w-full overflow-hidden rounded-2xl border border-line bg-white shadow-card">
      <Link to={`/place/${r.id}`} state={{ restaurant: r }} className="block active:bg-cream">
        <PlaceholderImage src={photoSrc} alt={r.name} className="h-[120px] w-full text-[12px]" />
        <div className="flex flex-col gap-1.5 px-3.5 pt-3.5">
          <b className="font-brand text-[18px] font-extrabold text-ink">{r.name}</b>
          <span className="text-[13px] text-muted">
            {r.city} · {r.key}
            {r._distKm != null && <span className="font-semibold text-terra"> · {r._distKm}km</span>}
          </span>
          {r.desc && <span className="line-clamp-2 text-[12px] text-ink/70">{r.desc}</span>}
          {allergy.groups.length > 0 && (
            <span className="flex items-center gap-1 text-[12px] font-semibold text-allergyink">
              <AlertTriangle size={12} /> {allergy.groups.join(', ')} 포함
            </span>
          )}
        </div>
      </Link>
      <div className="flex gap-2 p-3.5 pt-2.5">
        <Link to={`/place/${r.id}`} state={{ restaurant: r }} className="flex-1 rounded-lg bg-[#D5EBDE] py-2.5 text-center text-[13px] font-extrabold text-green">
          상세 보기
        </Link>
        <a
          href={`https://map.naver.com/v5/search/${encodeURIComponent(r.addr || r.name)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 rounded-lg border-[1.5px] border-green py-2.5 text-center text-[13px] font-bold text-green"
        >
          길찾기
        </a>
      </div>
    </div>
  )
}

/* 마우스로도 가로 스크롤을 쉽게 — 세로 휠을 가로로 바꿔주고, 잡고 끌기도 지원한다.
   (터치 기기는 원래 스와이프가 되므로 영향 없음. 끌어서 넘긴 직후의 클릭은 카드 이동을
   방지하려고 억제한다.) */
function useDragScroll() {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    let down = false, moved = false, startX = 0, startLeft = 0
    const onDown = (e) => { down = true; moved = false; startX = e.pageX; startLeft = el.scrollLeft }
    const onMove = (e) => {
      if (!down) return
      const dx = e.pageX - startX
      if (Math.abs(dx) > 4) moved = true
      el.scrollLeft = startLeft - dx
    }
    const onUp = () => { down = false }
    const onClick = (e) => { if (moved) { e.preventDefault(); e.stopPropagation(); moved = false } }
    const onWheel = (e) => {
      if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) { el.scrollLeft += e.deltaY; e.preventDefault() }
    }
    el.addEventListener('mousedown', onDown)
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    el.addEventListener('click', onClick, true)
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => {
      el.removeEventListener('mousedown', onDown)
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
      el.removeEventListener('click', onClick, true)
      el.removeEventListener('wheel', onWheel)
    }
  }, [])
  return ref
}

/* 추천 카드 가로 캐러셀 — 휠·드래그로 옆으로 넘길 수 있다. */
function CardCarousel({ restaurants }) {
  const ref = useDragScroll()
  return (
    <div
      ref={ref}
      className="no-scrollbar -mr-4 flex shrink-0 cursor-grab snap-x snap-mandatory select-none gap-3 overflow-x-auto overflow-y-hidden pb-1 pr-4 active:cursor-grabbing"
    >
      {restaurants.map((r, i) => (
        <div key={i} className="w-[80%] shrink-0 snap-start">
          <ChatCard r={r} />
        </div>
      ))}
    </div>
  )
}

/* 시세 답변 카드 — 현재가·추세·6개월 예측을 한눈에. 추세는 소비자 관점 색상
   (오름세=주황/주의, 내림세=초록/구매유리)으로 표시해 판단을 돕는다. */
function PriceCard({ p }) {
  const up = p.trend === '오름세'
  const down = p.trend === '내림세'
  const trendColor = up ? 'text-terra' : down ? 'text-green' : 'text-muted'
  const trendBg = up ? 'bg-terra/10' : down ? 'bg-[#D5EBDE]' : 'bg-cream'
  const arrow = up ? '▲' : down ? '▼' : '―'
  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-white shadow-card">
      <div className="flex items-center justify-between border-b border-line bg-cream px-4 py-2.5">
        <b className="font-brand text-[15px] font-extrabold text-green">{p.item} 시세</b>
        <span className="text-[11px] text-muted">{p.year_month} 기준</span>
      </div>
      <div className="px-4 py-3.5">
        <div className="flex items-end gap-1">
          <b className="font-brand text-[27px] font-black leading-none text-ink">
            {p.current.toLocaleString()}
          </b>
          <span className="pb-0.5 text-[15px] font-semibold text-ink">원</span>
          {p.unit && <span className="pb-0.5 text-[13px] text-muted">/{p.unit}</span>}
        </div>
        {p.has_forecast ? (
          <>
            <div className="mt-3 flex items-center gap-2">
              <span className={`inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[13px] font-bold ${trendBg} ${trendColor}`}>
                {arrow} {p.trend}
              </span>
              <span className="text-[13px] text-muted">
                6개월 뒤 <b className="text-ink">{p.forecast.toLocaleString()}원</b>
              </span>
            </div>
            <div className="mt-2 text-[11px] text-muted-soft">
              AI 예측 · 오차 {p.mape}% ({p.forecast_month})
            </div>
            {p.advice && (
              <div className={`mt-3 rounded-lg px-3 py-2 text-[12.5px] font-semibold ${trendBg} ${trendColor}`}>
                💡 {p.advice}
              </div>
            )}
          </>
        ) : (
          <div className="mt-3 text-[12px] text-muted">예측 데이터 없음 · 현재 시세 기준</div>
        )}
      </div>
    </div>
  )
}
