/* 가벼운 토스트 — useToast()(msg) 로 하단에 잠깐 표시 */
import { createContext, useContext, useRef, useState, useCallback } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [msg, setMsg] = useState('')
  const [show, setShow] = useState(false)
  const timer = useRef(null)

  const toast = useCallback((text) => {
    setMsg(text)
    setShow(true)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setShow(false), 1600)
  }, [])

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div
        className={`pointer-events-none fixed left-1/2 z-50 -translate-x-1/2 rounded-full bg-ink px-4 py-2.5 text-[13px] font-semibold text-white transition-all duration-200 ${
          show ? 'bottom-[96px] opacity-100' : 'bottom-[84px] opacity-0'
        }`}
      >
        {msg}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
