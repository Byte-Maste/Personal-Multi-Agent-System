import { useEffect, useState } from "react"
import SpendingPieChart from "../components/SpendingPieChart"
import TrendBarChart from "../components/TrendBarChart"

export default function Insights() {
  const [data, setData] = useState<{
    insights: { type: string; text: string }[]
    category_summaries: Record<string, number>
    trends: { month: string; total_spent: number; total_income: number }[]
    investment_readiness?: { score: number; recommendation: string }
  } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("token")
    fetch("http://localhost:8000/dashboard/", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-gray-400">Loading...</div>

  const pieData = data?.category_summaries
    ? Object.entries(data.category_summaries)
        .filter(([, v]) => v < 0)
        .map(([name, value]) => ({ name, value: Math.abs(value) }))
    : []

  const barData = data?.trends
    ? data.trends.map(t => ({
        month: t.month,
        income: t.total_income,
        expense: t.total_spent,
      }))
    : []

  const insights = data?.insights || []
  const ir = data?.investment_readiness

  return (
    <div className="p-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-6">Advisor Insights</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {pieData.length > 0 && (
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <h2 className="text-lg font-semibold mb-3">Spending by Category</h2>
            <SpendingPieChart data={pieData} />
          </div>
        )}
        {barData.length > 0 && (
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <h2 className="text-lg font-semibold mb-3">Monthly Trends</h2>
            <TrendBarChart data={barData} />
          </div>
        )}
      </div>

      {ir && (
        <div className="bg-purple-50 rounded-xl border border-purple-200 p-4 mb-6">
          <h2 className="text-lg font-semibold text-purple-800 mb-2">Investment Readiness</h2>
          <div className="flex items-center gap-4">
            <span className="text-3xl font-bold text-purple-600">{ir.score}/100</span>
            <p className="text-sm text-purple-700">{ir.recommendation}</p>
          </div>
        </div>
      )}

      {insights.length === 0 ? (
        <p className="text-gray-400">No insights yet — upload a statement first.</p>
      ) : (
        <div className="space-y-3">
          {insights.map((insight, i) => (
            <div key={i} className="bg-white rounded-xl border p-4 shadow-sm">
              <span className="text-xs font-semibold uppercase tracking-wide text-brand-600">{insight.type}</span>
              <p className="mt-1 text-gray-700">{insight.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
