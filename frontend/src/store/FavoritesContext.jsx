/* 찜(즐겨찾기) 전역 상태 — localStorage 영속. 화면 어디서나 useFavorites() 로 사용.
   추후 로그인/서버 동기화 시, load/persist 부분만 API 호출로 바꾸면 된다. */
import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const KEY = 'namdo:favorites'
const FavoritesContext = createContext(null)

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || []
  } catch {
    return []
  }
}

export function FavoritesProvider({ children }) {
  const [ids, setIds] = useState(load)

  useEffect(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(ids))
    } catch {
      /* storage 접근 불가 시 무시 */
    }
  }, [ids])

  const isFavorite = useCallback((id) => ids.includes(Number(id)), [ids])

  const toggleFavorite = useCallback((id) => {
    const n = Number(id)
    let added = false
    setIds((prev) => {
      if (prev.includes(n)) return prev.filter((x) => x !== n)
      added = true
      return [n, ...prev]
    })
    return added
  }, [])

  return (
    <FavoritesContext.Provider value={{ ids, isFavorite, toggleFavorite }}>
      {children}
    </FavoritesContext.Provider>
  )
}

export function useFavorites() {
  const ctx = useContext(FavoritesContext)
  if (!ctx) throw new Error('useFavorites must be used within FavoritesProvider')
  return ctx
}
