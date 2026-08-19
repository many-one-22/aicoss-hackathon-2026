/* ① 모바일 홈 — 위치 자동감지 · 오늘의 추천 · 찜 기반 추천 · 이번 주 제철(가로 스크롤) */
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MapPin, Heart } from 'lucide-react';
import * as api from '../api/client.js';
import { useFavorites } from '../store/FavoritesContext.jsx';
import { recommendByFavorites } from '../lib/derive.js';
import { imageForIngredient } from '../lib/categoryImage.js';
import RestaurantCard from '../components/RestaurantCard.jsx';
import PlaceholderImage from '../components/PlaceholderImage.jsx';
import Logo from '../components/Logo.jsx';
import { useDragScroll } from '../hooks/useDragScroll.js';
import { useRestaurantPhoto } from '../hooks/useRestaurantPhoto.js';

/* 받침 유무에 따라 주격조사를 붙인다. 예: 감자 → '감자가', 전복 → '전복이'. */
function withSubjectParticle(word) {
  const last = (word || '').trim().slice(-1);
  const code = last.charCodeAt(0);
  // 한글 음절이 아니면(숫자·영문 등) 안전하게 '이(가)'
  if (!(code >= 0xac00 && code <= 0xd7a3)) return `${word}이(가)`;
  const hasFinal = (code - 0xac00) % 28 !== 0;
  return `${word}${hasFinal ? '이' : '가'}`;
}

/* 이 시장의 네이버 '장소 화면'(길찾기 버튼 포함)을 연다. 시장명+지역으로 검색해 동명 시장 혼동 방지. */
function openNaverMarket(m) {
  const query = [m.name, m.sido, m.city].filter(Boolean).join(' ');
  window.open(
    `https://map.naver.com/p/search/${encodeURIComponent(query)}`,
    '_blank',
    'noopener,noreferrer',
  );
}

