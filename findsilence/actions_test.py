""" This module defines the tests and the behaviour of actions """

import unittest
from actions import (ActionHandler, register_handler, register_method, register,
                     emmit_action, clear, register_nostate_handler, Context)

class _Test(unittest.TestCase):
    def test_actionhandler(self):
        class Foo(ActionHandler):
            def __init__(self):
                ActionHandler.__init__(self)
                self.test = "foobar"
            
            @register_method('foo')
            def foo(self, state):
                return self.test
            
            @register_method('bar')
            def bar(self, state):
                return "bar"
        
        foo = Foo()
        self.assertEqual(emmit_action('foo'), ['foobar'])
        self.assertEqual(emmit_action('bar'), ['bar'])
    
    def test_removehandlers(self):
        class Foo(ActionHandler):
            def __init__(self):
                ActionHandler.__init__(self)
                self.test = "foobar"
            
            @register_method('foo')
            def foo(self, state):
                return self.test
        
        foo = Foo()
        register_handler('foo', lambda x: 'foo')
        self.assertEqual(emmit_action('foo'), ['foobar', 'foo'])
        foo.remove_handlers()
        self.assertEqual(emmit_action('foo'), ['foo'])

    def test_removeactions(self):
        class Foo(ActionHandler):
            def __init__(self):
                ActionHandler.__init__(self)
                self.test = "foobar"
            
            @register_method('foo')
            def foo(self, state):
                return self.test
        
        foo = Foo()
        register_handler('foo', lambda x: 'foo')
        self.assertEqual(emmit_action('foo'), ['foobar', 'foo'])
        foo.remove_actions()
        self.assertEqual(emmit_action('foo'), [])
    
    def test_multiple_deco_method(self):
        class Foo(ActionHandler):
            def __init__(self):
                ActionHandler.__init__(self)
                self.test = "foobar"
            
            @register_method('bar')
            @register_method('foo')
            def foo(self, state):
                return self.test
        
        foo = Foo()
        self.assertEqual(emmit_action('foo'), ['foobar'])
        self.assertEqual(emmit_action('bar'), ['foobar'])
    
    def test_multiple(self):
        @register('foo', 'bar')
        def baz(state):
            return 'foo-bar'
        self.assertEqual(emmit_action('foo'), ['foo-bar'])
        self.assertEqual(emmit_action('bar'), ['foo-bar'])
    
    def test_multiple_deco(self):
        @register('foo')
        @register('bar')
        def baz(state):
            return 'foo-bar'
        self.assertEqual(emmit_action('foo'), ['foo-bar'])
        self.assertEqual(emmit_action('bar'), ['foo-bar'])
        
    def test_register(self):
        @register('baz')
        def baz(state):
            return 'foo'
        
        @register('foo')
        def foo_bar(state):
            return "foo bar"
        self.assertEqual(emmit_action('foo'), ['foo bar'])
        self.assertEqual(emmit_action('baz'), ['foo'])
    
    def test_nostate(self):
        def baaz():
            return 'baaz'
        
        register_nostate_handler('baz', baaz)
        self.assertEqual(emmit_action('baz'), ['baaz'])
    
    def test_context(self):
        register_handler('bar', lambda x: 'bar')
        cont = Context()
        class Bar(ActionHandler):
            def __init__(self):
                ActionHandler.__init__(self, cont)
            
            @register_method('bar')
            def baar(self, state):
                return 'bar'
        bar = Bar()
        self.assertEqual(cont.emmit_action('bar'), ['bar'])
        self.assertEqual(emmit_action('bar'), ['bar'])
    
    def tearDown(self):
        clear()


if __name__ == '__main__':
    unittest.main()