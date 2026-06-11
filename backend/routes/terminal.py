"""
AIRA — Terminal Routes
WebSocket namespace for PTY Terminal.
"""

import os
import pty
import subprocess
import select
import shlex
import threading
from flask import request, current_app
from flask_socketio import Namespace, emit
from flask_jwt_extended import decode_token

from models.project import Project
from utils.logger import get_logger

logger = get_logger("terminal")

class TerminalNamespace(Namespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.terminals = {}  # sid -> { 'fd': int, 'child_pid': int, 'thread': Thread }

    def on_connect(self):
        # We need to authenticate using the token sent in the query string or headers
        # Since SocketIO in browser often can't send custom headers during handshake,
        # we expect `token` in query args.
        pass

    def on_start(self, data):
        """Start a new terminal session."""
        token = data.get('token')
        project_id = data.get('project')
        
        if not token:
            emit('terminal_output', {'data': '\r\n[AIRA Terminal] No token provided.\r\n'})
            return

        try:
            decoded = decode_token(token)
            user_id = decoded.get("sub")
        except Exception as e:
            emit('terminal_output', {'data': f'\r\n[AIRA Terminal] Auth error: {e}\r\n'})
            return

        # Determine working directory
        cwd = current_app.config.get("WORKSPACE_FOLDER", "/app/data/workspace")
        if project_id:
            project = Project.find_by_id(project_id, user_id=user_id)
            if project and project.get("path"):
                cwd = project["path"]

        # Ensure directory exists
        os.makedirs(cwd, exist_ok=True)

        try:
            # Fork a new PTY
            (child_pid, fd) = pty.fork()
            if child_pid == 0:
                # Inside child process
                # Set terminal env vars
                os.environ["TERM"] = "xterm-256color"
                os.environ["PS1"] = "\\u@aira:\\w\\$ "
                # We need to change to the project directory
                os.chdir(cwd)
                # Execute bash
                subprocess.run(["bash"])
                # Exit when bash exits
                os._exit(0)
            else:
                # Inside parent process
                self.terminals[request.sid] = {
                    'fd': fd,
                    'child_pid': child_pid
                }
                
                # Start a background thread to read from the PTY and emit to socket
                def read_and_forward_output():
                    max_read_bytes = 1024 * 20
                    while True:
                        socketio_sid = request.sid
                        if socketio_sid not in self.terminals:
                            break
                        
                        try:
                            # Use select to wait for output
                            timeout_sec = 0.5
                            (data_ready, _, _) = select.select([fd], [], [], timeout_sec)
                            if data_ready:
                                output = os.read(fd, max_read_bytes).decode('utf-8', errors='replace')
                                if output:
                                    self.socketio.emit('terminal_output', {'data': output}, to=socketio_sid, namespace=self.namespace)
                                else:
                                    # EOF
                                    break
                        except Exception as e:
                            logger.error(f"PTY read error: {e}")
                            break
                    
                    # Cleanup on exit
                    if socketio_sid in self.terminals:
                        self.socketio.emit('terminal_output', {'data': '\r\n[AIRA Terminal] Process exited.\r\n'}, to=socketio_sid, namespace=self.namespace)
                        del self.terminals[socketio_sid]

                thread = self.socketio.start_background_task(read_and_forward_output)
                self.terminals[request.sid]['thread'] = thread

                emit('terminal_output', {'data': f'\r\n[AIRA Terminal] Started session in {cwd}\r\n'})

        except Exception as e:
            logger.error(f"Failed to start terminal: {e}")
            emit('terminal_output', {'data': f'\r\n[AIRA Terminal] Failed to start: {e}\r\n'})

    def on_terminal_input(self, data):
        """Handle input from the client and send to PTY."""
        sid = request.sid
        if sid in self.terminals:
            fd = self.terminals[sid]['fd']
            input_data = data.get('data', '')
            try:
                os.write(fd, input_data.encode('utf-8'))
            except Exception as e:
                logger.error(f"PTY write error: {e}")

    def on_resize(self, data):
        """Handle terminal resize event."""
        sid = request.sid
        if sid in self.terminals:
            fd = self.terminals[sid]['fd']
            cols = data.get('cols', 80)
            rows = data.get('rows', 24)
            # In a real robust implementation, we would use fcntl and termios to set window size
            # For simplicity, we just skip it here or use a basic approach.
            import termios
            import struct
            import fcntl
            try:
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
            except Exception as e:
                logger.warning(f"Could not resize terminal: {e}")

    def on_disconnect(self):
        """Cleanup when client disconnects."""
        sid = request.sid
        if sid in self.terminals:
            child_pid = self.terminals[sid]['child_pid']
            try:
                # Terminate the child process
                os.kill(child_pid, 9)
                os.waitpid(child_pid, 0)
            except Exception as e:
                logger.error(f"Error killing terminal process: {e}")
            
            try:
                os.close(self.terminals[sid]['fd'])
            except Exception:
                pass
            
            del self.terminals[sid]
            logger.info(f"Terminal session {sid} cleaned up.")
