def init(gameMap):
    # Save this import until right before we need it.
    import gui
    import prompt
    import messageFrame
    import animation
    import keymap
    gui.prompt.setModule(prompt)
    gui.messenger.setModule(messageFrame)
    gui.animation.setModule(animation)
    gui.keymap = keymap.WxKeymap()
    import mainApp
    mainApp.makeApp(gameMap)

