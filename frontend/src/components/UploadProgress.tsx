type ProgressStep = 'idle' | 'uploading' | 'extracting' | 'parsing' | 'categorizing' | 'complete'

const steps: { key: ProgressStep; label: string; icon: string }[] = [
  { key: 'uploading', label: 'Uploading', icon: '📤' },
  { key: 'extracting', label: 'Extracting', icon: '🔍' },
  { key: 'parsing', label: 'LLM Parsing', icon: '🤖' },
  { key: 'categorizing', label: 'Categorizing', icon: '🏷️' },
  { key: 'complete', label: 'Complete', icon: '✅' },
]

interface UploadProgressProps {
  step: ProgressStep
}

export default function UploadProgress({ step }: UploadProgressProps) {
  if (step === 'idle') return null

  const currentIndex = steps.findIndex(s => s.key === step)

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between">
        {steps.map((s, i) => {
          const isActive = i === currentIndex
          const isDone = i < currentIndex
          const isPending = i > currentIndex

          return (
            <div key={s.key} className="flex flex-col items-center gap-1">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold transition-all ${
                  isDone ? 'bg-green-500 text-white' :
                  isActive ? 'bg-brand-600 text-white animate-pulse' :
                  'bg-gray-200 text-gray-400'
                }`}
              >
                {isDone ? '✓' : s.icon}
              </div>
              <span className={`text-xs font-medium ${
                isActive ? 'text-brand-700' : isDone ? 'text-green-600' : 'text-gray-400'
              }`}>
                {s.label}
              </span>
            </div>
          )
        })}
      </div>
      <div className="relative mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-brand-600 transition-all duration-500 rounded-full"
          style={{ width: `${((currentIndex + 1) / steps.length) * 100}%` }}
        />
      </div>
    </div>
  )
}
