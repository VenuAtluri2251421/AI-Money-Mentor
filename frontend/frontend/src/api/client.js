import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('artha_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ─── Auth ────────────────────────────────────────────────────────────────────

/** POST auth/register */
export const registerUser = (data) => api.post('auth/register', data)

/** POST auth/login */
export const loginUser = (data) => api.post('auth/login', data)

/** POST auth/send-code (Deprecated for now) */
export const sendVerificationCode = (email) =>
  api.post('auth/send-code', { email })

// ─── Profile & Portfolio ───────────────────────────────────────────────────────

/** PUT profile */
export const saveProfile = (data) => api.put('profile', data)

/** GET profile */
export const getProfile = () => api.get('profile')

/** GET portfolios */
export const getPortfolios = () => api.get('portfolios')

// ─── Calculators ─────────────────────────────────────────────────────────────

/** POST calculate/fire */
export const calculateFire = (data) => api.post('calculate/fire', data)

/** POST calculate/sip */
export const calculateSip = (data) => api.post('calculate/sip', data)

/** POST calculate/tax */
export const calculateTax = (data) => api.post('calculate/tax', data)

/** POST calculate/health */
export const calculateHealth = (data) => api.post('calculate/health', data)

// ─── AI Advisor ───────────────────────────────────────────────────────────────

/** POST advisor/chat */
export const advisorChat = (data) => api.post('advisor/chat', data)

export default api
