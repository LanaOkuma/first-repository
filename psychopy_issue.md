Having this issue on a fresh Anaconda install (Python 3.8.8), pip installed PsychoPy 2021.2.0, pyglet 1.4.11, Windows 10.

Using the "working example" script found here: https://www.psychopy.org/coder/globalKeys.html

Pressing `ctrl-q` leads to the following dump in PowerShell:

```
Exception ignored on calling ctypes callback function: <function Win32Window._get_window_proc.<locals>.f at 0x00000297F3D96160>
Traceback (most recent call last):
  File "C:\ProgramData\Anaconda3\lib\site-packages\pyglet\window\win32\__init__.py", line 665, in f
    result = event_handler(msg, wParam, lParam)
  File "C:\ProgramData\Anaconda3\lib\site-packages\pyglet\window\win32\__init__.py", line 736, in _event_key
    self.dispatch_event(ev, symbol, modifiers)
  File "C:\ProgramData\Anaconda3\lib\site-packages\pyglet\window\__init__.py", line 1330, in dispatch_event
    if EventDispatcher.dispatch_event(self, *args) != False:
  File "C:\ProgramData\Anaconda3\lib\site-packages\pyglet\event.py", line 425, in dispatch_event
    if getattr(self, event_type)(*args):
  File "C:\ProgramData\Anaconda3\lib\site-packages\psychopy\visual\backends\pygletbackend.py", line 422, in onKey
    event._onPygletKey(evt, modifiers)
  File "C:\ProgramData\Anaconda3\lib\site-packages\psychopy\event.py", line 238, in _onPygletKey
    _process_global_event_key(thisKey, modifiers)
  File "C:\ProgramData\Anaconda3\lib\site-packages\psychopy\event.py", line 259, in _process_global_event_key
    r = event.func(*event.func_args, **event.func_kwargs)
  File "C:\ProgramData\Anaconda3\lib\site-packages\psychopy\core.py", line 85, in quit
    sys.exit(0)  # quits the python session entirely
SystemExit: 0
```

However the program keeps running (still running for a short time, then eventually hangs).

Setting any key to quit results in the same error - for example,  `event.globalKeys.add(key='a', func=core.quit)`.

Having the program randomly quit (putting `core.quit()` at any point) does not cause the error. I also tried a workaround with iohub:
```
from psychopy.iohub.client import launchHubServer 
io = launchHubServer()
kb = io.devices.keyboard

events = kb.getKeys()
for kbe in events:
    if kbe.key == 'q':
        core.quit()
```
Which works totally fine.

