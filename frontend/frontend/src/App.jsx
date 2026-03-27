import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import CursorGlow from './components/CursorGlow'

// Pages
import Landing    from './pages/Landing'
import Login      from './pages/Login'
import SignUp     from './pages/SignUp'
import Onboarding from './pages/Onboarding'
import Dashboard  from './pages/Dashboard'
import FIREPathPlanner    from './pages/FIRE_Path_Planner'
import MoneyHealthScore   from './pages/Money_Health_Score'
import Portfolio          from './pages/Portfolio'
import HealthScore        from './pages/HealthScore'
import LifeEventAdvisor   from './pages/Life_Event_Advisor'
import TaxOptimizer       from './pages/Tax_Optimizer'
import PortfolioXRay      from './pages/Portfolio_X_Ray'
import AIAdvisor          from './pages/AI_Advisor'

export default function App() {
  return (
    <ThemeProvider>
      <CursorGlow />
      <BrowserRouter>
        <Routes>
          {/* Default → Landing */}
          <Route path="/"              element={<Landing />} />

          {/* Auth */}
          <Route path="/login"         element={<Login />} />
          <Route path="/signup"        element={<SignUp />} />

          {/* Onboarding */}
          <Route path="/onboarding"    element={<Onboarding />} />

          {/* Dashboard */}
          <Route path="/dashboard"     element={<Dashboard />} />

          {/* Feature Pages */}
          <Route path="/fire"          element={<FIREPathPlanner />} />
          <Route path="/health-score"  element={<MoneyHealthScore />} />
          <Route path="/portfolio"     element={<Portfolio />} />
          <Route path="/health"        element={<HealthScore />} />
          <Route path="/life-events"   element={<LifeEventAdvisor />} />
          <Route path="/tax"           element={<TaxOptimizer />} />
          <Route path="/portfolio-xray" element={<PortfolioXRay />} />
          <Route path="/ai-advisor"    element={<AIAdvisor />} />

          {/* 404 fallback */}
          <Route path="*"              element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}
