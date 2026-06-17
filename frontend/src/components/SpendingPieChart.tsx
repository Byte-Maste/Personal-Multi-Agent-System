import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

const COLORS = ['#8B5CF6', '#F59E0B', '#EF4444', '#10B981', '#3B82F6', '#EC4899', '#6366F1', '#14B8A6', '#F97316', '#84CC16']

interface SpendingPieChartProps {
  data: { name: string; value: number }[]
}

export default function SpendingPieChart({ data }: SpendingPieChartProps) {
  if (!data || data.length === 0) return null

  const total = data.reduce((s, d) => s + Math.abs(d.value), 0)

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
            nameKey="name"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => `₹${Math.abs(value).toLocaleString()}`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      <p className="text-center text-sm text-gray-500 mt-2">Total: ₹{total.toLocaleString()}</p>
    </div>
  )
}
