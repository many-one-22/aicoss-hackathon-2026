/* 하단 고정 탭바 — 홈 / 제철 / 음식점 / 대화. 모든 화면에서 항상 표시. */
import { NavLink } from 'react-router-dom'
import { Home, Store, Sprout, MessageCircle } from 'lucide-react'

const TABS = [
  { to: '/', label: '홈', icon: Home, end: true },
  { to: '/seasonal', label: '제철', icon: Sprout, end: false },
  { to: '/market', label: '음식점', icon: Store, end: false },
  { to: '/chat', label: '대화', icon: MessageCircle, end: false },
]

export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-1/2 z-30 flex h-16 w-full max-w-phone -translate-x-1/2 border-t border-line bg-white">
      {TABS.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            `flex flex-1 flex-col items-center justify-center gap-1 text-[11px] font-medium ${
              isActive ? 'text-terra' : 'text-muted-soft'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <Icon size={22} strokeWidth={isActive ? 2.4 : 2} />
              <span>{label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
