import { useEffect, useState } from "react"
import { useLocation } from "react-router-dom"
import { toast } from "sonner"

type ScenarioType = 'salary_hike' | 'job_loss' | 'new_loan'

interface ScenarioHistory {
  id: string; name: string; scenario_type: string
  inputs: Record<string, unknown>; projected_impact: Record<string, unknown>
  recommendation: string | null; created_at: string | null
}

interface SimulationResult {
  scenario_id: string; name: string
  current: { monthly_income: number; monthly_expenses: number; savings_rate: number }
  projected: Record<string, unknown>
  recommendation: string
}

const INPUT_FIELDS: Record<ScenarioType, { key: string; label: string; type: string; default: number | string }[]> = {
  salary_hike: [
    { key: 'hike_percentage', label: 'Hike %', type: 'number', default: 20 },
    { key: 'hike_month', label: 'Effective Month', type: 'month', default: '' },
  ],
  job_loss: [
    { key: 'months_without_income', label: 'Months Without Income', type: 'number', default: 6 },
    { key: 'severance_months', label: 'Severance (months)', type: 'number', default: 1 },
  ],
  new_loan: [
    { key: 'loan_amount', label: 'Loan Amount (₹)', type: 'number', default: 500000 },
    { key: 'tenure_years', label: 'Tenure (years)', type: 'number', default: 5 },
    { key: 'interest_rate', label: 'Interest Rate (%)', type: 'number', default: 9.5 },
  ],
}

export default function Scenarios() {
  const location = useLocation()
  const state = location.state as { sandbox?: boolean; type?: ScenarioType } | null
  const [sandboxMode] = useState(state?.sandbox || false)
  const [scenarioType, setScenarioType] = useState<ScenarioType>(state?.type || 'salary_hike')
  const [inputs, setInputs] = useState<Record<string, string>>({})
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [history, setHistory] = useState<ScenarioHistory[]>([])
  const [loading, setLoading] = useState(false)
  const [fetchingHistory, setFetchingHistory] = useState(true)

  const token = localStorage.getItem("token")

  useEffect(() => {
    fetch("http://localhost:8000/scenarios/", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(d => { setHistory(Array.isArray(d) ? d : []); setFetchingHistory(false) })
      .catch(() => setFetchingHistory(false))
  }, [])

  useEffect(() => {
    const defaults: Record<string, string> = {}
    INPUT_FIELDS[scenarioType].forEach(f => {
      defaults[f.key] = f.default ? String(f.default) : new Date().toISOString().slice(0, 7)
    })
    setInputs(defaults)
    setResult(null)
  }, [scenarioType])

  const handleSimulate = async () => {
    setLoading(true)
    setResult(null)
    const payload: Record<string, unknown> = {}
    Object.entries(inputs).forEach(([k, v]) => {
      const field = INPUT_FIELDS[scenarioType].find(f => f.key === k)
      payload[k] = field?.type === 'number' ? parseFloat(v) : v
    })

    try {
      const res = await fetch("http://localhost:8000/scenarios/simulate", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_type: scenarioType, inputs: payload }),
      })
      const data = await res.json()
      if (res.ok) {
        setResult(data)
        toast.success("Simulation complete")
        fetch("http://localhost:8000/scenarios/", { headers: { Authorization: `Bearer ${token}` } })
          .then(r => r.json())
          .then(d => setHistory(Array.isArray(d) ? d : []))
          .catch(() => {})
      } else {
        toast.error(data.detail || "Simulation failed")
      }
    } catch {
      toast.error("Server unreachable")
    } finally {
      setLoading(false)
    }
  }

  const getResultColor = () => {
    if (!result) return ''
    if (scenarioType === 'salary_hike') return 'border-green-200 bg-green-50'
    if (scenarioType === 'job_loss') return 'border-red-200 bg-red-50'
    return 'border-amber-200 bg-amber-50'
  }

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">
          {sandboxMode ? 'Financial Twin Sandbox' : 'What-If Scenarios'}
        </h1>
        {sandboxMode && (
          <span className="px-3 py-1.5 rounded-lg bg-yellow-100 text-yellow-800 text-sm font-medium animate-pulse">
            Sandbox Mode
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border p-6 shadow-sm space-y-4">
          <h2 className="text-lg font-semibold">Simulate</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Scenario Type</label>
            <select
              value={scenarioType}
              onChange={e => setScenarioType(e.target.value as ScenarioType)}
              className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm"
            >
              <option value="salary_hike">Salary Hike</option>
              <option value="job_loss">Job Loss</option>
              <option value="new_loan">New Loan</option>
            </select>
          </div>

          {INPUT_FIELDS[scenarioType].map(field => (
            <div key={field.key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{field.label}</label>
              <input
                type={field.type}
                value={inputs[field.key] || ''}
                onChange={e => setInputs(i => ({ ...i, [field.key]: e.target.value }))}
                className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm"
              />
            </div>
          ))}

          <button
            onClick={handleSimulate}
            disabled={loading}
            className="w-full px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
          >
            {loading ? "Simulating..." : "Simulate"}
          </button>

          {result && (
            <div className={`rounded-lg border-2 p-4 ${getResultColor()}`}>
              <h3 className="font-semibold mb-2">{result.name}</h3>

              <div className="text-sm space-y-2 mb-3">
                <p className="font-medium text-gray-600">Current:</p>
                <div className="flex justify-between text-gray-700"><span>Monthly Income</span><span>₹{result.current.monthly_income.toLocaleString()}</span></div>
                <div className="flex justify-between text-gray-700"><span>Monthly Expenses</span><span>₹{result.current.monthly_expenses.toLocaleString()}</span></div>
                <div className="flex justify-between text-gray-700"><span>Savings Rate</span><span>{result.current.savings_rate}%</span></div>
              </div>

              <div className="text-sm space-y-2 mb-3">
                <p className="font-medium text-gray-600">Projected:</p>
                {Object.entries(result.projected).map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span className="capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className="font-medium">
                      {typeof v === 'number' ? (k.includes('rate') || k.includes('ratio') ? `${v}%` : `₹${v.toLocaleString()}`) : String(v)}
                    </span>
                  </div>
                ))}
              </div>

              {result.recommendation && (
                <div className="text-sm p-3 rounded bg-white/70">
                  <span className="font-medium">Recommendation:</span> {result.recommendation}
                </div>
              )}
            </div>
          )}
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-4">History</h2>
          {fetchingHistory ? (
            <p className="text-gray-400 text-sm">Loading...</p>
          ) : history.length === 0 ? (
            <p className="text-gray-400 text-sm">No previous simulations.</p>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {history.map(sim => (
                <div key={sim.id} className="bg-white rounded-lg border p-4 text-sm">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-medium">{sim.name}</span>
                    <span className="text-xs text-gray-400">
                      {sim.created_at ? new Date(sim.created_at).toLocaleDateString() : ''}
                    </span>
                  </div>
                  {sim.recommendation && (
                    <p className="text-gray-600 text-xs mt-1">{sim.recommendation}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
