import wx


## This module displays whatever is in the cell the mouse is over.
class LookFrame(wx.Frame):
    def __init__(self, *args):
        wx.Frame.__init__(self, *args)
        self.text = wx.TextCtrl(self)


    ## Replace the text in the frame.
    def setText(self, lines):
        self.text.SetValue("\n".join(lines))



def makeWindow(parent, loc):
    window = LookFrame(parent)
    window.SetPosition(loc)
    window.Show()
    return window
