import { HashRouter as Router, Routes, Route } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { RecorderScreen } from './pages/RecorderScreen'
import ConverterScreen from './pages/ConverterScreen'
import EditorScreen from './pages/EditorScreen'
import { useEffect } from 'react'
import { wsService } from './services/api'

function App() {
  useEffect(() => {
    wsService.connect()
    return () => {
      wsService.disconnect()
    }
  }, [])

  return (
    <Router>
      <div className="min-h-screen bg-blue-50 text-slate-900 font-sans">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/recorder" element={<RecorderScreen />} />
          <Route path="/converter" element={<ConverterScreen />} />
          <Route path="/editor" element={<EditorScreen />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
