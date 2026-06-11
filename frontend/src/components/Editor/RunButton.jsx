import { useWorkspaceStore } from '../../stores/workspaceStore'
import { HiOutlinePlay } from 'react-icons/hi'

export default function RunButton() {
  const { fileTree, toggleTerminal, setBottomPanelTab } = useWorkspaceStore()

  // Auto-detect project type
  const detectRunner = () => {
    const files = fileTree.map(f => f.name)
    if (files.includes('package.json')) return 'npm run dev\r'
    if (files.includes('requirements.txt') || files.includes('app.py') || files.includes('main.py')) {
      const entry = files.includes('app.py') ? 'app.py' : 'main.py'
      return `python ${entry}\r`
    }
    if (files.includes('Makefile')) return 'make\r'
    if (files.includes('index.html')) return null // Handled by preview
    return null
  }

  const handleRun = () => {
    const cmd = detectRunner()
    if (!cmd) {
      alert('Could not automatically detect how to run this project.')
      return
    }

    // Open terminal tab
    toggleTerminal(true)
    setBottomPanelTab('terminal')

    // Send command to terminal
    document.dispatchEvent(new CustomEvent('aira_terminal_input', { detail: cmd }))
  }

  return (
    <button className="workspace-toolbar-btn text-aira-success" onClick={handleRun} title="Run Project">
      <HiOutlinePlay className="w-4 h-4" />
    </button>
  )
}
