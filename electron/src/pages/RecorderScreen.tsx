import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'

import { ArrowLeft, Play, Square, Save, Globe, Bot, MousePointerClick } from 'lucide-react'
import { useStore } from '../store/useStore'
import { wsService } from '../services/api'
import { useState } from 'react'

export function RecorderScreen() {
  const navigate = useNavigate()
  const { url, setUrl, isRecording, commands, startRecording, stopRecording, clearCommands } = useStore()
  const [targetUrl, setTargetUrl] = useState(url)
  const [projectName, setProjectName] = useState('VeraRecording')
  const [crawlMode, setCrawlMode] = useState('manualcrawl')

  const handleStart = () => {
    setUrl(targetUrl)
    clearCommands()
    startRecording()
    wsService.sendCommand('START_RECORDING', { url: targetUrl })
  }

  const handleAutoCrawl = () => {
    setUrl(targetUrl)
    clearCommands()
    setCrawlMode('autocrawl')
    startRecording()
    wsService.sendCommand('START_AUTO_CRAWL', { url: targetUrl })
  }

  const handleStop = () => {
    stopRecording()
    wsService.sendCommand('STOP_RECORDING')
    
    // Autosave as .side file
    wsService.sendCommand('EXPORT_SIDE', { 
      projectName: projectName ? `${projectName}_${crawlMode}` : `VeraRecording_${crawlMode}`,
      url: targetUrl,
      commands: commands
    })

    // Do not show commands on UI when done, navigate back to history
    clearCommands()
    navigate('/')
  }

  return (
    <div className="flex flex-col h-screen">
      <header className="border-b border-blue-200 bg-white p-4 px-6 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/')} className="text-blue-600 hover:text-blue-900 hover:bg-blue-50">
            <ArrowLeft size={20} />
          </Button>
          <h2 className="text-xl font-bold text-blue-900">New Recording Session</h2>
          {isRecording ? (
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-600">Recording</span>
          ) : (
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">Ready</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {!isRecording ? (
            <>
              <Button onClick={handleStart} className="bg-emerald-600 hover:bg-emerald-700 gap-2 text-white">
                <Play size={16} /> Start Browser Session
              </Button>
            </>
          ) : (
            <>
              <Button onClick={() => {
                wsService.sendCommand('EXPORT_SIDE', { 
                  projectName: projectName ? `${projectName}_login_sequence` : 'Login_Sequence',
                  url: targetUrl,
                  commands: commands
                })
                clearCommands()
              }} variant="outline" className="gap-2 border-indigo-300 text-indigo-700 bg-indigo-50 hover:bg-indigo-100">
                <Save size={16} /> Save Login Sequence (.SIDE)
              </Button>
              <Button onClick={() => setCrawlMode('manualcrawl')} className={`gap-2 text-white shadow-sm ${crawlMode === 'manualcrawl' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-slate-400 hover:bg-slate-500'}`}>
                <MousePointerClick size={16} /> Manual Crawl
              </Button>
              <Button onClick={handleAutoCrawl} className={`gap-2 text-white shadow-sm ${crawlMode === 'autocrawl' ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-slate-400 hover:bg-slate-500'}`}>
                <Bot size={16} /> Auto Crawl
              </Button>
              <Button onClick={handleStop} variant="outline" className="gap-2 border-red-200 text-red-600 bg-red-50 hover:bg-red-100 hover:text-red-700">
                <Square size={16} /> Stop & Close Session
              </Button>
            </>
          )}
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Main Content Area */}
        <main className="flex-1 p-6 overflow-y-auto bg-blue-50/50">
          <div className="max-w-3xl mx-auto space-y-6">
            {!isRecording && commands.length === 0 ? (
              <div className="bg-white p-8 rounded-xl border border-blue-200 text-center space-y-4 shadow-sm">
                <Globe className="w-12 h-12 text-blue-400 mx-auto" />
                <h3 className="text-lg font-medium text-blue-900">Configure Recording Session</h3>
                <div className="flex flex-col max-w-md mx-auto gap-4">
                  <div>
                    <label className="text-sm text-blue-600 font-medium block text-left mb-1">Project Name</label>
                    <Input 
                      placeholder="MyProject" 
                      value={projectName}
                      onChange={(e) => setProjectName(e.target.value)}
                      className="bg-white border-blue-300 text-slate-900 placeholder:text-slate-400 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-blue-600 font-medium block text-left mb-1">Target URL</label>
                    <Input 
                      placeholder="https://example.com/login" 
                      value={targetUrl}
                      onChange={(e) => setTargetUrl(e.target.value)}
                      className="bg-white border-blue-300 text-slate-900 placeholder:text-slate-400 focus:border-blue-500"
                    />
                  </div>
                </div>
                <p className="text-sm text-blue-600">
                  Click start to launch the browser and begin recording.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <h3 className="font-semibold text-lg text-blue-900">Recording Timeline</h3>
                {commands.length === 0 ? (
                  <div className="p-12 text-center border border-dashed border-blue-300 rounded-lg text-blue-500 bg-white">
                    Listening for browser interactions...
                  </div>
                ) : (
                  <div className="space-y-3">
                    {commands.map((cmd, index) => (
                      <div key={cmd.id} className="bg-white border border-blue-200 px-6 py-4 rounded-md flex items-center justify-between shadow-sm">
                        <div className="flex items-center gap-6">
                          <span className="text-blue-400 font-mono text-sm w-4">{index + 1}</span>
                          <span className="border border-blue-200 text-blue-600 bg-blue-50 text-[11px] px-2 py-0.5 rounded-sm uppercase tracking-wider">{cmd.command}</span>
                          <span className="font-mono text-[13px] text-indigo-600">{cmd.target}</span>
                          {cmd.value && (
                            <span className="text-[13px] text-blue-600 ml-2">Value: "{cmd.value}"</span>
                          )}
                        </div>
                        {cmd.confidence && (
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-500">Locator Confidence</span>
                            <span className={`text-xs px-2 py-0.5 rounded-sm font-medium ${cmd.confidence > 0.9 ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                              {Math.round(cmd.confidence * 100)}%
                            </span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
