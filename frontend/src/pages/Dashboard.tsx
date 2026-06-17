import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import SandboxToggle from "../components/SandboxToggle"
import SpendingPieChart from "../components/SpendingPieChart"
import TrendBarChart from "../components/TrendBarChart"

interface DashboardData {
  health_score: number
  health_breakdown: Record<string, number>
  utilization_report: {
    total_income: number; total_needs: number; total_wants: number; total_savings: number
    needs_pct: number; wants_pct: number; savings_pct: number
  }
  budget_alerts: { type: string; category: string; message: string; severity: string }[]
  anomalies: { description: string; amount: number; reason: string; severity: string }[]
  subscriptions: { merchant: string; estimated_amount: number; frequency: string }[]
  cashflow_forecast: {
    current_balance: number; projected_balance_30d: number; avg_daily_income: number; avg_daily_expense: number; net_daily: number
    lowest_balance: number; lowest_balance_date: string; forecast: { date: string; projected_balance: number }[]
  }
  trends: { month: string; total_spent: number; total_income: number; top_category: string }[]
  insights: { type: string; text: string }[]
  category_summaries: Record<string, number>
  monthly_summaries: Record<string, Record<string, number>>
  rebalance_recommendations: { area: string; action: string; potential_saving: number }[]
  investment_readiness?: {
    score: number; breakdown: Record<string, number>
    emergency_fund_months: number; debt_ratio_pct: number
    recommendation: string; suggested_allocation: Record<string, string>
  }
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [sandboxMode, setSandboxMode] = useState(false)
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    fetch('http://localhost:8000/dashboard/', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-gray-500">Loading dashboard...</div>

  if (!data || !data.trends || data.trends.length === 0) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[60vh]">
        <h1 className="text-3xl font-bold mb-4">Welcome to AI CFO Dashboard</h1>
        <p className="text-gray-500 mb-6 text-center max-w-md">
          Upload your first bank statement to get AI-powered financial insights, spending analysis, and budget recommendations.
        </p>
        <button
          onClick={() => navigate('/upload')}
          className="px-6 py-3 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors"
        >
          Upload Statement
        </button>
      </div>
    )
  }

  const u = data?.utilization_report
  const cf = data?.cashflow_forecast
  const ir = data?.investment_readiness

  const pieData = data.category_summaries
    ? Object.entries(data.category_summaries)
        .filter(([, v]) => v < 0)
        .map(([name, value]) => ({ name, value: Math.abs(value) }))
    : []

  const barData = data.trends
    ? data.trends.map(t => ({
        month: t.month,
        income: t.total_income,
        expense: t.total_spent,
      }))
    : []

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">AI CFO Dashboard</h1>
        <SandboxToggle
          onEnterSandbox={() => setSandboxMode(true)}
          onExitSandbox={() => setSandboxMode(false)}
        />
      </div>

      {sandboxMode && (
        <div className="rounded-lg border-2 border-dashed border-yellow-400 bg-yellow-50/50 p-6">
          <h2 className="text-lg font-semibold text-yellow-800 mb-2">Financial Twin Sandbox</h2>
          <p className="text-sm text-yellow-700 mb-4">You are in sandbox mode.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => navigate('/scenarios', { state: { sandbox: true, type: 'salary_hike' } })}
              className="px-4 py-3 rounded-lg border border-yellow-300 bg-white text-sm font-medium hover:bg-yellow-50 text-left"
            >
              Simulate salary hike
            </button>
            <button
              onClick={() => navigate('/scenarios', { state: { sandbox: true, type: 'job_loss' } })}
              className="px-4 py-3 rounded-lg border border-yellow-300 bg-white text-sm font-medium hover:bg-yellow-50 text-left"
            >
              Simulate job loss
            </button>
            <button
              onClick={() => navigate('/scenarios', { state: { sandbox: true, type: 'new_loan' } })}
              className="px-4 py-3 rounded-lg border border-yellow-300 bg-white text-sm font-medium hover:bg-yellow-50 text-left"
            >
              Simulate new loan
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="rounded-xl border p-4 bg-white shadow-sm">
          <p className="text-sm text-gray-500">Health Score</p>
          <p className="text-3xl font-bold text-brand-600">{data?.health_score ?? '--'}</p>
          {data?.health_breakdown && (
            <div className="mt-2 text-xs text-gray-400 space-y-1">
              {Object.entries(data.health_breakdown).map(([k, v]) => (
                <div key={k} className="flex justify-between"><span>{k}</span><span>{v}</span></div>
              ))}
            </div>
          )}
        </div>
        <div className="rounded-xl border p-4 bg-white shadow-sm">
          <p className="text-sm text-gray-500">Monthly Savings</p>
          <p className="text-3xl font-bold text-green-600">₹{u?.total_savings?.toLocaleString() ?? '--'}</p>
          <p className="text-xs text-gray-400">{u?.savings_pct ?? 0}% of income (target 20%)</p>
        </div>
        <div className="rounded-xl border p-4 bg-white shadow-sm">
          <p className="text-sm text-gray-500">Budget Utilization</p>
          <p className="text-3xl font-bold text-brand-600">50/30/20</p>
          <div className="mt-1 text-xs text-gray-400">Needs {u?.needs_pct ?? 0}% · Wants {u?.wants_pct ?? 0}% · Savings {u?.savings_pct ?? 0}%</div>
        </div>
        <div className="rounded-xl border p-4 bg-white shadow-sm">
          <p className="text-sm text-gray-500">Current Balance</p>
          <p className="text-3xl font-bold text-brand-600">₹{cf?.current_balance?.toLocaleString() ?? '--'}</p>
          <p className="text-xs text-gray-400">from latest statement</p>
        </div>
        <div className="rounded-xl border p-4 bg-white shadow-sm">
          <p className="text-sm text-gray-500">Investment Readiness</p>
          <p className="text-3xl font-bold text-purple-600">{ir?.score ?? '--'}</p>
          <p className="text-xs text-gray-400 truncate">{ir?.recommendation?.slice(0, 40) ?? 'N/A'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border p-4 bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Category Breakdown</h2>
          <SpendingPieChart data={pieData} />
        </div>
        <div className="rounded-xl border p-4 bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Income vs Expense Trend</h2>
          <TrendBarChart data={barData} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {cf && (
          <div className="rounded-xl border p-4 bg-white shadow-sm">
            <h2 className="text-lg font-semibold mb-3">Cash Flow Forecast (30d)</h2>
            <div className="text-sm space-y-1">
              <div className="flex justify-between"><span>Current Balance</span><span className="font-medium">₹{cf.current_balance.toLocaleString()}</span></div>
              <div className="flex justify-between"><span>Projected Balance</span><span className="font-medium">₹{cf.projected_balance_30d.toLocaleString()}</span></div>
              <div className="flex justify-between"><span>Avg Daily Income</span><span>₹{cf.avg_daily_income.toLocaleString()}</span></div>
              <div className="flex justify-between"><span>Avg Daily Expense</span><span>₹{cf.avg_daily_expense.toLocaleString()}</span></div>
              <div className="flex justify-between"><span>Lowest Balance</span><span className={cf.lowest_balance < 0 ? 'text-red-600' : 'text-green-600'}>₹{cf.lowest_balance.toLocaleString()} on {cf.lowest_balance_date}</span></div>
            </div>
          </div>
        )}
        {data && data.subscriptions && data.subscriptions.length > 0 && (
          <div className="rounded-xl border p-4 bg-white shadow-sm">
            <h2 className="text-lg font-semibold mb-3">Subscriptions</h2>
            <div className="text-sm space-y-1">
              {data.subscriptions.map(s => (
                <div key={s.merchant} className="flex justify-between">
                  <span>{s.merchant}</span>
                  <span className="font-medium">₹{s.estimated_amount.toLocaleString()}/{s.frequency}</span>
                </div>
              ))}
              <div className="border-t pt-1 mt-1 flex justify-between font-medium">
                <span>Total</span>
                <span>₹{data.subscriptions.reduce((a, s) => a + s.estimated_amount, 0).toLocaleString()}/mo</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {ir && (
        <div className="rounded-xl border p-4 bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Investment Readiness</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex justify-between"><span>Score</span><span className="font-bold text-purple-600">{ir.score}/100</span></div>
              <div className="flex justify-between"><span>Emergency Fund</span><span>{ir.emergency_fund_months} months</span></div>
              <div className="flex justify-between"><span>Debt Ratio</span><span>{ir.debt_ratio_pct}%</span></div>
            </div>
            <div>
              <p className="text-gray-700 mb-2">{ir.recommendation}</p>
              <div className="flex gap-2 flex-wrap">
                {Object.entries(ir.suggested_allocation).map(([k, v]) => (
                  <span key={k} className="px-2 py-1 rounded bg-gray-100 text-xs">{k}: {v}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {data && data.insights && data.insights.length > 0 && (
        <div className="rounded-xl border p-4 bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Advisor Insights</h2>
          <div className="space-y-2">
            {data.insights.slice(0, 8).map((insight, i) => (
              <div key={i} className="text-sm p-2 rounded bg-gray-50">
                <span className="text-gray-400 uppercase text-xs mr-2">{insight.type}</span>
                {insight.text}
              </div>
            ))}
          </div>
        </div>
      )}

      {data && data.budget_alerts && data.budget_alerts.length > 0 && (
        <div className="rounded-xl border-2 border-amber-200 p-4 bg-amber-50">
          <h2 className="text-lg font-semibold text-amber-800 mb-2">Budget Alerts</h2>
          {data.budget_alerts.map((a, i) => (
            <div key={i} className="text-sm text-amber-700 flex items-start gap-2">
              <span>⚠️</span><span>{a.message}</span>
            </div>
          ))}
        </div>
      )}

      {data && data.anomalies && data.anomalies.length > 0 && (
        <div className="rounded-xl border-2 border-red-200 p-4 bg-red-50">
          <h2 className="text-lg font-semibold text-red-800 mb-2">Anomalies Detected</h2>
          {data.anomalies.map((a, i) => (
            <div key={i} className="text-sm text-red-700 flex items-start gap-2 mb-1">
              <span>🚩</span><span>{a.description}: {a.reason}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