export default function Home() {
  const navigate = useNavigate();
  const { ids } = useFavorites();
  const seasonalDrag = useDragScroll();
  const [loc, setLoc] = useState({
    city: '광주',
    region: '광주',
    label: '광주 · 자동감지',
  });
  const [todayItem, setTodayItem] = useState(null);
  const [all, setAll] = useState([]);

  useEffect(() => {
    api.detectLocation().then(setLoc);
    api.getRestaurants().then(setAll);
  }, []);

  useEffect(() => {
    if (!loc.city) return;
    // 오늘의 제철은 재호출(위치 변경/리로드)마다 저렴한 것 중 랜덤으로 새로 뽑힌다.
    // 그 재료를 메뉴로 쓰는 근처 식당 목록(restaurants)도 함께 온다.
    api.getTodaySeasonal(loc).then(setTodayItem);
  }, [loc.city, loc.region, loc.lat, loc.lng]);

  // 로딩(데이터/찜 변경)마다 한 번만 계산 — 재렌더로 깜빡이지 않게 메모이즈
  const favRestaurants = useMemo(() => all.filter((r) => ids.includes(r.id)), [all, ids]);
  const recos = useMemo(
    () => recommendByFavorites(favRestaurants, all, 3, loc),
    [favRestaurants, all, loc],
  );

  return (
    <div>
      {/* 헤더 */}
      <header className="sticky top-0 z-10 flex h-14 items-center gap-2 border-b border-line bg-cream px-5">
        <Logo row size={30} />
        <span className="ml-auto flex items-center gap-1 text-[12px] text-muted">
          <MapPin size={13} className="text-terra" fill="#C85227" />
          <b className="font-bold text-terra">{loc.city}</b>
        </span>
        <Link
          to="/favorites"
          aria-label="찜 목록"
          className="relative ml-1 grid h-9 w-9 place-items-center"
        >
          <Heart
            size={22}
            className="text-[#C85227]"
            fill={ids.length ? '#C85227' : 'transparent'}
          />
          {ids.length > 0 && (
            <span className="absolute right-0 top-0 grid h-4 min-w-4 place-items-center rounded-full bg-[#C85227] px-1 text-[10px] font-bold text-white">
              {ids.length}
            </span>
          )}
        </Link>
      </header>

      {/* 검색 프롬프트 */}
      <div className="relative mx-5 mt-4 rounded-2xl border border-line bg-white px-4 py-3.5 text-[14px] text-ink">
        지금 {loc.city} 계시죠? 오늘은 이 집 어때요?
        <span className="absolute -bottom-[6px] right-4 h-3 w-3 rotate-45 border-b border-r border-line bg-white" />
      </div>

      {/* 리드 */}
      <div className="px-5 pb-1 pt-4">
        <h1 className="font-brand text-[18px] font-extrabold tracking-tight text-ink">
          즐겨찾기와 저장된 장소로 취향 탐색
        </h1>
        <p className="mt-1 text-[11px] text-muted">
          위치와 다녀간 기록을 보고 쓸수록 더 잘 맞는 곳을 골라드려요
        </p>
      </div>

      {/* 오늘의 제철 — 박스 클릭 시 시세 상세, '시장 가는 길'은 네이버 지도 길찾기 */}
      {todayItem?.item && (
        <div
          onClick={() => navigate(`/ingredient/${todayItem.item.id}`)}
          className="mx-5 mt-3 block cursor-pointer overflow-hidden rounded-2xl border border-line bg-white shadow-card active:bg-cream"
        >
          <div className="relative h-[150px]">
            <PlaceholderImage
              src={imageForIngredient(todayItem.item.item)}
              alt={todayItem.item.item}
              label={todayItem.item.item}
              className="h-full w-full text-[13px]"
            />
            <span className="absolute left-3.5 top-3.5 rounded-full bg-terra px-2.5 py-1 text-[12px] font-bold text-white">
              오늘의 제철
            </span>
          </div>
          <div className="flex flex-col gap-1.5 px-4 pb-4 pt-3.5">
            <h3 className="font-brand text-[20px] font-extrabold text-ink">
              {todayItem.item.item}
            </h3>
            <span className="text-[13px] text-muted">
              {todayItem.item.level === '저렴' && <b className="text-terra">지금 저렴 · </b>}
              {todayItem.item.current != null
                ? `${Math.round(todayItem.item.current).toLocaleString()}원/${todayItem.item.unit}`
                : todayItem.item.region}
            </span>
            {todayItem.market && (
              <span className="text-[12px] text-muted-soft">
                {todayItem.market.name}
                {todayItem.market._distKm != null && ` · ${todayItem.market._distKm}km`}
              </span>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (todayItem.market) openNaverMarket(todayItem.market);
              }}
              className="mt-1 rounded-xl bg-[#D5EBDE] py-3 text-center text-[14px] font-extrabold text-olive"
            >
              시장 가는 길
            </button>
          </div>
        </div>
      )}

      {/* 찜 기반 추천 / 안내 */}
      {recos.length > 0 ? (
        <>
          <div className="mx-5 mt-4 rounded-2xl bg-green px-4 py-3.5">
            <b className="block text-[15px] font-bold text-white">
              찜한 {ids.length}곳 취향으로 골랐어요
            </b>
            <span className="text-[12px] text-white/70">
              비슷한 향토 키워드로 다음 장소를 추천해요
            </span>
          </div>
          <div className="flex flex-col gap-2.5 px-5 pt-2.5">
            {recos.map(({ r, why }) => (
              <RestaurantCard key={r.id} restaurant={r} why={why} />
            ))}
          </div>
        </>
      ) : (
        <div className="mx-5 mt-4 flex items-center gap-3 rounded-2xl border border-tintgreen bg-tintgreen/50 px-4 py-3.5">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white">
            <Heart size={17} className="text-terra" fill="#F2993E" />
          </span>
          <div className="min-w-0">
            <b className="block text-[14px] font-bold text-ink">
              마음에 드는 곳에 하트를 눌러보세요
            </b>
            <span className="text-[12px] text-muted">
              찜한 장소가 쌓일수록 취향에 맞는 추천을 드려요
            </span>
          </div>
        </div>
      )}

      {/* 오늘의 제철 재료를 메뉴로 쓰는 근처 식당 (드래그 가로 스크롤) */}
      {todayItem?.item && todayItem.restaurants?.length > 0 && (
        <>
          <div className="flex items-end justify-between px-5 pb-1.5 pt-5">
            <div>
              <span className="text-[12px] text-muted-soft">
                {loc.city} 기준 · 밀어서 더 보기
              </span>
              <h2 className="mt-0.5 font-brand text-[19px] font-extrabold text-ink">
                {withSubjectParticle(todayItem.item.item)} 들어가는 식당
              </h2>
            </div>
            <Link to="/market" className="shrink-0 text-[12px] font-semibold text-terra">
              음식점 보기 →
            </Link>
          </div>
          <div
            ref={seasonalDrag.ref}
            {...seasonalDrag.bind}
            className="flex cursor-grab gap-3 select-none overflow-x-auto overflow-y-hidden px-5 pb-3 active:cursor-grabbing"
          >
            {todayItem.restaurants.map((r) => (
              <SeasonalRestaurantCard key={r.id} r={r} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/* 오늘의 제철 재료 카드 아래 가로 캐러셀용 식당 미니카드 — 너비 150px 고정, 위 제철카드와 같은 결. */
function SeasonalRestaurantCard({ r }) {
  const photoSrc = useRestaurantPhoto(r);
  return (
    <Link to={`/place/${r.id}`} className="w-[150px] shrink-0">
      <PlaceholderImage src={photoSrc} alt={r.name} className="h-24 w-full rounded-xl text-[11px]" />
      <b className="mt-2 block truncate font-brand text-[14px] font-bold text-ink">{r.name}</b>
      <span className="block truncate text-[12px] text-muted">
        {r.city} · {r.key}
        {r._distKm != null && <span className="font-semibold text-terra"> · {r._distKm}km</span>}
      </span>
    </Link>
  );
}
