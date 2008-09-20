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

"""

Decorators
==========
It is also possible to register handlers using decorators.

Functions
---------
You can use the register decorator in order to register a function to an
action.

>>> @register("baz")
... def baz(state):
...     print state
... 
>>> emmit_action("baz", "state")
state
>>> 

Bound methods
-------------
If you want to bind bound methods of your instances to actions, you need to
subclass ActionHandler and call its __init__ in the __init__ of your class
so that it registers the handlers once an instance is created.
The methods can be bound to a actions using the register_method decorator.

>>> class Handlers(ActionHandler):
...     def __init__(self):
...             ActionHandler.__init__(self)
...     @register_method("foo")
...     def foo(self, state):
...             print "foo", state
... 
>>> handlers = Handlers()
>>> emmit_action("foo", "this is the state")
foo this is the state
>>> 

Context
=======
The functions exposed at module level use the default context.
If you need serveral parts of your application to use actions 
independantely, specify a context object for each of them, and use 
its methods and/or pass itto the constructor of ActionHandler or 
to register when using decorators.
"""

# Increment by one everytime the file is changed!
__version__ = 3

import inspect
import warnings

from collections import defaultdict


def require(version):
    """ Raise ImportWarning if version of this file is older than the value 
    passed to require. """
    if __version__ < version:
        raise ImportWarning("Version of actions is older than the required one")


class StopHandling(Exception):
    """ Raising this exception in an action handler prevents all the 
    successive handlers from being executed. """
    pass


class Context:
    """ The context in which the actions are defined. A default context is 
    created and its methods are exposed at module level automatically. 
    You may want to use contexts if you have got two independant things that
    both need to use actions, then you can define a context for each of them.
    """
    def __init__(self):
        self.actions = defaultdict(list)
        
    def register_handler(self, action, exc, *args, **kwargs):
        """ Register exc to the action action with additional paramenters to be 
        passed to the hook function. 
        
        Registering multiple hooks for the same 
        action will execute them in order of registration. """
        self.actions[action].append((exc, args, kwargs, False))
    
    def register_nostate_handler(self, action, exc, *args, **kwargs):
        """ Register handler that does *NOT* take state as first argument. 
        
        Please only use this rarely and only for handlers that would only take 
        None as state. Useful for binding directly to framework functions. """
        self.actions[action].append((exc, args, kwargs, True))
        
    def remove_handler(self, action, exc):
        """ Remove the function exc from the list of hooks for action. """
        self.actions[action] = [x for x in self.actions[action]
                                if not x[0] is exc]
    
    def delete_action(self, action):
        """ Delete all handlers associated with action. """
        del self.actions[action]
    
    def emmit_action(self, action, state=None):
        """ Call all the functions associated with action with state as first 
        argument, unless they are nostate handlers. """
        for callback in self.actions[action]:
            exc, args, kwargs, no_state = callback
            try:
                if no_state:
                    # Do not pass state to nostate handlers.
                    exc(*args, **kwargs)
                else:
                    exc(state, *args, **kwargs)
            except StopHandling:
                break


# Create default context and expose its methods on module level.
# This is useful for people who only use one context in their program.
_inst = Context()
register_handler = _inst.register_handler
register_nostate_handler = _inst.register_nostate_handler
remove_handler = _inst.remove_handler
delete_action = _inst.delete_action
emmit_action = _inst.emmit_action


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


def register(action, context=_inst):
    """ Associate decorated function with action. """
    def decorate(f):
        context.register_handler(action, f)
        return f
    return decorate


class ActionHandler:
    """ Subclass this class for classes using the register_method decorators 
    with one or more of its methods.
    Make sure to call the __init__, otherwise the handlers will
    not be bound. 
    """
    def __init__(self, context=_inst):
        self.__actions = []
        self.context = context
        for name, method in inspect.getmembers(self):
            if hasattr(method, '_bind_to'):
                self.__actions.append(method._bind_to)
                self.context.register_handler(method._bind_to, method)
                
    def remove_actions(self):
        """ This deletes all actions that were associated with methods of the 
        class.
        
        Please note that it doesn't only delete the handlers, but also any 
        other handlers that may be associated with the given action. 
        """
        for action in self.__actions:
            self.context.delete_action(action)
    
    def remove_handlers(self):
        """ This deassociates all handlers of this class from the actions. 
        
        In difference to remove_action this does not delete any other handlers 
        """
        for action in self.__actions:
            for handler in self.context.actions[action]:
                handler_func = handler[0]
                if inspect.ismethod(handler_func) and \
                   handler_func.im_self is self:
                    self.context.remove_handler(action, handler_func)


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
    
    def baaz():
        print 'baaz'
    
    register_nostate_handler('baz', baaz)
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
    