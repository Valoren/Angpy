import frame
import mainApp
import drawingcontext

## Frame displaying the message history.
class MessageFrame(frame.Frame):
    def __init__(self):
        super(MessageFrame, self).__init__(0, 24, 80, 10)
        # message history buffer
        self.messages = ['Starting Pyrel...']

    def addMessage(self, *args):
        msg = " ".join([a.encode('utf-8') for a in args])
        self.messages.append(msg)
        if len(self.messages) > self.height:
            self.messages = self.messages[-self.height:]
        self.Show()

    def Show(self):
        for i in range(10):
            self.window.move(i,0)
            self.window.clrtoeol()
            if i < len(self.messages):
                self.window.addstr(self.messages[i])
        self.windowRefresh()

# application interface to append message to history
def message(*args):
    message = " ".join(map(unicode, args))
    mainApp.getApp().messageFrame.addMessage(message)


