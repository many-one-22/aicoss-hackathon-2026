/* API 클라이언트 — 모든 화면은 이 모듈만 호출한다.
   데이터는 namdo.sqlite 에서 추출한 실데이터 JSON(src/data/*.real.json)을 사용한다.
   위치는 브라우저 Geolocation 좌표를 광주·전남 도시로 오프라인 매핑(geo.js)해 얻고,
   식당/시장/추천/제철을 모두 '현재 위치' 기준으로 필터·정렬한다. */
import { RESTAURANTS } from '../data/restaurants.js';
import { SEASONAL, DISH_TO_ITEM } from '../data/seasonal.js';
import { MARKETS } from '../data/markets.js';
import { CITIES, nearestCity, cityByName, distanceKm } from '../data/geo.js';
import {
  allergyInfo,
  seasonalFor,
  searchRestaurants,
  favoriteProfile,
} from '../lib/derive.js';
import { retrieveLocal, enrich } from '../lib/chatbot.js';
import { getVisits } from '../store/visits.js';

const delay = (ms = 200) => new Promise((res) => setTimeout(res, ms));
const LEVEL_ORDER = { 저렴: 0, 평균: 1, 비쌈: 2 };

/* loc 에서 정렬 기준 좌표를 얻는다(없으면 null). */
function originOf(loc = {}) {
  if (loc.lat != null && loc.lng != null) return { lat: loc.lat, lng: loc.lng };
  const c = loc.city
    ? cityByName(loc.city)
    : loc.region === '광주'
      ? cityByName('광주')
      : null;
  return c ? { lat: c.lat, lng: c.lng } : null;
}
/* 좌표가 있는 항목을 사용자와 가까운 순으로 정렬(사본 반환). */
function byDistance(list, origin) {
  if (!origin) return list.slice();
  return list
    .map((x) => ({
      x,
      d: x.lat != null && x.lng != null ? distanceKm(origin, x) : Infinity,
    }))
    .sort((a, b) => a.d - b.d)
    .map((o) => ({ ...o.x, _distKm: Math.round(o.d) }));
}

export async function getRestaurants() {
  await delay();
  return RESTAURANTS;
}

export async function getRestaurant(id) {
  await delay(120);
  return RESTAURANTS.find((r) => r.id === Number(id)) || null;
}

/* 현재 위치에서 가까운 순 식당(같은 권역 우선). 각 항목에 _distKm 포함. */
export async function getRestaurantsNear(loc = {}, { region = true } = {}) {
  await delay(160);
  const origin = originOf(loc);
  const reg = typeof loc === 'string' ? null : loc.region;
  const pool =
    region && reg ? RESTAURANTS.filter((r) => r.region === reg) : RESTAURANTS;
  return byDistance(pool.length ? pool : RESTAURANTS, origin);
}

/* ── 위치 자동 감지 ── */
function locFromCity(c, auto = true) {
  return {
    city: c.name,
    region: c.region,
    lat: c.lat,
    lng: c.lng,
    label: `${c.name} · ${auto ? '자동감지' : '선택'}`,
  };
}
export async function detectLocation() {
  const fallback = locFromCity(cityByName('광주'));
  if (!('geolocation' in navigator)) return fallback;
  try {
    const pos = await new Promise((resolve, reject) =>
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        timeout: 4000,
        maximumAge: 600000,
      }),
    );
    const { latitude, longitude } = pos.coords;
    const c = nearestCity(latitude, longitude);
    return {
      city: c.name,
      region: c.region,
      lat: latitude,
      lng: longitude,
      label: `${c.name} · 자동감지`,
    };
  } catch {
    return fallback;
  }
}
export function locationChoices() {
  return CITIES.map((c) => c.name);
}
export function locationByName(name) {
  const c = cityByName(name);
  return c ? locFromCity(c, false) : null;
}

/* ── 제철 시세 (실데이터) ──
   현재 월에 성수기(peak_months)인 품목만. 광주 사용자는 광주 시세 우선 + 전국 보완.
   정렬: 광주 지역 우선 → 구매적기(저렴) → 평년比 낮은 순. */
