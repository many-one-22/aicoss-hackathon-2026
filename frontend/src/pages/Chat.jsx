/* ④ 모바일 챗봇 — 위치 안내 → 질의 → 음식점 카드 동적 렌더. 말풍선 간격 여유 확보. */
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronLeft, Plus, AlertTriangle } from 'lucide-react'
import * as api from '../api/client.js'
import { allergyInfo } from '../lib/derive.js'
import { useRestaurantPhoto } from '../hooks/useRestaurantPhoto.js'
import PlaceholderImage from '../components/PlaceholderImage.jsx'

const GREETING = { who: 'bot', text: '지금 여수 계시죠? 무엇을 도와드릴까요?' }
const SUGGESTIONS = [
  { label: '가족 식사', prompt: '가족이랑 먹기 좋은 국물요리 있어?' },
  { label: '혼밥', prompt: '혼자 가기 좋은 곳 알려줘' },
  { label: '술 안주', prompt: '술 한잔하기 좋은 안주 맛집' },
  { label: '해장', prompt: '해장하기 좋은 국밥집' },
]

export default function Chat() {
  const [messages, setMessages] = useState([GREETING])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages])

  async function send(text) {
    const q = (text ?? input).trim()
    if (!q || busy) return
    setInput('')
    setBusy(true)
    setMessages((m) => [...m, { who: 'user', text: q }, { who: 'typing' }])
    const res = await api.chatReply(q)
    setMessages((m) => [...m.filter((x) => x.who !== 'typing'), ...res.messages])
    setBusy(false)
  }

  function reset() {
    setMessages([GREETING])
    setInput('')
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="flex h-14 shrink-0 items-center border-b border-line bg-white px-4">
        <Link to="/" aria-label="뒤로" className="grid h-9 w-9 place-items-center">
          <ChevronLeft size={22} />
        </Link>
        <span className="ml-1 text-[16px] font-bold text-ink">큐레이터 AI</span>
        <button onClick={reset} className="ml-auto flex items-center gap-1 text-[13px] font-medium text-muted">
          <Plus size={15} /> 새 대화
        </button>
      </header>

      {/* 메시지 (간격 여유 gap-4) */}
      <div ref={scrollRef} className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-5 pb-40">
        {messages.map((m, i) => (
          <Bubble key={i} m={m} />
        ))}
      </div>

      {/* 입력 (하단 탭바 위) */}
      <div className="fixed bottom-16 left-1/2 z-20 w-full max-w-phone -translate-x-1/2 border-t border-line bg-cream px-4 pb-3 pt-3">
        <div className="no-scrollbar mb-2 flex gap-2 overflow-x-auto">
          {SUGGESTIONS.map((s) => (
            <button
              key={s.label}
              onClick={() => send(s.prompt)}
              className="shrink-0 rounded-full border border-line bg-white px-3 py-1.5 text-[13px] text-ink/80"
            >
              {s.label}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            send()
          }}
          className="flex items-center gap-2 rounded-xl border border-line bg-white py-1.5 pl-4 pr-1.5"
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
  )
}

function Bubble({ m }) {
  const photoSrc = useRestaurantPhoto(m.restaurant)
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
  if (m.who === 'card' && m.restaurant) {
    const r = m.restaurant
    const allergy = allergyInfo(r)
    return (
      <div className="mr-auto w-[88%] overflow-hidden rounded-2xl border border-line bg-white shadow-card">
        <PlaceholderImage src={photoSrc} alt={r.name} className="h-[120px] w-full text-[12px]" />
        <div className="flex flex-col gap-1.5 p-3.5">
          <b className="text-[18px] font-extrabold text-ink">{r.name}</b>
          <span className="text-[13px] text-muted">
            {r.city} · {r.key} · {(r.tags || [])[0]}
          </span>
          {allergy.groups.length > 0 && (
            <span className="flex items-center gap-1 text-[12px] font-semibold text-allergyink">
              <AlertTriangle size={12} /> {allergy.groups.join(', ')} 포함
            </span>
          )}
          <div className="mt-1 flex gap-2">
            <Link to={`/place/${r.id}`} className="flex-1 rounded-lg bg-terra py-2.5 text-center text-[13px] font-bold text-white">
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
        <div className="bg-cream px-3.5 py-2 text-[11px] text-muted-soft">
          근거: 음식 영양·알레르기 DB · 이용 기록 기반 추천
        </div>
      </div>
    )
  }
  return (
    <div className="mr-auto max-w-[80%] rounded-2xl rounded-bl-md bg-white px-4 py-3 text-[15px] leading-relaxed text-ink shadow-card">
      {m.text}
    </div>
  )
}
