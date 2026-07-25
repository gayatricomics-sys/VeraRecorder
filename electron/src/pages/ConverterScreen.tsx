import { useState } from 'react'
import { Link } from 'react-router-dom'

export default function ConverterScreen() {
  const [format, setFormat] = useState<'playwright' | 'cypress'>('playwright')
  const [projectName, setProjectName] = useState('MyProject')
  const [targetUrl, setTargetUrl] = useState('https://example.com')
  const [scriptContent, setScriptContent] = useState('')
  const [status, setStatus] = useState<'idle' | 'converting' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  const handleConvert = async () => {
    if (!scriptContent.trim()) {
      setStatus('error')
      setMessage('Please paste a Playwright script first.')
      return
    }

    setStatus('converting')
    setMessage('Converting script to .SIDE format...')

    try {
      const endpoint = format === 'playwright' 
        ? 'http://127.0.0.1:8000/api/convert/playwright'
        : 'http://127.0.0.1:8000/api/convert/cypress'
        
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scriptContent,
          projectName,
          targetUrl
        })
      })

      const result = await response.json()
      if (result.status === 'success') {
        setStatus('success')
        setMessage(`Successfully converted and saved to: ${result.path}`)
      } else {
        setStatus('error')
        setMessage(`Failed to convert: ${result.message}`)
      }
    } catch (err: any) {
      setStatus('error')
      setMessage(`Connection error: ${err.message}`)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a14] via-[#111122] to-[#1a1a3a] text-slate-200 font-inter">
      {/* Top Navbar */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-white/5 bg-black/20 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold tracking-wide text-white">
            Script to <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">.SIDE Converter</span>
          </h1>
        </div>
        <Link 
          to="/" 
          className="px-5 py-2.5 rounded-full bg-white/5 hover:bg-white/10 text-sm font-medium transition-all duration-300 border border-white/5 hover:border-white/10 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Dashboard
        </Link>
      </nav>

      <main className="max-w-5xl mx-auto px-8 py-10 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Col - Settings */}
        <div className="space-y-6 lg:col-span-1">
          <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm shadow-xl space-y-5">
            <h2 className="text-lg font-medium text-white mb-2 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Project Details
            </h2>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-400">Framework</label>
              <div className="flex bg-black/40 p-1 rounded-xl border border-white/5">
                <button
                  onClick={() => setFormat('playwright')}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${format === 'playwright' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'}`}
                >
                  Playwright
                </button>
                <button
                  onClick={() => setFormat('cypress')}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${format === 'cypress' ? 'bg-emerald-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'}`}
                >
                  Cypress
                </button>
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-400">Project Name</label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="w-full px-4 py-3 bg-black/30 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm"
                placeholder="e.g. Acme_Web_Tests"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-400">Base URL</label>
              <input
                type="text"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                className="w-full px-4 py-3 bg-black/30 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm font-mono text-blue-300"
                placeholder="https://example.com"
              />
            </div>
            
            <button
              onClick={handleConvert}
              disabled={status === 'converting'}
              className="w-full mt-4 py-3.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-xl font-semibold shadow-lg shadow-blue-500/25 transition-all duration-300 flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status === 'converting' ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Converting...
                </>
              ) : (
                <>
                  Convert to .SIDE
                  <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </>
              )}
            </button>
          </div>
          
          {message && (
            <div className={`p-4 rounded-xl border backdrop-blur-sm text-sm ${status === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-200' : 'bg-green-500/10 border-green-500/20 text-green-200'}`}>
              {message}
            </div>
          )}
        </div>

        {/* Right Col - Code Input */}
        <div className="lg:col-span-2 flex flex-col h-[600px]">
          <div className="flex-1 p-1 rounded-2xl bg-gradient-to-b from-white/10 to-transparent shadow-xl">
            <div className="h-full bg-[#0d0d16] rounded-xl flex flex-col overflow-hidden">
              <div className="px-4 py-3 border-b border-white/5 bg-black/20 flex items-center gap-2">
                <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{format === 'playwright' ? 'Playwright Script (JS/TS/Py)' : 'Cypress Script (JS/TS)'}</span>
              </div>
              <textarea
                value={scriptContent}
                onChange={(e) => setScriptContent(e.target.value)}
                placeholder={format === 'playwright' 
                  ? "Paste your Playwright script here...\\n\\nExample:\\nawait page.goto('https://testfire.net');\\nawait page.locator('#query').fill('admin');\\nawait page.getByRole('button', { name: 'Go' }).click();"
                  : "Paste your Cypress script here...\\n\\nExample:\\ncy.visit('https://testfire.net');\\ncy.get('#query').type('admin');\\ncy.contains('Go').click();"}
                className="flex-1 w-full p-4 bg-transparent resize-none focus:outline-none text-slate-300 font-mono text-sm leading-relaxed"
                spellCheck="false"
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
