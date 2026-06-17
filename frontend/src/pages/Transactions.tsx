import { useEffect, useState } from "react"

interface Transaction {
  id: string; transaction_date: string; description: string | null; merchant: string | null
  amount: number; type: string; category_name: string | null; is_recurring: boolean; is_anomaly: boolean
}

interface Category { id: string; name: string; type: string }

export default function Transactions() {
  const [txns, setTxns] = useState<Transaction[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const pageSize = 25

  const token = localStorage.getItem("token")
  const headers = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    fetch("http://localhost:8000/transactions/categories", { headers })
      .then(r => r.json())
      .then(setCategories)
      .catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
    if (search) params.set("search", search)
    if (categoryFilter) params.set("category_id", categoryFilter)
    fetch(`http://localhost:8000/transactions/?${params}`, { headers })
      .then(r => r.json())
      .then(d => { setTxns(d.items); setTotal(d.total); setLoading(false) })
      .catch(() => setLoading(false))
  }, [page, search, categoryFilter])

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Transactions</h1>

      <div className="flex gap-4 mb-4">
        <input
          type="text" placeholder="Search description or merchant..."
          value={search} onChange={e => { setSearch(e.target.value); setPage(1) }}
          className="flex-1 rounded-lg border border-gray-200 px-4 py-2 text-sm"
        />
        <select value={categoryFilter} onChange={e => { setCategoryFilter(e.target.value); setPage(1) }} className="rounded-lg border border-gray-200 px-4 py-2 text-sm">
          <option value="">All categories</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-4 py-3">Date</th>
              <th className="text-left px-4 py-3">Description</th>
              <th className="text-left px-4 py-3">Merchant</th>
              <th className="text-right px-4 py-3">Amount</th>
              <th className="text-center px-4 py-3">Type</th>
              <th className="text-left px-4 py-3">Category</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">Loading...</td></tr>
            ) : txns.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">No transactions</td></tr>
            ) : txns.map(tx => (
              <tr key={tx.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-500">{tx.transaction_date}</td>
                <td className="px-4 py-3">{tx.description ?? '—'}</td>
                <td className="px-4 py-3 text-gray-500">{tx.merchant ?? '—'}</td>
                <td className={`px-4 py-3 text-right font-medium ${tx.type === 'credit' ? 'text-green-600' : 'text-red-600'}`}>
                  {tx.type === 'credit' ? '+' : '-'}₹{tx.amount.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${tx.type === 'credit' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {tx.type}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full">
                    {tx.category_name ?? 'Uncategorized'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-gray-500">{total} total transactions</span>
          <div className="flex gap-2">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 rounded border text-sm disabled:opacity-30">Prev</button>
            <span className="px-3 py-1 text-sm">{page} / {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} className="px-3 py-1 rounded border text-sm disabled:opacity-30">Next</button>
          </div>
        </div>
      )}
    </div>
  )
}
