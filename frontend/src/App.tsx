import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider, useApp } from './hooks/AppContext'
import { FilterProvider } from './hooks/FilterContext'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import ToastContainer from './components/Toast'

import UploadPage from './pages/UploadPage'
import DataPreparationPage from './pages/DataPreparationPage'
import DashboardPage from './pages/DashboardPage'
import SalesPage from './pages/SalesPage'
import CustomerPage from './pages/CustomerPage'
import RestaurantPage from './pages/RestaurantPage'
import DeliveryPage from './pages/DeliveryPage'
import ForecastPage from './pages/ForecastPage'
import ChurnPage from './pages/ChurnPage'
import RecommendationsPage from './pages/RecommendationsPage'
import DatasetManagerPage from './pages/DatasetManagerPage'

function RequireDataset({ children }: { children: React.ReactNode }) {
  const { currentDataset } = useApp()
  if (!currentDataset) return <Navigate to="/upload" replace />
  return <>{children}</>
}

function Shell() {
  return (
    <div className="flex">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <TopBar />
        <main className="p-6 max-w-[1600px] mx-auto">
          <Routes>
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/" element={<RequireDataset><DashboardPage /></RequireDataset>} />
            <Route path="/data-preparation" element={<RequireDataset><DataPreparationPage /></RequireDataset>} />
            <Route path="/sales" element={<RequireDataset><SalesPage /></RequireDataset>} />
            <Route path="/customers" element={<RequireDataset><CustomerPage /></RequireDataset>} />
            <Route path="/restaurants" element={<RequireDataset><RestaurantPage /></RequireDataset>} />
            <Route path="/delivery" element={<RequireDataset><DeliveryPage /></RequireDataset>} />
            <Route path="/forecast" element={<RequireDataset><ForecastPage /></RequireDataset>} />
            <Route path="/churn" element={<RequireDataset><ChurnPage /></RequireDataset>} />
            <Route path="/recommendations" element={<RequireDataset><RecommendationsPage /></RequireDataset>} />
            <Route path="/datasets" element={<DatasetManagerPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
      <ToastContainer />
    </div>
  )
}

export default function App() {
  return (
    <AppProvider>
      <FilterProvider>
        <BrowserRouter>
          <Shell />
        </BrowserRouter>
      </FilterProvider>
    </AppProvider>
  )
}
