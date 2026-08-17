import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Home from './pages/Home.jsx'
import PlaceDetail from './pages/PlaceDetail.jsx'
import SearchEmpty from './pages/SearchEmpty.jsx'
import Chat from './pages/Chat.jsx'
import Ingredient from './pages/Ingredient.jsx'
import Market from './pages/Market.jsx'
import Favorites from './pages/Favorites.jsx'
import Seasonal from './pages/Seasonal.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/place/:id" element={<PlaceDetail />} />
        <Route path="/search" element={<SearchEmpty />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/ingredient/:id" element={<Ingredient />} />
        <Route path="/market" element={<Market />} />
        <Route path="/seasonal" element={<Seasonal />} />
        <Route path="/favorites" element={<Favorites />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
