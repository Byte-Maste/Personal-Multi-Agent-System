import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { toast } from 'sonner'

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      })
      const data = await res.json()
      if (res.ok) {
        toast.success('Account created')
        navigate('/login')
      } else {
        toast.error(data.detail || 'Registration failed')
      }
    } catch {
      toast.error('Server unreachable')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-2xl shadow-lg w-full max-w-md space-y-6">
        <h1 className="text-3xl font-bold text-center text-brand-700">Create Account</h1>
        <p className="text-center text-gray-500">Join Personal Finance Agent</p>
        <div className="space-y-4">
          <input type="text" placeholder="Full Name" value={name} onChange={e => setName(e.target.value)} required className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none" />
          <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none" />
          <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none" />
        </div>
        <button type="submit" className="w-full bg-brand-600 text-white py-3 rounded-lg font-semibold hover:bg-brand-700 transition-colors">Create Account</button>
        <p className="text-center text-sm text-gray-500">Already have an account? <Link to="/login" className="text-brand-600 hover:underline">Sign in</Link></p>
      </form>
    </div>
  )
}