export async function getSeasonal(ctx = {}) {
  await delay(120);
  const month = ctx.month || new Date().getMonth() + 1;
  const isGwangju = ctx.region === '광주';
  const inMonth = (s) => s.peak_months.includes(month);

  let list;
  if (isGwangju) {
    const gj = SEASONAL.filter((s) => s.region === '광주' && inMonth(s));
    const names = new Set(gj.map((s) => s.item));
    const nat = SEASONAL.filter(
      (s) => s.region === '전국' && inMonth(s) && !names.has(s.item),
    );
    list = [...gj, ...nat];
  } else {
    list = SEASONAL.filter((s) => s.region === '전국' && inMonth(s));
  }
  return list
    .map((s) => ({ ...s, month, _regionRank: s.region === '광주' ? 0 : 1 }))
    .sort((a, b) => {
      if (a._regionRank !== b._regionRank) return a._regionRank - b._regionRank;
      const lv = (LEVEL_ORDER[a.level] ?? 1) - (LEVEL_ORDER[b.level] ?? 1);
      if (lv !== 0) return lv;
      return a.vsAvgPct - b.vsAvgPct;
    });
}

export async function getMarkets(loc) {
  await delay(160);
  return loc ? byDistance(MARKETS, originOf(loc)) : MARKETS;
}

/* 시세품목이 들어가는 향토음식(메뉴 키워드) — ingredient_map 역방향. */
function dishesForItem(item) {
  const ks = Object.entries(DISH_TO_ITEM)
    .filter(([, v]) => v === item)
    .map(([k]) => k);
  return [...new Set([item, ...ks])].slice(0, 6);
}

/* ── 산지·시세 상세 (실데이터 12개월 추이) ── */
export async function getIngredient(id) {
  await delay(120);
  const s = SEASONAL.find((x) => x.id === id);
  if (!s) return null;
  const monthNames = {
    1: '1월',
    2: '2월',
    3: '3월',
    4: '4월',
    5: '5월',
    6: '6월',
    7: '7월',
    8: '8월',
    9: '9월',
    10: '10월',
    11: '11월',
    12: '12월',
  };
  return {
    id: s.id,
    name: s.item,
    region: s.region,
    unit: s.unit,
    level: s.level,
    season: s.peak_months.map((m) => monthNames[m]).join('·'),
    current: s.current,
    avg: s.avg12,
    vsAvgPct: s.vsAvgPct,
    wowPct: s.wowPct,
    dishes: dishesForItem(s.item),
    trend: s.trend, // [[ 'YYYY-MM', price ], ...]
    forecast: s.forecast ?? null, // [{ym,yhat,lo,hi}] Prophet 6개월 예측 (있는 재료만)
    forecastMape: s.forecastMape ?? null, // 백테스트 오차율(%) — 정확도 표시용
    inSeason: s.peak_months.includes(new Date().getMonth() + 1),
  };
}

/* ── 오늘의 추천 — 현재 위치 근처 + 방문 취향 기반 ──
   가까운 후보군에서, 방문기록(다녀간 곳)의 음식유형·태그와 가까운 곳을 우선한다.
   방문기록이 없으면 기존처럼 무작위(재호출 때마다 바뀜). */
export async function getTodayRecommendation(loc = {}) {
  await delay(180);
  const origin = originOf(loc);
  const region = typeof loc === 'string' ? null : loc.region;
  const pool = region
    ? RESTAURANTS.filter((r) => r.region === region)
    : RESTAURANTS;
  const base = pool.length ? pool : RESTAURANTS;
  const near = byDistance(base, origin).slice(0, 12); // 사용자와 가장 가까운 12곳
  const local = near.filter((r) => (r.local_score || 0) >= 1); // 그 안에서 향토색 있는 곳 우선
  const cands = local.length >= 4 ? local : near;

  // 방문 취향(다녀간 곳의 음식유형·태그)과 가까운 후보 우선
  const visits = getVisits();
  let pick;
  if (visits.length) {
    const p = favoriteProfile(visits);
    const seen = new Set(visits.map((v) => v.id));
    const scored = cands
      .filter((r) => !seen.has(r.id)) // 이미 다녀간 곳은 제외
      .map((r) => {
        let s = 0;
        (r.tags || []).forEach((t) => {
          if (p.tagFreq[t]) s += 2 * p.tagFreq[t];
        });
        if (r.key && p.keyFreq[r.key]) s += 1.5 * p.keyFreq[r.key];
        return { r, s };
      })
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s);
    // 상위 취향매칭 중 무작위(3곳 이내)
    if (scored.length)
      pick = scored[Math.floor(Math.random() * Math.min(3, scored.length))].r;
  }
  if (!pick) pick = cands[Math.floor(Math.random() * cands.length)] || base[0]; // 기록 없으면 기존 무작위

  return {
    restaurant: pick,
    allergy: allergyInfo(pick),
    seasonal: seasonalFor(pick, loc),
  };
}

