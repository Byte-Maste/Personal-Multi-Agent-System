import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { toast } from 'sonner'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (res.ok) {
        localStorage.setItem('token', data.access_token)
        toast.success('Logged in')
        navigate('/dashboard')
      } else {
        toast.error(data.detail || 'Login failed')
      }
    } catch {
      toast.error('Server unreachable')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-2xl shadow-lg w-full max-w-md space-y-6">
        <h1 className="text-3xl font-bold text-center text-brand-700">Personal Finance Agent</h1>
        <p className="text-center text-gray-500">Sign in to your account</p>
        <div className="space-y-4">
          <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none" />
          <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none" />
        </div>
        <button type="submit" className="w-full bg-brand-600 text-white py-3 rounded-lg font-semibold hover:bg-brand-700 transition-colors">Sign In</button>
        <p className="text-center text-sm text-gray-500">Don't have an account? <Link to="/register" className="text-brand-600 hover:underline">Register</Link></p>
      </form>
    </div>
  )
}
