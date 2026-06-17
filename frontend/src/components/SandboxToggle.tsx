import { useState } from "react"

interface SandboxToggleProps {
  onEnterSandbox: () => void
  onExitSandbox: () => void
}

export default function SandboxToggle({ onEnterSandbox, onExitSandbox }: SandboxToggleProps) {
  const [inSandbox, setInSandbox] = useState(false)

  const handleToggle = () => {
    if (inSandbox) {
      setInSandbox(false)
      onExitSandbox()
    } else {
      setInSandbox(true)
      onEnterSandbox()
    }
  }

  return (
    <div className="flex items-center gap-3 px-4 py-2 rounded-lg border border-yellow-300 bg-yellow-50">
      <div className="flex items-center gap-2">
        <span className={`w-3 h-3 rounded-full ${inSandbox ? "bg-yellow-500 animate-pulse" : "bg-green-500"}`} />
        <span className="text-sm font-medium text-yellow-800">
          {inSandbox ? "Financial Twin Sandbox Active" : "Live Mode"}
        </span>
      </div>
      <button
        onClick={handleToggle}
        className={`text-xs font-semibold px-3 py-1.5 rounded-md transition-colors ${
          inSandbox
            ? "bg-yellow-500 text-white hover:bg-yellow-600"
            : "bg-gray-200 text-gray-700 hover:bg-gray-300"
        }`}
      >
        {inSandbox ? "Exit Sandbox" : "Enter Financial Twin Sandbox"}
      </button>
      {inSandbox && (
        <span className="text-xs text-yellow-700 ml-2">
          Scenario changes won't affect your live data
        </span>
      )}
    </div>
  )
}
