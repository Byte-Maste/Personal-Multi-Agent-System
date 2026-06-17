import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface TrendBarChartProps {
  data: { month: string; income: number; expense: number }[]
}

export default function TrendBarChart({ data }: TrendBarChartProps) {
  if (!data || data.length === 0) return null

  const chartData = data.map(d => ({
    month: d.month,
    Income: d.income,
    Expense: d.expense,
  }))

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData}>
          <XAxis dataKey="month" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value: number) => `₹${value.toLocaleString()}`} />
          <Legend />
          <Bar dataKey="Income" fill="#10B981" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Expense" fill="#EF4444" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
