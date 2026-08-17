/* 식당 이미지 소스 — 우선순위: ① data의 image 필드(직접 수집한 실사진)
   ② Google Places 실사진 조회 ③ 카테고리 스톡사진.
   ①이 있으면 그대로 쓰고 API 조회는 건너뛴다(호출량도 아낄 겸). */
import { useEffect, useState } from 'react'
import { fetchRestaurantPhoto } from '../lib/googlePlaces.js'
import { imageFor } from '../lib/categoryImage.js'

export function useRestaurantPhoto(r) {
  const [src, setSrc] = useState(() => (r ? imageFor(r) : null))

  useEffect(() => {
    if (!r) {
      setSrc(null)
      return
    }
    setSrc(imageFor(r))
    if (r.image) return // 직접 수집한 사진이 있으면 API 조회 불필요

    let live = true
    fetchRestaurantPhoto(r).then((url) => {
      if (live && url) setSrc(url)
    })
    return () => {
      live = false
    }
  }, [r?.id, r?.image])

  return src
}
