/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // 브랜드 (프롬프트 지정): 딥그린 / 오렌지·브라운 / 크림 아이보리
        green: { DEFAULT: '#1E4D3A', dark: '#163A2C', 900: '#102A20' },
        terra: { DEFAULT: '#F2993E', dark: '#D97F28', tint: '#FDF0E1' },
        cream: '#FAF7F2',
        ink: '#1C1F1D',
        muted: { DEFAULT: '#6B6F6A', soft: '#8A8478' },
        line: '#EAE3D7',
        tintgreen: '#E7EFE9',
        season: '#F1F5ED',
        seasonink: '#337347',
        allergy: '#FEEEEA',
        allergyink: '#80472E',
        thumb: '#D8CFBE',
      },
      fontFamily: {
        sans: ['"Gothic A1"', 'system-ui', 'sans-serif'],
        serif: ['"Noto Serif KR"', 'serif'],
        title: ['"Gyeonggi Title"', '"Noto Serif KR"', 'serif'], // 로고 워드마크(경기천년제목 Bold)
      },
      maxWidth: { phone: '430px' },
      boxShadow: {
        card: '0 8px 24px -16px rgba(28,31,29,.3)',
        pop: '0 12px 32px -12px rgba(28,31,29,.22)',
      },
    },
  },
  plugins: [],
}
