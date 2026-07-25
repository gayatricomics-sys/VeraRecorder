import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Card } from '../components/ui/card'

interface Command {
  id: string;
  command: string;
  target: string;
  value: string;
}

export default function EditorScreen() {
  const location = useLocation()
  
  const queryParams = new URLSearchParams(location.search)
  const filename = queryParams.get('file') || ''
  
  const [commands, setCommands] = useState<Command[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  
  useEffect(() => {
    if (!filename) {
      setLoading(false)
      return
    }
    
    fetch(`http://127.0.0.1:8000/api/exports/read?filename=${encodeURIComponent(filename)}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
           const tests = data.data.tests || []
           if (tests.length > 0) {
              setCommands(tests[0].commands || [])
           }
        }
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [filename])

  const handleValueChange = (index: number, newValue: string) => {
    const updated = [...commands]
    updated[index].value = newValue
    setCommands(updated)
  }
  
  const handleTargetChange = (index: number, newTarget: string) => {
    const updated = [...commands]
    updated[index].target = newTarget
    setCommands(updated)
  }

  const saveScript = async () => {
    setSaving(true)
    try {
      const res = await fetch('http://127.0.0.1:8000/api/exports/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename,
          commands
        })
      })
      const data = await res.json()
      if (data.status === 'success') {
         alert('Script saved successfully! Playwright and Cypress files were also regenerated.')
      } else {
         alert('Error saving script.')
      }
    } catch (err) {
      console.error(err)
      alert('Failed to save script.')
    }
    setSaving(false)
  }

  if (loading) return <div className="p-10 text-white">Loading...</div>
  if (!filename) return <div className="p-10 text-white">No file specified.</div>

  return (
    <div className="flex-1 bg-[#0a0a14] overflow-y-auto">
      <div className="sticky top-0 z-10 p-6 bg-[#0a0a14]/80 backdrop-blur-xl border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-wide text-white">
              Edit Script: <span className="text-indigo-400">{filename}</span>
            </h1>
            <p className="text-xs text-slate-400">Replace hardcoded values with {'${SCANNER_VARIABLES}'}</p>
          </div>
        </div>
        
        <div className="flex gap-3">
          <button 
            onClick={saveScript}
            disabled={saving}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
            </svg>
            {saving ? 'Saving...' : 'Save Script'}
          </button>
          
          <Link 
            to="/"
            className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>

      <div className="p-6">
        <Card className="bg-white/5 border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-black/40 border-b border-white/5">
                  <th className="p-3 text-xs font-semibold text-slate-300 uppercase tracking-wider w-1/4">Command</th>
                  <th className="p-3 text-xs font-semibold text-slate-300 uppercase tracking-wider w-1/3">Target</th>
                  <th className="p-3 text-xs font-semibold text-slate-300 uppercase tracking-wider">Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {commands.map((cmd, idx) => (
                  <tr key={cmd.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="p-3">
                      <span className="inline-block px-2 py-1 bg-indigo-500/10 text-indigo-400 text-xs font-mono rounded border border-indigo-500/20">
                        {cmd.command}
                      </span>
                    </td>
                    <td className="p-3">
                      <input 
                        type="text" 
                        value={cmd.target} 
                        onChange={e => handleTargetChange(idx, e.target.value)}
                        className="w-full bg-black/20 border border-transparent focus:border-indigo-500/50 rounded px-2 py-1 text-sm text-slate-300 font-mono transition-colors focus:outline-none"
                      />
                    </td>
                    <td className="p-3">
                      <input 
                        type="text" 
                        value={cmd.value} 
                        onChange={e => handleValueChange(idx, e.target.value)}
                        placeholder="e.g. ${TOTP_SECRET}"
                        className="w-full bg-black/40 border border-white/10 focus:border-indigo-500 rounded px-3 py-1.5 text-sm text-white font-mono transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/20 placeholder-slate-600"
                      />
                    </td>
                  </tr>
                ))}
                {commands.length === 0 && (
                  <tr>
                    <td colSpan={3} className="p-8 text-center text-slate-500 text-sm">
                      No commands found in this script.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
