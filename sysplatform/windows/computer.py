from core.computer.interfaces import ComputerController

class WindowsComputerController(ComputerController):
    def __init__(self):
        raise NotImplementedError("Windows computer controller is not yet fully implemented.")
        
    @property
    def application(self):
        raise NotImplementedError()
        
    @property
    def window(self):
        raise NotImplementedError()
        
    @property
    def mouse(self):
        raise NotImplementedError()
        
    @property
    def keyboard(self):
        raise NotImplementedError()
        
    @property
    def clipboard(self):
        raise NotImplementedError()
        
    @property
    def screen(self):
        raise NotImplementedError()
        
    @property
    def browser(self):
        raise NotImplementedError()
        
    @property
    def observer(self):
        raise NotImplementedError()
