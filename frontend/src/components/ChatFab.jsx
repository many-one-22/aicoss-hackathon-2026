/* 떠있는 큐레이터 AI 버튼 — 하단 탭바 위에 고정 */
import { Link } from 'react-router-dom'
import { MessageCircle } from 'lucide-react'

export default function ChatFab({ bottom = 84 }) {
  return (
    <Link
      to="/chat"
      aria-label="큐레이터 AI"
      className="fixed left-1/2 z-40 grid h-14 w-14 place-items-center rounded-full bg-terra text-white shadow-pop"
      style={{ bottom, transform: 'translateX(min(50vw, 215px))', marginLeft: -70 }}
    >
      <MessageCircle size={24} fill="#fff" className="text-terra" />
    </Link>
  )
}
