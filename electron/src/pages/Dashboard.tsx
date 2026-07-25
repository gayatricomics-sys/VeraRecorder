import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Plus, Settings, History, FileCode, Wand2 } from 'lucide-react'

interface ExportFile {
  name: string;
  size: number;
  modified: number;
  path: string;
}

export function Dashboard() {
  const navigate = useNavigate()
  const [exports, setExports] = useState<ExportFile[]>([])

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/exports')
      .then(res => res.json())
      .then(data => {
        if (data && data.files) {
          setExports(data.files)
        }
      })
      .catch(err => console.error('Failed to fetch exports', err))
  }, [])

  const handleOpenExport = (filename: string) => {
    if (filename.endsWith('.side')) {
      navigate(`/editor?file=${encodeURIComponent(filename)}`)
    } else {
      fetch(`http://127.0.0.1:8000/api/exports/open?filename=${encodeURIComponent(filename)}`, { method: 'POST' })
        .catch(err => console.error('Failed to open export', err))
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight">VeraRecorder</h1>
          <p className="text-blue-600 mt-2 text-lg">Veracode Login Script Generator</p>
        </div>
        <Button size="lg" onClick={() => navigate('/recorder')} className="gap-2 bg-indigo-600 hover:bg-indigo-700">
          <Plus size={20} />
          New Recording Project
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
        <Card onClick={() => navigate('/converter')} className="bg-white border-blue-200 shadow-sm hover:border-blue-400 transition-all cursor-pointer group">
          <CardHeader>
            <Wand2 className="w-8 h-8 text-indigo-600 mb-2 group-hover:scale-110 transition-transform" />
            <CardTitle className="text-blue-900">Script Converter</CardTitle>
            <CardDescription className="text-blue-600">Convert Playwright and Cypress scripts to Veracode DAST format</CardDescription>
          </CardHeader>
        </Card>
        <Card className="bg-white border-blue-200 shadow-sm hover:border-blue-400 transition-all cursor-pointer">
          <CardHeader>
            <Settings className="w-8 h-8 text-emerald-600 mb-2" />
            <CardTitle className="text-blue-900">Configuration</CardTitle>
            <CardDescription className="text-blue-600">Manage browser profiles and proxies</CardDescription>
          </CardHeader>
        </Card>

        <Card className="bg-white border-blue-200 shadow-sm hover:border-blue-400 transition-all">
          <CardHeader>
            <History className="w-8 h-8 text-amber-500 mb-2" />
            <CardTitle className="text-blue-900">Export History</CardTitle>
            <CardDescription className="text-blue-600">View previously generated .side scripts</CardDescription>
          </CardHeader>
          <CardContent>
            {exports.length === 0 ? (
              <p className="text-sm text-slate-500 italic">No recordings found</p>
            ) : (
              <ul className="space-y-2 text-sm text-slate-700">
                {exports.slice(0, 5).map(f => (
                  <li 
                    key={f.name} 
                    className="flex justify-between items-center py-2 px-2 -mx-2 border-b border-blue-100 last:border-0 cursor-pointer hover:bg-blue-50 rounded transition-colors"
                    onClick={() => handleOpenExport(f.name)}
                  >
                    <div className="flex flex-col gap-0.5">
                      <div className="flex items-center gap-2">
                        <FileCode className="w-4 h-4 text-blue-600" />
                        <span className="font-medium text-blue-900">{f.name}</span>
                      </div>
                      <span className="text-[10px] text-blue-400/80 font-mono pl-6" title={f.path}>{f.path}</span>
                    </div>
                    <span className="text-blue-500 text-xs">
                      {new Date(f.modified * 1000).toLocaleDateString()} {new Date(f.modified * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
