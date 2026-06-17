import { useState, useEffect, useRef } from "react"
import { toast } from "sonner"
import UploadProgress from "../components/UploadProgress"

type ProgressStep = 'idle' | 'uploading' | 'extracting' | 'parsing' | 'categorizing' | 'complete'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [source, setSource] = useState("unknown")
  const [password, setPassword] = useState("")
  const [uploading, setUploading] = useState(false)
  const [progressStep, setProgressStep] = useState<ProgressStep>('idle')
  const [result, setResult] = useState<{ statement_id: string; transactions_count: number; status: string } | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const pollStatus = (statementId: string) => {
    setProgressStep('extracting')
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/upload/status/${statementId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        })
        const data = await res.json()
        if (data.status === "completed") {
          if (pollRef.current) clearInterval(pollRef.current)
          setProgressStep('parsing')
          setTimeout(() => setProgressStep('categorizing'), 600)
          setTimeout(() => {
            setProgressStep('complete')
            setResult(data)
            toast.success(`Processed ${data.transactions_count} transactions`)
          }, 1200)
        }
      } catch {
        if (pollRef.current) clearInterval(pollRef.current)
      }
    }, 2000)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) { toast.error("Select a file"); return }
    setUploading(true)
    setResult(null)
    setProgressStep('uploading')

    const form = new FormData()
    form.append("file", file)
    form.append("source", source)
    if (password) form.append("statement_password", password)

    try {
      const res = await fetch("http://localhost:8000/upload/statement", {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: form,
      })
      const data = await res.json()
      if (res.ok) {
        pollStatus(data.statement_id)
      } else {
        setProgressStep('idle')
        toast.error(data.detail || "Upload failed")
      }
    } catch {
      setProgressStep('idle')
      toast.error("Server unreachable")
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">Upload Statement</h1>
      <form onSubmit={handleSubmit} className="space-y-4 bg-white rounded-xl border p-6 shadow-sm">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">File (PDF/CSV)</label>
          <input type="file" accept=".pdf,.csv" onChange={e => setFile(e.target.files?.[0] ?? null)} className="w-full" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
          <select value={source} onChange={e => setSource(e.target.value)} className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm">
            <option value="unknown">Auto-detect</option>
            <option value="hdfc">HDFC</option>
            <option value="icici">ICICI</option>
            <option value="sbi">SBI</option>
            <option value="axis">Axis</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">PDF Password (if encrypted)</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="w-full rounded-lg border border-gray-200 px-4 py-2 text-sm" placeholder="Leave blank if not password-protected" />
        </div>
        <button type="submit" disabled={uploading} className="px-6 py-2 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 disabled:opacity-50">
          {uploading ? "Processing..." : "Upload"}
        </button>
      </form>

      <UploadProgress step={progressStep} />

      {result && progressStep === 'complete' && (
        <div className="mt-6 bg-green-50 border border-green-200 rounded-xl p-4">
          <h3 className="font-semibold text-green-800">Upload Successful</h3>
          <p className="text-sm text-green-700">Statement ID: {result.statement_id}</p>
          <p className="text-sm text-green-700">Transactions: {result.transactions_count}</p>
          <p className="text-sm text-green-700">Status: {result.status}</p>
        </div>
      )}
    </div>
  )
}
