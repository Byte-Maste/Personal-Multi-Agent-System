import { useEffect, useState } from "react"
import { toast } from "sonner"

interface Goal {
  id: string; title: string; target_amount: number; current_amount: number
  deadline: string | null; monthly_required: number | null; priority: string | null
  status: string; progress_pct: number; months_remaining: number | null; feasible: boolean
}

interface GoalsResponse {
  goals: Goal[]
  total_monthly_required: number
  available_monthly: number
  shortfall: number
}

export default function Goals() {
  const [goalsData, setGoalsData] = useState<GoalsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [newGoal, setNewGoal] = useState({ title: "", target_amount: "", deadline: "", priority: "medium" })
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  const token = localStorage.getItem("token")
  const api = (path: string) => `http://localhost:8000${path}`

  const fetchGoals = () => {
    fetch(api("/goals/"), { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => { setGoalsData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(() => { fetchGoals() }, [])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    const amount = parseFloat(newGoal.target_amount)
    if (!newGoal.title || !amount || amount <= 0) { toast.error("Enter a valid title and target amount"); return }
    setSaving(true)
    try {
      const res = await fetch(api("/goals/"), {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newGoal.title,
          target_amount: amount,
          deadline: newGoal.deadline || null,
          priority: newGoal.priority,
        }),
      })
      if (res.ok) {
        toast.success("Goal created")
        setShowAddForm(false)
        setNewGoal({ title: "", target_amount: "", deadline: "", priority: "medium" })
        fetchGoals()
      } else {
        const d = await res.json()
        toast.error(d.detail || "Failed to create goal")
      }
    } catch { toast.error("Server unreachable") }
    finally { setSaving(false) }
  }

  const handleUpdateProgress = async (goalId: string, current_amount: number) => {
    setUpdatingId(goalId)
    try {
      const res = await fetch(api(`/goals/${goalId}`), {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ current_amount }),
      })
      if (res.ok) { fetchGoals(); toast.success("Progress updated") }
      else { const d = await res.json(); toast.error(d.detail || "Update failed") }
    } catch { toast.error("Server unreachable") }
    finally { setUpdatingId(null) }
  }

  const handleToggleStatus = async (goalId: string, status: string) => {
    try {
      const res = await fetch(api(`/goals/${goalId}`), {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      })
      if (res.ok) { fetchGoals(); toast.success(`Goal ${status}`) }
      else { const d = await res.json(); toast.error(d.detail || "Failed") }
    } catch { toast.error("Server unreachable") }
  }

  if (loading) return <div className="p-8 text-gray-400">Loading...</div>

  const goals = goalsData?.goals || []
  const { total_monthly_required = 0, available_monthly = 0, shortfall = 0 } = goalsData || {}

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Financial Goals</h1>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700"
        >
          {showAddForm ? "Cancel" : "+ Add Goal"}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleAdd} className="bg-white rounded-xl border p-6 shadow-sm mb-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input type="text" value={newGoal.title} onChange={e => setNewGoal(g => ({ ...g, title: e.target.value }))}
              className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm" placeholder="e.g. Buy a Car" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Target Amount (₹)</label>
            <input type="number" min="1" value={newGoal.target_amount} onChange={e => setNewGoal(g => ({ ...g, target_amount: e.target.value }))}
              className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm" placeholder="e.g. 1000000" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Deadline (optional)</label>
            <input type="date" value={newGoal.deadline} onChange={e => setNewGoal(g => ({ ...g, deadline: e.target.value }))}
              className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select value={newGoal.priority} onChange={e => setNewGoal(g => ({ ...g, priority: e.target.value }))}
              className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <button type="submit" disabled={saving}
            className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50">
            {saving ? "Creating..." : "Create Goal"}
          </button>
        </form>
      )}

      {goals.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 mb-4">No goals yet. Set your first financial goal!</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-xl border p-4 shadow-sm">
              <p className="text-sm text-gray-500">Monthly Required</p>
              <p className="text-xl font-bold text-brand-600">₹{total_monthly_required.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-xl border p-4 shadow-sm">
              <p className="text-sm text-gray-500">Available</p>
              <p className="text-xl font-bold text-green-600">₹{available_monthly.toLocaleString()}</p>
            </div>
            <div className="bg-white rounded-xl border p-4 shadow-sm">
              <p className="text-sm text-gray-500">Shortfall</p>
              <p className={`text-xl font-bold ${shortfall > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {shortfall > 0 ? `₹${shortfall.toLocaleString()}` : 'None'}
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {goals.map(g => (
              <div key={g.id} className={`bg-white rounded-xl border p-6 shadow-sm ${g.status !== 'active' ? 'opacity-60' : ''}`}>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-lg">{g.title}</h3>
                    <p className="text-sm text-gray-500">
                      {g.priority && <span className="capitalize">{g.priority} priority</span>}
                      {g.deadline && <span> · Due {new Date(g.deadline).toLocaleDateString()}</span>}
                      {g.months_remaining && <span> · {g.months_remaining} months left</span>}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {g.status === 'active' && (
                      <>
                        <button onClick={() => handleToggleStatus(g.id, 'completed')}
                          className="text-xs px-2 py-1 rounded bg-green-100 text-green-700 hover:bg-green-200">Complete</button>
                        <button onClick={() => handleToggleStatus(g.id, 'cancelled')}
                          className="text-xs px-2 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200">Cancel</button>
                      </>
                    )}
                    <span className={`text-xs font-semibold px-2 py-1 rounded capitalize ${
                      g.status === 'active' ? 'bg-blue-100 text-blue-700' :
                      g.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                    }`}>{g.status}</span>
                  </div>
                </div>

                <div className="mb-3">
                  <div className="flex justify-between text-sm mb-1">
                    <span>₹{g.current_amount.toLocaleString()} / ₹{g.target_amount.toLocaleString()}</span>
                    <span className="font-medium">{g.progress_pct}%</span>
                  </div>
                  <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        g.progress_pct >= 100 ? 'bg-green-500' : g.feasible ? 'bg-brand-600' : 'bg-amber-500'
                      }`}
                      style={{ width: `${Math.min(g.progress_pct, 100)}%` }}
                    />
                  </div>
                </div>

                <div className="flex gap-4 text-sm text-gray-600">
                  {g.monthly_required && <span>Monthly: ₹{g.monthly_required.toLocaleString()}</span>}
                  {g.months_remaining && g.monthly_required && (
                    <span>At current pace: {Math.ceil((g.target_amount - g.current_amount) / g.monthly_required)} months</span>
                  )}
                  {!g.feasible && <span className="text-amber-600 font-medium">⚠ May need adjustment</span>}
                </div>

                {g.status === 'active' && (
                  <div className="mt-3 flex items-center gap-2">
                    <input
                      type="number"
                      placeholder="Update progress (₹)"
                      className="w-40 rounded-lg border border-gray-200 px-3 py-1.5 text-sm"
                      onKeyDown={e => {
                        if (e.key === 'Enter') {
                          const val = parseFloat((e.target as HTMLInputElement).value)
                          if (!isNaN(val) && val >= 0) handleUpdateProgress(g.id, val)
                        }
                      }}
                    />
                    <span className="text-xs text-gray-400">Enter amount + press Enter</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
