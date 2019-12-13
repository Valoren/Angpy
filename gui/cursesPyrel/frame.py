import curses

## Base Class For all UI Frame elements, containing its
# extent, as well as its specialized character buffer
# \todo support response to resizing of terminal display during runtime
class Frame(object):
    def __init__(self, left, top, width, height):
        ## extent of frame
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        ## display buffer
        self.window = curses.newpad(height+1, width+1)

    #Updates the main curses screen buffer with the contents
    # of this frame's window
    def windowRefresh(self):
        self.window.noutrefresh(0, 0, self.top, self.left,
                            self.top + self.height - 1,
                            self.left + self.width - 1)