export async function search(query, loc) {
  try {
    const res = await fetch('http://localhost:8000/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, region: loc?.region, top_k: 10 }),
    });
    if (!res.ok) throw new Error('backend error');
    const data = await res.json();

    const byId = new Map(RESTAURANTS.map((r) => [String(r.poi_id), r]));
    const hits = data.results.map((item) => byId.get(String(item.restaurant_id))).filter(Boolean);

    return loc ? byDistance(hits, originOf(loc)) : hits;
  } catch (e) {
    await delay(220);
    const hits = searchRestaurants(query, RESTAURANTS);
    return loc ? byDistance(hits, originOf(loc)) : hits;
  }
}

/* ── 챗봇 — minseo AI 추천 엔진(retrieve+recommend) 이식본 ──
   자연어 → 필터 파싱 → 하드필터 → 랭킹(질의·향토색·근접) → 시세·시장 보강. */
/* KoSBERT 챗봇 백엔드 (minseo/api_chat.py). 기본 로컬 8001, 환경변수(VITE_CHAT_API)로 교체 가능. */
const CHAT_API = import.meta.env?.VITE_CHAT_API || 'http://localhost:8001';

/* 백엔드 카드 → 프론트 restaurant 객체.
   번들(restaurants.real.json)에 같은 식당(poi_id)이 있으면 그 정수 id 객체를 써서 상세 라우팅을
   살리고, 없으면 백엔드 카드를 그대로 쓴다(챗봇 카드에서 상세로 객체를 넘겨 렌더). 위치 있으면 거리 계산. */
function adoptCard(card, origin) {
  const inBundle = card.poi_id
    ? RESTAURANTS.find((r) => r.poi_id === card.poi_id)
    : null;
  const base = inBundle || card;
  if (origin && base.lat != null)
    return { ...base, _distKm: Math.round(distanceKm(origin, base)) };
  return { ...base };
}

/* KoSBERT 백엔드 /chat 호출. 미기동·네트워크 실패·타임아웃이면 null 반환(→ 로컬 폴백). */
async function fetchKosbert(text, region) {
  const qs = new URLSearchParams({ q: text, top_n: '4' });
  if (region) qs.set('region', region);
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 8000);
  try {
    const resp = await fetch(`${CHAT_API}/chat?${qs}`, { signal: ctrl.signal });
    return resp.ok ? await resp.json() : null;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

export async function chatReply(text, loc = {}) {
  const cityLabel = loc.city || '현재 위치';
  const region = typeof loc === 'string' ? null : loc.region;
  const origin = originOf(loc);

  // 1) KoSBERT 의미검색(백엔드) 우선 — 전체 식당 대상 '진짜 의미검색'
  const data = await fetchKosbert(text, region);
  if (data) {
    const results = (data.results || []).map((c) => adoptCard(c, origin));
    if (results.length) {
      const top = results[0];
      const bits = enrich(top, loc);
      const messages = [
        {
          who: 'bot',
          text: `${cityLabel} 근처 향토음식점으로 이곳을 추천해요. (KoSBERT 의미검색)`,
        },
        { who: 'card', restaurant: top },
      ];
      if (bits.length)
        messages.push({
          who: 'bot',
          text: `👍 ${top.name} — ${bits.join(' · ')}`,
        });
      return { messages, hits: results, engine: 'KoSBERT' };
    }
  }

  // 2) 폴백: 백엔드 미기동/결과 없음 → 로컬 토큰매칭(번들 3,500곳)
  await delay(300);
  const { filters, fallback, results } = retrieveLocal(text, loc, 4);
  if (!results.length) {
    return {
      messages: [
        {
          who: 'bot',
          text: `아직 ${cityLabel} 근처에서 딱 맞는 곳을 못 찾았어요. 메뉴(예: 꼬막·게장·백반)나 상황(예: 가족·해장)을 함께 말해주시면 더 정확해집니다.`,
        },
      ],
      hits: [],
    };
  }

  // 인식한 조건 요약(재료/음식유형/건강)
  const chips = [
    ...filters.ingredients,
    ...filters.dishType,
    ...filters.health,
  ];
  const cond = chips.length ? `‘${chips.slice(0, 3).join(', ')}’ ` : '';
  const top = results[0]; // 질문당 딱 한 곳만 추천
  const bits = enrich(top, loc);

  const messages = [
    {
      who: 'bot',
      text: fallback
        ? `${cityLabel} 근처엔 딱 맞는 곳이 적어 조건을 넓혀 골랐어요. 가장 가까운 이곳을 추천해요.`
        : `${cityLabel} 근처 ${cond}향토음식점으로 이곳을 추천해요.`,
    },
    { who: 'card', restaurant: top },
  ];
  if (bits.length)
    messages.push({ who: 'bot', text: `👍 ${top.name} — ${bits.join(' · ')}` });
  return { messages, hits: results };
}
