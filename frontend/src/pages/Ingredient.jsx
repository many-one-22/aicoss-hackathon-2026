/* ⑤ 산지·시세 — 시세품목 실데이터 + 기간 탭(3·6·12개월) 실측 추이 그래프 + 가까운 시장.
   모든 수치는 namdo.sqlite seasonality(KAMIS 실측) 기반. */
import { useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer, ReferenceLine, YAxis, Tooltip } from 'recharts'
import * as api from '../api/client.js'
import ChatFab from '../components/ChatFab.jsx'

const PERIODS = [
  { key: '3개월', n: 3 },
  { key: '6개월', n: 6 },
  { key: '1년', n: 12 },
]
const won = (n) => (n ?? 0).toLocaleString('ko-KR')

export default function Ingredient() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [ing, setIng] = useState(null)
  const [markets, setMarkets] = useState([])
  const [period, setPeriod] = useState('1년')

  useEffect(() => {
    api.getIngredient(id).then((res) => {
      setIng(res)
      setPeriod('1년')
    })
    api.detectLocation().then((loc) => api.getMarkets(loc).then((m) => setMarkets(m.slice(0, 3))))
  }, [id])

  const slice = useMemo(() => {
    if (!ing) return []
    const n = PERIODS.find((p) => p.key === period)?.n ?? 12
    return ing.trend.slice(-n)
  }, [ing, period])

  const chartData = useMemo(() => slice.map(([ym, v], i) => ({ i, v, ym })), [slice])
  const sliceAvg = useMemo(
    () => (slice.length ? Math.round(slice.reduce((a, [, v]) => a + v, 0) / slice.length) : 0),
    [slice],
  )
  // Prophet 6개월 시세 예측(있는 재료만) — 점선 차트용 데이터
  const forecastData = useMemo(
    () => (ing?.forecast ?? []).map((f, i) => ({ i, yhat: f.yhat, lo: f.lo, hi: f.hi, ym: f.ym })),
    [ing],
  )

  if (!ing) return <div className="p-10 text-center text-muted">불러오는 중…</div>

  const vs = ing.vsAvgPct
  const vsTxt = vs < 0 ? `연평균比 ${Math.abs(vs)}%↓` : vs > 0 ? `연평균比 ${vs}%↑` : '연평균 수준'

  return (
    <div>
      <header className="sticky top-0 z-10 flex h-14 items-center justify-center border-b border-line bg-white px-12 text-[16px] font-bold text-ink">
        <button onClick={() => navigate(-1)} aria-label="뒤로" className="absolute left-3 grid h-9 w-9 place-items-center">
          <ChevronLeft size={22} />
        </button>
        {ing.name} · 산지·시세
      </header>

      {/* 타이틀 + 연평균비 */}
      <div className="bg-cream px-5 pb-4 pt-4">
        <h1 className="font-serif text-[28px] font-black text-ink">{ing.name}</h1>
        <p className="mt-0.5 text-[13px] text-muted">
          {ing.region} 시세 · 성수기 {ing.season}
          {ing.inSeason && <span className="ml-2 rounded-full bg-terra/10 px-2 py-0.5 text-[11px] font-bold text-terra">지금 제철</span>}
        </p>
        <p className="mt-1.5 text-[15px] font-bold text-seasonink">
          {vsTxt} <span className="text-[12px] font-normal text-muted">KAMIS 실측 · 오늘 기준</span>
        </p>
      </div>

      {/* 시세 추이 + 기간 탭 */}
      <div className="px-5 pt-3">
        <div className="mb-2 flex items-center justify-between">
          <b className="text-[15px] font-bold text-ink">시세 추이</b>
          <div className="flex gap-1.5">
            {PERIODS.map((p) => (
              <button
                key={p.key}
                onClick={() => setPeriod(p.key)}
                className={`rounded-full px-3 py-1 text-[12px] font-semibold ${
                  p.key === period ? 'bg-green text-white' : 'border border-line bg-white text-muted'
                }`}
              >
                {p.key}
              </button>
            ))}
          </div>
        </div>
        <div className="h-[180px] w-full rounded-xl border border-tintgreen bg-gradient-to-b from-[#F4F8F5] to-cream p-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 8, left: 8, bottom: 6 }}>
              <YAxis hide domain={['dataMin - 800', 'dataMax + 800']} />
              <Tooltip
                formatter={(v) => [`${won(v)}원`, '시세']}
                labelFormatter={(i) => chartData[i]?.ym ?? ''}
                contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #EAE3D7' }}
              />
              <ReferenceLine y={sliceAvg} stroke="#A7A29A" strokeDasharray="3 4" strokeWidth={1.5} />
              <Line type="monotone" dataKey="v" stroke="#1E4D3A" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-1.5 text-[11px] text-muted-soft">실선 = 월별 실측 · 보조선 = 기간 평균 · 데이터 KAMIS(namdo.sqlite)</p>
      </div>

      {/* 🔮 6개월 시세 전망 — Prophet 예측(예측 있는 재료만 표시) */}
      {ing.forecast && ing.forecast.length > 0 && (
        <div className="px-5 pt-5">
          <div className="mb-2 flex items-center justify-between">
            <b className="text-[15px] font-bold text-ink">🔮 6개월 시세 전망</b>
            {ing.forecastMape != null && (
              <span className="rounded-full bg-green/10 px-2 py-0.5 text-[11px] font-bold text-green">
                예측 정확도 {Math.round(100 - ing.forecastMape)}%
              </span>
            )}
          </div>
          <div className="h-[150px] w-full rounded-xl border border-tintgreen bg-gradient-to-b from-[#F4F8F5] to-cream p-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecastData} margin={{ top: 10, right: 8, left: 8, bottom: 6 }}>
                <YAxis hide domain={['dataMin - 800', 'dataMax + 800']} />
                <Tooltip
                  formatter={(v) => [`${won(v)}원`, '예측']}
                  labelFormatter={(i) => forecastData[i]?.ym ?? ''}
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #EAE3D7' }}
                />
                <Line type="monotone" dataKey="yhat" stroke="#C4703A" strokeWidth={2.5} strokeDasharray="5 4" dot={{ r: 3, fill: '#C4703A' }} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-1.5 text-[11px] text-muted-soft">점선 = Prophet 예측 · 정확도는 과거 6개월 백테스트(MAPE) 기준</p>
        </div>
      )}

      {/* 통계 3종 */}
      <div className="grid grid-cols-3 gap-2.5 px-5 pt-4">
        <Stat label="오늘 시세" value={`${won(ing.current)}원`} sub={ing.unit ? `${ing.unit}당` : '소매가'} />
        <Stat label="연평균가" value={`${won(ing.avg)}원`} sub="12개월 평균" />
        <Stat
          label="전월 대비"
          value={`${ing.wowPct > 0 ? '+' : ''}${ing.wowPct}%`}
          sub={ing.wowPct < 0 ? '하락 추세' : ing.wowPct > 0 ? '상승 추세' : '보합'}
          accent={ing.wowPct <= 0 ? 'text-seasonink' : 'text-terra'}
        />
      </div>

      {/* 관련 향토음식 */}
      {ing.dishes.length > 0 && (
        <div className="px-5 pt-5">
          <b className="text-[15px] font-bold text-ink">이 재료가 들어가는 음식</b>
          <div className="mt-2 flex flex-wrap gap-2">
            {ing.dishes.map((dish) => (
              <span key={dish} className="rounded-full border border-line bg-white px-3 py-1.5 text-[13px] text-ink/80">
                {dish}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 가까운 전통시장 */}
      <div className="px-5 pb-24 pt-5">
        <b className="text-[15px] font-bold text-ink">가까운 전통시장</b>
        <div className="mt-2.5 flex flex-col gap-2.5">
          {markets.map((m) => (
            <Link key={m.id} to="/market" className="rounded-2xl border border-line bg-white p-3.5">
              <b className="block text-[15px] font-bold text-ink">{m.name}</b>
              <span className="text-[12px] text-muted">
                {m.sido} {m.city} · {(m.items || []).slice(0, 3).join('·')}
                {m._distKm != null ? ` · ${m._distKm}km` : ''}
              </span>
            </Link>
          ))}
          <div className="flex items-center justify-between rounded-xl border border-dashed border-[#CFC7B7] bg-cream px-4 py-3">
            <span className="text-[13px] text-muted">제철 · 저가 알림 받기</span>
            <span className="text-[13px] font-bold text-terra">설정 →</span>
          </div>
        </div>
      </div>

      <ChatFab />
    </div>
  )
}

function Stat({ label, value, sub, accent = 'text-ink' }) {
  return (
    <div className="rounded-xl border border-line bg-white px-2 py-3 text-center">
      <span className="block text-[11px] text-muted-soft">{label}</span>
      <b className={`mt-0.5 block text-[17px] font-extrabold ${accent}`}>{value}</b>
      <span className="block text-[10px] text-muted-soft">{sub}</span>
    </div>
  )
}
