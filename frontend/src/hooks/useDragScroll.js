/* 마우스 드래그로 가로 스크롤 — 터치는 브라우저 기본 스와이프로 동작.
   드래그 후 발생하는 클릭(링크 이동)은 onClickCapture 로 억제한다. */
import { useRef } from 'react'

export function useDragScroll() {
  const ref = useRef(null)
  const st = useRef({ down: false, startX: 0, startLeft: 0, moved: false })

  const onMouseDown = (e) => {
    const el = ref.current
    if (!el) return
    st.current = { down: true, startX: e.pageX, startLeft: el.scrollLeft, moved: false }
  }
  const onMouseMove = (e) => {
    const el = ref.current
    const s = st.current
    if (!s.down || !el) return
    e.preventDefault()
    const dx = e.pageX - s.startX
    if (Math.abs(dx) > 4) s.moved = true
    el.scrollLeft = s.startLeft - dx
  }
  const stop = () => {
    st.current.down = false
  }
  const onClickCapture = (e) => {
    if (st.current.moved) {
      e.preventDefault()
      e.stopPropagation()
      st.current.moved = false
    }
  }

  return { ref, bind: { onMouseDown, onMouseMove, onMouseUp: stop, onMouseLeave: stop, onClickCapture } }
}
