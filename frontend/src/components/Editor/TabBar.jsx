import { useWorkspaceStore } from '../../stores/workspaceStore'
import { HiX, HiDocument } from 'react-icons/hi'

export default function TabBar() {
  const { openFiles, activeFile, closeFile, setActiveFile, unsavedFiles } = useWorkspaceStore()

  if (openFiles.length === 0) return null

  return (
    <div className="flex overflow-x-auto bg-aira-surface border-b border-aira-border no-scrollbar hide-scrollbar h-10">
      {openFiles.map(file => {
        const isActive = activeFile?.path === file.path
        const isUnsaved = unsavedFiles.has(file.path)

        return (
          <div
            key={file.path}
            onClick={() => setActiveFile(file.path)}
            className={`flex items-center gap-2 px-3 py-2 min-w-[120px] max-w-[200px] border-r border-aira-border cursor-pointer group transition-colors select-none ${
              isActive 
                ? 'bg-aira-bg text-aira-text border-t-2 border-t-aira-primary' 
                : 'bg-aira-surface text-aira-text-muted hover:bg-aira-surface-3 border-t-2 border-t-transparent'
            }`}
          >
            <HiDocument className="w-4 h-4 flex-shrink-0 text-aira-text-dim" />
            
            <span className="truncate flex-1 text-sm">{file.name}</span>
            
            <button
              onClick={(e) => {
                e.stopPropagation()
                closeFile(file.path)
              }}
              className={`flex-shrink-0 p-0.5 rounded transition-all ${
                isUnsaved 
                  ? 'opacity-100 bg-aira-accent/20 w-2.5 h-2.5 rounded-full hover:bg-transparent hover:w-auto hover:h-auto group-hover:block'
                  : 'opacity-0 group-hover:opacity-100 hover:bg-white/10'
              }`}
            >
              {isUnsaved ? (
                <span className="group-hover:hidden block w-full h-full rounded-full bg-aira-accent" />
              ) : null}
              <HiX className={`w-3.5 h-3.5 ${isUnsaved ? 'hidden group-hover:block' : ''}`} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
