import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { PublicLayout } from '../components/layout/PublicLayout'
import { ProtectedRoute } from './ProtectedRoute'
import { PublicRoute } from './PublicRoute'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import { DashboardPage } from '../pages/DashboardPage'
import { PortfolioPage } from '../pages/PortfolioPage'
import { PortfolioDetailPage } from '../pages/PortfolioDetailPage'
import { AnalysisPage } from '../pages/AnalysisPage'
import { TechnicalPage } from '../pages/TechnicalPage'
import { OptionsFlowPage } from '../pages/OptionsFlowPage'
import { EarningsPage } from '../pages/EarningsPage'
import { WatchlistPage } from '../pages/WatchlistPage'
import { AlertsPage } from '../pages/AlertsPage'
import { MacroPage } from '../pages/MacroPage'
import { RiskPage } from '../pages/RiskPage'
import { SettingsPage } from '../pages/SettingsPage'
import { NotFoundPage } from '../pages/NotFoundPage'

export const router = createBrowserRouter([
  {
    element: <PublicRoute />,
    children: [
      {
        element: <PublicLayout />,
        children: [
          { path: '/login', element: <LoginPage /> },
          { path: '/register', element: <RegisterPage /> },
        ],
      },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <DashboardPage /> },
          { path: '/portfolios', element: <PortfolioPage /> },
          { path: '/portfolios/:id', element: <PortfolioDetailPage /> },
          { path: '/analysis', element: <AnalysisPage /> },
          { path: '/technical', element: <TechnicalPage /> },
          { path: '/options-flow', element: <OptionsFlowPage /> },
          { path: '/earnings', element: <EarningsPage /> },
          { path: '/watchlists', element: <WatchlistPage /> },
          { path: '/alerts', element: <AlertsPage /> },
          { path: '/macro', element: <MacroPage /> },
          { path: '/risk', element: <RiskPage /> },
          { path: '/settings', element: <SettingsPage /> },
        ],
      },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
])
