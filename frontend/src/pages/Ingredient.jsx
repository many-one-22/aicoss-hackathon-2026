/* ⑤ 모바일 산지·시세 — 식재료 동적 데이터 + 기간 탭(4주/3개월/1년) 그래프 + 관련 시장 */
import { useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer, ReferenceLine, YAxis, Tooltip } from 'recharts'
import * as api from '../api/client.js'
import ChatFab from '../components/ChatFab.jsx'

const PERIODS = ['4주', '3개월', '1년']
const won = (n) => n.toLocaleString('ko-KR')

export default function Ingredient() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [ing, setIng] = useState(null)
  const [markets, setMarkets] = useState([])
  const [period, setPeriod] = useState('4주')

  useEffect(() => {
    api.getIngredient(id).then((res) => {
      setIng(res)
      setPeriod('4주')
    })
    api.getMarkets().then(setMarkets)
  }, [id])

  const d = ing?.ranges[period]
  const chartData = useMemo(() => (d ? d.series.map((v, i) => ({ i, v })) : []), [d])

  if (!ing || !d) return <div className="p-10 text-center text-muted">불러오는 중…</div>

  const vs = d.vsAvgPct
  const vsTxt = vs < 0 ? `평년比 ${Math.abs(vs)}%↓` : vs > 0 ? `평년比 ${vs}%↑` : '평년 수준'
  const relatedMarkets = markets.filter((m) => (ing.markets || []).includes(m.name))

  return (
    <div>
      <header className="sticky top-0 z-10 flex h-14 items-center justify-center border-b border-line bg-white px-12 text-[16px] font-bold text-ink">
        <button onClick={() => navigate(-1)} aria-label="뒤로" className="absolute left-3 grid h-9 w-9 place-items-center">
          <ChevronLeft size={22} />
        </button>
        {ing.name} · 산지·시세
      </header>

      {/* 타이틀 + 평년비 */}
      <div className="bg-cream px-5 pb-4 pt-4">
        <h1 className="font-serif text-[28px] font-black text-ink">{ing.name}</h1>
        <p className="mt-0.5 text-[13px] text-muted">산지 {ing.origin} · 제철 {ing.season}</p>
        <p className="mt-1.5 text-[15px] font-bold text-seasonink">
          {vsTxt} <span className="text-[12px] font-normal text-muted">KAMIS 소매가 · 오늘 기준</span>
        </p>
      </div>

      {/* 시세 추이 + 기간 탭 */}
      <div className="px-5 pt-3">
        <div className="mb-2 flex items-center justify-between">
          <b className="text-[15px] font-bold text-ink">시세 추이</b>
          <div className="flex gap-1.5">
            {PERIODS.map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`rounded-full px-3 py-1 text-[12px] font-semibold ${
                  p === period ? 'bg-green text-white' : 'border border-line bg-white text-muted'
                }`}
              >
                {p}
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
                labelFormatter={() => ''}
                contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #EAE3D7' }}
              />
              <ReferenceLine y={d.avg} stroke="#A7A29A" strokeDasharray="3 4" strokeWidth={1.5} />
              <Line type="monotone" dataKey="v" stroke="#1E4D3A" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-1.5 text-[11px] text-muted-soft">실선 = 실측 · 보조선 = 평년 동기 · 데이터 KAMIS(데모 시드값)</p>
      </div>

      {/* 통계 3종 */}
      <div className="grid grid-cols-3 gap-2.5 px-5 pt-4">
        <Stat label="오늘 시세" value={`${won(d.current)}원`} sub="kg당 소매가" />
        <Stat label="평년가" value={`${won(d.avg)}원`} sub="동기간 평균" />
        <Stat
          label="전월 대비"
          value={`${d.wowPct > 0 ? '+' : ''}${d.wowPct}%`}
          sub={d.wowPct < 0 ? '하락 추세' : d.wowPct > 0 ? '상승 추세' : '보합'}
          accent={d.wowPct < 0 ? 'text-seasonink' : 'text-terra'}
        />
      </div>

      {/* 향토음식 */}
      <div className="px-5 pt-5">
        <b className="text-[15px] font-bold text-ink">이 식재료로 만드는 향토음식</b>
        <div className="mt-2 flex flex-wrap gap-2">
          {ing.dishes.map((dish) => (
            <span key={dish} className="rounded-full border border-line bg-white px-3 py-1.5 text-[13px] text-ink/80">
              {dish}
            </span>
          ))}
        </div>
      </div>

      {/* 살 수 있는 전통시장 */}
      <div className="px-5 pb-24 pt-5">
        <b className="text-[15px] font-bold text-ink">살 수 있는 전통시장</b>
        <div className="mt-2 flex h-[120px] items-center justify-center rounded-xl bg-season text-[12px] text-muted-soft">
          지도: 산지 · 취급 시장 핀
        </div>
        <div className="mt-2.5 flex flex-col gap-2.5">
          {relatedMarkets.map((m) => (
            <Link key={m.id} to="/market" className="rounded-2xl border border-line bg-white p-3.5">
              <b className="block text-[15px] font-bold text-ink">{m.name}</b>
              <span className="text-[12px] text-muted">
                {m.city} · 점포 {m.stores} · {(m.items || []).slice(0, 2).join('·')}
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
