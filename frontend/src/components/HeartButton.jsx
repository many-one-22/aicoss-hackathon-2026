/* 찜하기 하트 버튼 — 채워짐/빈 상태 토글 + 토스트. 어디서나 재사용. */
import { Heart } from 'lucide-react'
import { useFavorites } from '../store/FavoritesContext.jsx'
import { useToast } from './Toast.jsx'

export default function HeartButton({ id, size = 24, className = '', stop = true }) {
  const { isFavorite, toggleFavorite } = useFavorites()
  const toast = useToast()
  const active = isFavorite(id)

  function onClick(e) {
    if (stop) {
      e.preventDefault()
      e.stopPropagation()
    }
    const added = toggleFavorite(id)
    toast(added ? '찜에 담았어요 ♥' : '찜에서 뺐어요')
  }

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      aria-label={active ? '찜 해제' : '찜하기'}
      className={`grid place-items-center transition-transform active:scale-90 ${className}`}
    >
      <Heart
        size={size}
        strokeWidth={2}
        className="text-terra"
        fill={active ? '#C85227' : 'transparent'}
      />
    </button>
  )
}
