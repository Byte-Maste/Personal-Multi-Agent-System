import { useEffect, useState } from "react"
import { toast } from "sonner"

interface FamilyMember {
  id: string; name: string; relation: string | null
  monthly_income: number | null; contribution_ratio: number | null
}

interface FamilyData {
  members: FamilyMember[]
  user_income: number
  aggregation: { total_income: number; member_count: number; own_contribution_ratio: number }
}

export default function Family() {
  const [familyData, setFamilyData] = useState<FamilyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [newMember, setNewMember] = useState({ name: "", relation: "spouse", monthly_income: "" })

  const token = localStorage.getItem("token")

  const fetchFamily = () => {
    fetch("http://localhost:8000/family/", { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => { setFamilyData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(() => { fetchFamily() }, [])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMember.name) { toast.error("Enter a name"); return }
    setSaving(true)
    try {
      const res = await fetch("http://localhost:8000/family/members", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newMember.name,
          relation: newMember.relation,
          monthly_income: parseFloat(newMember.monthly_income) || null,
        }),
      })
      if (res.ok) {
        toast.success("Member added")
        setShowAddForm(false)
        setNewMember({ name: "", relation: "spouse", monthly_income: "" })
        fetchFamily()
      } else {
        const d = await res.json()
        toast.error(d.detail || "Failed")
      }
    } catch { toast.error("Server unreachable") }
    finally { setSaving(false) }
  }

  const handleRemove = async (memberId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/family/members/${memberId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) { toast.success("Member removed"); fetchFamily() }
      else { const d = await res.json(); toast.error(d.detail || "Failed") }
    } catch { toast.error("Server unreachable") }
  }

  const allMembers = familyData
    ? [
        { id: 'self', name: 'You', relation: 'self', monthly_income: familyData.user_income, contribution_ratio: familyData.aggregation.own_contribution_ratio },
        ...familyData.members,
      ]
    : []

  if (loading) return <div className="p-8 text-gray-400">Loading...</div>

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Family Dashboard</h1>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700"
        >
          {showAddForm ? "Cancel" : "+ Add Member"}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleAdd} className="bg-white rounded-xl border p-6 shadow-sm mb-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input type="text" value={newMember.name} onChange={e => setNewMember(m => ({ ...m, name: e.target.value }))}
              className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm" placeholder="e.g. Priya" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Relation</label>
            <select value={newMember.relation} onChange={e => setNewMember(m => ({ ...m, relation: e.target.value }))}
              className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm">
              <option value="spouse">Spouse</option>
              <option value="parent">Parent</option>
              <option value="child">Child</option>
              <option value="sibling">Sibling</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Income (₹)</label>
            <input type="number" min="0" value={newMember.monthly_income} onChange={e => setNewMember(m => ({ ...m, monthly_income: e.target.value }))}
              className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm" placeholder="e.g. 65000" />
          </div>
          <button type="submit" disabled={saving}
            className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50">
            {saving ? "Adding..." : "Add Member"}
          </button>
        </form>
      )}

      {familyData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <p className="text-sm text-gray-500">Family Members</p>
            <p className="text-2xl font-bold text-brand-600">{familyData.aggregation.member_count}</p>
          </div>
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <p className="text-sm text-gray-500">Total Income</p>
            <p className="text-2xl font-bold text-green-600">₹{familyData.aggregation.total_income.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <p className="text-sm text-gray-500">Your Contribution</p>
            <p className="text-2xl font-bold text-brand-600">{familyData.aggregation.own_contribution_ratio}%</p>
          </div>
        </div>
      )}

      {allMembers.length === 0 && !familyData ? (
        <p className="text-gray-400 text-center py-16">No family members yet.</p>
      ) : (
        <div className="space-y-3">
          {allMembers.map(m => (
            <div key={m.id} className={`bg-white rounded-xl border p-5 shadow-sm ${m.relation === 'self' ? 'border-brand-200 bg-brand-50/30' : ''}`}>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 font-bold">
                    {m.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold">{m.name}</h3>
                    <p className="text-xs text-gray-500 capitalize">{m.relation === 'self' ? 'You' : m.relation}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium">{m.monthly_income ? `₹${m.monthly_income.toLocaleString()}` : '—'}</p>
                  <p className="text-xs text-gray-400">{m.contribution_ratio ? `${m.contribution_ratio}% of total` : ''}</p>
                </div>
              </div>

              <div className="mt-3 w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-brand-500"
                  style={{ width: `${m.contribution_ratio || 0}%` }}
                />
              </div>

              {m.relation !== 'self' && (
                <button
                  onClick={() => handleRemove(m.id)}
                  className="mt-2 text-xs text-red-500 hover:text-red-700"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
