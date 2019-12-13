## This module provides any overrides required of methods in 
# gui/base/animation.py
# In addition, it must implement the receiveAnimation method, which passes
# the animation to the relevant UI handler
import mainApp

def receiveAnimation(generator):
    mainApp.getPanel().receiveAnimation(generator)

