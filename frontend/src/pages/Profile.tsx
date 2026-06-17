import { useEffect, useState } from "react"
import { toast } from "sonner"

interface UserProfile {
  id: string; email: string; name: string | null; monthly_income: number | null
  currency: string; risk_profile: string | null
}

interface DashboardSummary {
  cashflow_forecast?: { current_balance: number }
  health_score?: number
}

export default function Profile() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [formData, setFormData] = useState({ name: "", monthly_income: "", risk_profile: "" })

  const token = localStorage.getItem("token")

  useEffect(() => {
    Promise.all([
      fetch("http://localhost:8000/auth/me", { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
      fetch("http://localhost:8000/dashboard/", { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
    ])
      .then(([prof, dash]) => {
        setProfile(prof)
        setDashboard(dash)
        setFormData({
          name: prof.name || "",
          monthly_income: prof.monthly_income?.toString() || "",
          risk_profile: prof.risk_profile || "moderate",
        })
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    const payload: Record<string, unknown> = {}
    if (formData.name !== (profile?.name || "")) payload.name = formData.name
    if (formData.monthly_income) {
      const val = parseFloat(formData.monthly_income)
      if (val <= 0) { toast.error("Monthly income must be > 0"); return }
      if (val !== profile?.monthly_income) payload.monthly_income = val
    }
    if (formData.risk_profile !== (profile?.risk_profile || "moderate")) payload.risk_profile = formData.risk_profile
    if (Object.keys(payload).length === 0) { setEditing(false); return }

    setSaving(true)
    try {
      const res = await fetch("http://localhost:8000/auth/me", {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (res.ok) {
        setProfile(data)
        toast.success("Profile updated")
        setEditing(false)
      } else {
        toast.error(data.detail || "Update failed")
      }
    } catch {
      toast.error("Server unreachable")
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="p-8 text-gray-400">Loading...</div>
  if (!profile) return <div className="p-8 text-red-500">Failed to load profile</div>

  const currentBalance = dashboard?.cashflow_forecast?.current_balance

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">Profile</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <p className="text-sm text-gray-500">Current Balance</p>
          <p className="text-2xl font-bold text-brand-600">₹{currentBalance?.toLocaleString() ?? '—'}</p>
          <p className="text-xs text-gray-400">from latest bank statement</p>
        </div>
        <div className="bg-white rounded-xl border p-6 shadow-sm">
          <p className="text-sm text-gray-500">Health Score</p>
          <p className="text-2xl font-bold text-brand-600">{dashboard?.health_score ?? '—'} / 100</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border p-6 shadow-sm space-y-4">
        {!editing ? (
          <>
            <div className="flex justify-between items-center">
              <div>
                <span className="text-sm text-gray-500">Name</span>
                <p className="font-medium">{profile.name ?? "—"}</p>
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-500">Email</span>
              <p className="font-medium">{profile.email}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Monthly Income</span>
              <p className="font-medium">{profile.monthly_income ? `₹${profile.monthly_income.toLocaleString()}` : "—"}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Currency</span>
              <p className="font-medium">{profile.currency}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Risk Profile</span>
              <p className="font-medium capitalize">{profile.risk_profile ?? "—"}</p>
            </div>
            <button
              onClick={() => setEditing(true)}
              className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700"
            >
              Edit Profile
            </button>
          </>
        ) : (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text" value={formData.name}
                onChange={e => setFormData(f => ({ ...f, name: e.target.value }))}
                className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Income (₹)</label>
              <input
                type="number" min="0" step="1000" value={formData.monthly_income}
                onChange={e => setFormData(f => ({ ...f, monthly_income: e.target.value }))}
                className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm"
                placeholder="e.g. 85000"
              />
              {formData.monthly_income && parseFloat(formData.monthly_income) <= 0 && (
                <p className="text-xs text-red-500 mt-1">Must be greater than 0</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Risk Profile</label>
              <select
                value={formData.risk_profile}
                onChange={e => setFormData(f => ({ ...f, risk_profile: e.target.value }))}
                className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm"
              >
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save"}
              </button>
              <button
                onClick={() => { setEditing(false); setFormData({ name: profile.name || "", monthly_income: profile.monthly_income?.toString() || "", risk_profile: profile.risk_profile || "moderate" }) }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
