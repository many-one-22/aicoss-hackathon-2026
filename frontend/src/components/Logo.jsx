/* 남도식탁 로고 — 아이콘(초록 원 + 젓가락 X자) + 아래 워드마크(경기천년제목 Bold).
   로고 관련 마크업/색은 전부 이 파일에서만 관리한다. 헤더·스플래시 어디서든 재사용.

   사용 예:
     <Logo />                     // 아이콘 + 아래 '남도식탁' (기본, 세로 배치)
     <Logo iconOnly />            // 아이콘만
     <Logo size={36} />           // 아이콘 크기 조절(텍스트도 함께 커짐)
     <Logo row />                 // 가로 배치(아이콘 옆에 글자)

   색은 팔레트(tailwind.config.js)와 맞춤: 딥그린 #1E4D3A / 테라코타 #F2993E / 크림 #FAF7F2.
   워드마크 글씨체: 경기천년제목 Bold(= font-title, index.css의 @font-face). */

const GREEN = '#1E4D3A';
const TERRA = '#F2993E';
const CREAM = '#FAF7F2';

/* 아이콘만 그리는 SVG (viewBox 48×48) — 초록 원을 더 크게 확장하고 젓가락을 중앙에 배치 */
export function LogoMark({ size = 32, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      role="img"
      aria-label="남도식탁 로고"
      className={className}
    >
      {/* 48x48 영역에 맞게 반지름(r)을 24로 키운 원 */}
      <circle cx="24" cy="24" r="24" fill={GREEN} />
      {/* 젓가락 2짝 — X자 교차점 및 위치 중앙 정렬 */}
      <line
        x1="11"
        y1="33"
        x2="29"
        y2="15"
        stroke={CREAM}
        strokeWidth="4"
        strokeLinecap="round"
      />
      <line
        x1="37"
        y1="33"
        x2="19"
        y2="15"
        stroke={TERRA}
        strokeWidth="4"
        strokeLinecap="round"
      />
    </svg>
  );
}

/* 아이콘 + 워드마크. 기본은 세로 배치(아이콘 위 / 글자 아래). */
export default function Logo({
  size = 32,
  iconOnly = false,
  showText = true,
  row = false,
  className = '',
}) {
  const withText = showText && !iconOnly;
  return (
    <span
      className={`inline-flex ${row ? 'flex-row items-center gap-1.5' : 'flex-col items-center gap-0.5'} ${className}`}
    >
      <LogoMark size={size} />
      {withText && (
        <span
          className="font-bold leading-none text-green"
          style={{
            fontFamily: '"Gyeonggi Title", "Noto Serif KR", serif',
            // 가로형은 아이콘 옆 워드마크라 좀 더 크게, 세로형은 아이콘 아래 작은 글씨
            fontSize: Math.round(size * (row ? 0.6 : 0.3)),
          }}
        >
          남도식탁
        </span>
      )}
    </span>
  );
}
