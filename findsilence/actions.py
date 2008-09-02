# actions - Handle actions by defining handlers
# Copyright (C) 2008 Florian Mayer

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Increment by one everytime the file is changed!
__version__ = 2


import inspect
import warnings

from collections import defaultdict


actions = defaultdict(list)


class StopHandling(Exception):
    """ Raising this exception in an action handler prevents all the 
    successive handlers from being executed. """
    pass


def require(version):
    """ Raise ImportWarning if version of this file is older than the value 
    passed to require. """
    if __version__ < version:
        raise ImportWarning("Version of actions is older than the required one")
    

def register_handler(action, exc, *args, **kwargs):
    """ Register exc to the action action with additional paramenters to be 
    passed to the hook function. 
    
    Registering multiple hooks for the same 
    action will execute them in order of registration. """
    actions[action].append((exc, args, kwargs, False))


def register_nostate_handler(action, exc, *args, **kwargs):
    """ Register handler that does *NOT* take state as first argument. 
    
    Please only use this rarely and only for handlers that would only take 
    None as state. Useful for binding directly to framework functions. """
    actions[action].append((exc, args, kwargs, True))
    

def remove_handler(action, exc):
    """ Remove the function exc from the list of hooks for action. """
    actions[action] = [x for x in actions[action] if not x[0] == exc] 
    

def delete_action(action):
    """ Delete all handlers associated with action. """
    del actions[action]


def emmit_action(action, state=None):
    """ Call all the functions associated with action with state as first 
    argument, unless they are nostate handlers. """
    for callback in actions[action]:
        exc, args, kwargs, no_state = callback
        try:
            if no_state:
                # Do not pass state to nostate handlers.
                exc(*args, **kwargs)
            else:
                exc(state, *args, **kwargs)
        except StopHandling:
            break


def register_method(action, lst=None):
    """ Associate decorated method with action. Be sure to call 
    ActionHandler.__init__ in your classes __init__ method. 
    """
    if lst is not None:
        # Developer still seems to use old version including _decorators.
        warnings.warn("Using register_method with lst is deprecated", 
                   DeprecationWarning, 2)
    def decorate(f):
        f._bind_to = action
        return f
    return decorate


def register(action):
    """ Associate decorated function with action. """
    def decorate(f):
        register_handler(action, f)
        return f
    return decorate


class ActionHandler:
    """ Subclass this class for classes using the register_method decorators 
    with one or more of its methods.
    Make sure to call the __init__, otherwise the handlers will
    not be bound. 
    """
    def __init__(self):
        self.__actions = []
        for name, method in inspect.getmembers(self):
            if hasattr(method, '_bind_to'):
                self.__actions.append(method._bind_to)
                register_handler(method._bind_to, method)
                
    def remove_actions(self):
        """ This deletes all actions that were associated with methods of the 
        class.
        
        Please note that it doesn't only delete the handlers, but also any 
        other handlers that may be associated with the given action. 
        """
        for action in self.__actions:
            delete_action(action)
    
    def remove_handlers(self):
        """ This deassociates all handlers of this class from the actions. 
        
        In difference to remove_action this does not delete any other handlers 
        """
        for action in self.__actions:
            for handler in actions[action]:
                handler_func = handler[0]
                if inspect.ismethod(handler_func) and \
                   handler_func.im_self is self:
                    remove_handler(action, handler_func)


# Testing purposes
if __name__ == '__main__':
    class Foo(ActionHandler):
        def __init__(self):
            ActionHandler.__init__(self)
            self.test = "foobar"
        
        @register_method('foo')
        def foo(self, state):
            print self.test
        
        @register_method('bar')
        def bar(self, state):
            print "bar"
    
    
    @register('baz')
    def baz(state):
        print 'foo'
    
    
    @register('foo')
    def foo_bar(self):
        print "foo bar"
    
    
    foo = Foo()
    print "--"    
    emmit_action('foo')
    print "--"
    emmit_action('bar')
    print "--"
    emmit_action('baz')
    # Check remove_handlers.
    print "--"
    foo.remove_handlers()
    emmit_action('foo')
    