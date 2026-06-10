import { useRef, useEffect } from 'react'
import Editor, { useMonaco } from '@monaco-editor/react'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { useThemeStore } from '../../stores/themeStore'

export default function MonacoEditor() {
  const { activeFile, updateFileContent, saveFile } = useWorkspaceStore()
  const { theme } = useThemeStore()
  const monaco = useMonaco()
  const editorRef = useRef(null)

  useEffect(() => {
    if (monaco) {
      // Define AIRA dark theme
      monaco.editor.defineTheme('aira-dark', {
        base: 'vs-dark',
        inherit: true,
        rules: [
          { background: '0a0e1a' }
        ],
        colors: {
          'editor.background': '#0a0e1a',
          'editor.lineHighlightBackground': '#111827',
          'editorLineNumber.foreground': '#64748b',
          'editorIndentGuide.background': '#1e293b',
          'editor.selectionBackground': '#1e293b',
        }
      })
      monaco.editor.setTheme(theme === 'dark' ? 'aira-dark' : 'vs-light')
    }
  }, [monaco, theme])

  const handleEditorDidMount = (editor) => {
    editorRef.current = editor
    
    // Add save command directly to editor as fallback
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      const currentModel = editor.getModel()
      if (currentModel) {
        const path = currentModel.uri.path.replace(/^\//, '') // simple extraction
        // In reality activeFile state is better
        const storeState = useWorkspaceStore.getState()
        if (storeState.activeFile) {
          storeState.saveFile(storeState.activeFile.path)
        }
      }
    })
  }

  const handleContentChange = (value) => {
    if (activeFile) {
      updateFileContent(activeFile.path, value || '')
    }
  }

  if (!activeFile) {
    return (
      <div className="flex-1 flex items-center justify-center bg-aira-surface">
        <div className="text-center text-aira-text-dim">
          <div className="w-16 h-16 mx-auto mb-4 opacity-20 bg-aira-primary/20 rounded-xl" />
          <p>No file is open</p>
          <p className="text-xs mt-2">Press <kbd className="px-1.5 py-0.5 rounded bg-aira-surface-2">Ctrl+P</kbd> to search files</p>
        </div>
      </div>
    )
  }

  const isNullContent = activeFile.content === null || activeFile.content === undefined
  const isEmptyContent = activeFile.content === ""

  if (isNullContent || isEmptyContent) {
    return (
      <div className="flex-1 flex items-center justify-center bg-aira-surface">
        <div className="text-center text-aira-text-dim">
          <p>{isNullContent ? "Unable to load file content" : "File is empty"}</p>
        </div>
      </div>
    )
  }

  // Get language from extension
  const getLanguage = (filename) => {
    const ext = filename.split('.').pop().toLowerCase()
    const map = {
      js: 'javascript', jsx: 'javascript', ts: 'typescript', tsx: 'typescript',
      py: 'python', json: 'json', md: 'markdown', css: 'css', html: 'html',
      yaml: 'yaml', yml: 'yaml', sh: 'shell'
    }
    return map[ext] || 'plaintext'
  }

  const editorValue = activeFile.content ?? "Unable to load file content"
  console.log(`EDITOR_CONTENT_LENGTH: ${editorValue.length}`)

  return (
    <div className="flex-1 w-full h-full relative">
      <Editor
        path={activeFile.path}
        value={editorValue}
        language={getLanguage(activeFile.name)}
        theme={theme === 'dark' ? 'aira-dark' : 'vs-light'}
        onMount={handleEditorDidMount}
        onChange={handleContentChange}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: 'JetBrains Mono, monospace',
          wordWrap: 'on',
          lineNumbersMinChars: 3,
          padding: { top: 16, bottom: 16 },
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          formatOnPaste: true,
        }}
        loading={
          <div className="flex items-center justify-center h-full">
            <div className="w-6 h-6 border-2 border-aira-border border-t-aira-primary rounded-full animate-spin" />
          </div>
        }
      />
    </div>
  )
}
