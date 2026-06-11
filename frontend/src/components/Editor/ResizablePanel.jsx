import { useRef, useCallback, useEffect } from 'react'

/**
 * ResizablePanel — a drag-resizable container.
 * 
 * Props:
 *   direction: 'horizontal' | 'vertical'
 *   size: current size in px
 *   onResize: (newSize) => void
 *   minSize: minimum px
 *   maxSize: maximum px
 *   side: 'left' | 'right' | 'top' | 'bottom' — where the handle is placed
 *   children: content
 *   className: extra classes
 *   style: extra inline styles
 */
export default function ResizablePanel({
  direction = 'horizontal',
  size,
  onResize,
  minSize = 100,
  maxSize = 800,
  side = 'right',
  children,
  className = '',
  style = {},
}) {
  const isResizing = useRef(false)
  const startPos = useRef(0)
  const startSize = useRef(0)

  const handleMouseDown = useCallback((e) => {
    e.preventDefault()
    isResizing.current = true
    startPos.current = direction === 'horizontal' ? e.clientX : e.clientY
    startSize.current = size
    document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize'
    document.body.style.userSelect = 'none'
  }, [direction, size])

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing.current) return
      const currentPos = direction === 'horizontal' ? e.clientX : e.clientY
      const delta = currentPos - startPos.current

      let newSize
      if (side === 'right' || side === 'bottom') {
        newSize = startSize.current + delta
      } else {
        newSize = startSize.current - delta
      }

      newSize = Math.max(minSize, Math.min(maxSize, newSize))
      onResize(newSize)
    }

    const handleMouseUp = () => {
      if (isResizing.current) {
        isResizing.current = false
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [direction, side, minSize, maxSize, onResize])

  const isHorizontal = direction === 'horizontal'

  const handleStyle = isHorizontal
    ? {
        position: 'absolute',
        top: 0,
        [side === 'right' ? 'right' : 'left']: 0,
        width: '4px',
        height: '100%',
        cursor: 'col-resize',
        zIndex: 10,
      }
    : {
        position: 'absolute',
        [side === 'bottom' ? 'bottom' : 'top']: 0,
        left: 0,
        width: '100%',
        height: '4px',
        cursor: 'row-resize',
        zIndex: 10,
      }

  return (
    <div
      className={`relative ${className}`}
      style={{
        ...style,
        [isHorizontal ? 'width' : 'height']: `${size}px`,
        flexShrink: 0,
      }}
    >
      {children}
      <div
        className="resize-handle"
        style={handleStyle}
        onMouseDown={handleMouseDown}
      />
    </div>
  )
}
