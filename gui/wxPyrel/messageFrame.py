## Displays the message history.

import wx

## Singleton message window.
window = None
class MessageFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title = "Message history")
        panel = wx.ScrolledWindow(self)
        self.text = wx.TextCtrl(panel, style = wx.TE_MULTILINE)



def makeWindow(parent, pos):
    global window
    window = MessageFrame(parent)
    window.SetPosition(pos)
    window.Show()


def message(*args):
    message = " ".join(map(unicode, args))
    # Only modify the UI when in the main thread.
    wx.CallAfter(window.text.write, message + "\n")


