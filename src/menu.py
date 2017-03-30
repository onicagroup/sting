#!/usr/bin/env python

class MenuMeta(type):
    @staticmethod
    def makeDummyFunction(msg):
        def dummy():
            print msg
        return dummy

    def __init__(cls, name, parents, dct):
        options = ()
        targets = {}

        if 'title' not in dct:
            cls.title = ''

        if 'options' in dct:
            options = dct['options']
            for i, option in enumerate(options):
                if option is None:
                    options[i] = ('',None)
                elif type(option) == str:
                    f = MenuMeta.makeDummyFunction(option + ' stub called')
                    targets[option] = f
                    options[i] = (option, f)
                elif type(option) in (tuple, list):
                    target = option[1]
                    if len(option) != 2:
                        raise RuntimeError('Option item must be type str or type list, tuple with len == 2')
                    if type(option[0]) != str:
                        raise RuntimeError('Option first item must be type str')

                    if ( not callable(target) 
                            and not isinstance(target, MenuBase) 
                            and not target == GoBack 
                            and not isinstance(target, GoBack)
                            ):
                        raise RuntimeError('Option second item must be callable, or a menu, or a GoBack().')

                    targets[option[0]] = option[1]


        super(MenuMeta, cls).__init__(name, parents, dct)
        cls.options = options
        cls.targets = targets
        cls.back = None


class GoBack(object): 
    pass


class MenuBase(object):
    __metaclass__ = MenuMeta


    def goBack(self):
        if self.back:
            self.onBack()
            self.back.onEnter()
            return self.back
        return self

    # When menu is left to enter another menu, but not because of GoBack
    def onLeave(self):
        pass

    # When "going back"
    def onBack(self):
        pass

    # When menu is selected, either from another menu, or GoBack()
    def onEnter(self):
        pass

    def select(self, item):
        # Special case, item is "GoBack" object
        if item == GoBack or isinstance(item, GoBack):
            return self.goBack()

        if len(self.options) - 1 < item:
            print('No item #%d in %s' % (item, self.__class__.__name__))
            return self

        option = self.options[item]

        name, target = option
        if target == GoBack or isinstance(target, GoBack):
            return self.goBack()
        elif isinstance(target, MenuBase):
            target.back = self
            target.back.onLeave()
            target.onEnter()
            return target
        elif callable(target):
            target()
            return self
        else:
            return self



    def dump(self, indent = 0):
        ii = ' ' * indent
        print ii, '>', self.title
        for option in self.options:
            if option is None: continue
            name, target = option
            print ii, ' ', name,
            if target == GoBack or isinstance(target, GoBack):
                print '<-- Back'
            elif isinstance(target, MenuBase):
                print ':'
                target.dump(indent + 1)
            elif callable(target):
                print '<function>'
            else:
                print target









if __name__ == '__main__':
    class ShutdownMenu(MenuBase):
        title = 'Shutdown?'

        options = [
                'Shutdown',
                None,
                None, 
                ('Cancel',  GoBack)
                ]

    class TopMenu(MenuBase): 
        title = ''
        options = [
                None,
                None,
                None, 
                ('Shutdown', ShutdownMenu())

                ]
    menu = TopMenu()
    print menu
    menu = menu.select(3)
    print menu
    menu = menu.select(0)
    print menu
    menu = menu.select(3)
    print menu


