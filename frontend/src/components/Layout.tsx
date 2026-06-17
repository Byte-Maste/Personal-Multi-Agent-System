import { NavLink, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/upload', label: 'Upload', icon: '📤' },
  { to: '/transactions', label: 'Transactions', icon: '💳' },
  { to: '/insights', label: 'Insights', icon: '💡' },
  { to: '/goals', label: 'Goals', icon: '🎯' },
  { to: '/scenarios', label: 'Scenarios', icon: '🧪' },
  { to: '/family', label: 'Family', icon: '👨‍👩‍👧‍👦' },
  { to: '/profile', label: 'Profile', icon: '👤' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()

  const handleLogout = () => {
    localStorage.removeItem('token')
    toast.success('Logged out')
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-xl font-bold text-brand-700">Finance Agent</h1>
        </div>
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-50'
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-100">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 w-full transition-colors"
          >
            <span>🚪</span>
            Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
