/* 모바일 폰 셸 — 최대폭 430px, 크림 배경. 하단 탭바는 모든 화면에서 항상 표시. */
import { Outlet } from 'react-router-dom'
import BottomNav from './BottomNav.jsx'

export default function Layout() {
  return (
    <div className="relative mx-auto min-h-screen w-full max-w-phone bg-cream shadow-pop">
      <div className="pb-[76px]">
        <Outlet />
      </div>
      <BottomNav />
    </div>
  )
}
