
__all__ = ['generateMenus']
from menu import MenuBase, GoBack

def generateMenus(stingGui):
    backString = '<<'
    class WhitelistRemoveMenu(MenuBase):
        title = 'Whitelist Remove'
        options = [
                None,
                None,
                None, 
                (backString,  GoBack)
                ]

        def onEnter(self):
            stingGui.addWhiteListFlag = False
            stingGui.removeWhiteListFlag = True

        def onBack(self):
            stingGui.addWhiteListFlag = False
            stingGui.removeWhiteListFlag = False

    class WhitelistAddMenu(MenuBase):
        title = 'Whitelist Add'
        options = [
                None,
                None,
                None, 
                (backString,  GoBack)
                ]

        def onEnter(self):
            stingGui.addWhiteListFlag = True
            stingGui.removeWhiteListFlag = False

        def onBack(self):
            stingGui.addWhiteListFlag = False
            stingGui.removeWhiteListFlag = False

    class ShutdownMenu(MenuBase):
        title = 'Shutdown?'
        options = [
                ('Shutdown', stingGui.stop),
                None, 
                None,
                (backString,  GoBack)
                ]

    class SetupMenu(MenuBase): 
        title = 'Setup'
        options = [
                ('Whitelist Add', WhitelistAddMenu()),
                ('Whitelist Remove', WhitelistRemoveMenu()),
                None,
                (backString, GoBack())

                ]

    class MainMenu(MenuBase): 
        options = [
                ('Setup', SetupMenu()),
                None,
                ('Shutdown', ShutdownMenu()),
                (backString, GoBack())
                ]

    class TopMenu(MenuBase):

        def onEnter(self):
            stingGui.fireEnable = True
            stingGui.toast = None

        def onLeave(self):
            stingGui.fireEnable = False
            stingGui.toast = None

        fontScale = .5
        options = [
                ('[ Menu ]', MainMenu())
                ]

    return TopMenu()
