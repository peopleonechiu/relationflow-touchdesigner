import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('browser_logic', Path(__file__).resolve().parents[1] / 'td' / 'browser_logic.py')
logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logic)

class StopTick(Exception): pass
class Pulse:
    def __init__(self): self.count = 0
    def pulse(self): self.count += 1
class Value:
    def eval(self): return True
class Node:
    def __init__(self):
        self.par = type('Pars', (), {'Run': Value(), 'reload': Pulse()})()
    def op(self, name): return self

class SlowBrowserTest(unittest.TestCase):
    def test_connection_that_takes_more_than_five_seconds_is_not_reloaded(self):
        node = Node()
        logic.comp = lambda: node
        logic.refresh_custom = lambda now: (_ for _ in ()).throw(StopTick())
        logic.table = lambda *args: None
        logic.state = {'initialized': True}
        logic.client = None
        for now in (1000, 1004, 1008, 1012):
            with patch.object(logic.time, 'monotonic', return_value=now):
                try: logic.tick()
                except StopTick: pass
        self.assertLessEqual(node.par.reload.count, 1, 'slow startup must not be repeatedly reloaded')

    def test_retry_occurs_after_full_grace_period(self):
        node = Node()
        logic.comp = lambda: node
        logic.refresh_custom = lambda now: (_ for _ in ()).throw(StopTick())
        logic.table = lambda *args: None
        logic.state = {'initialized': True}
        logic.client = None
        for now in (1000, 1015, 1059, 1060, 1061):
            with patch.object(logic.time, 'monotonic', return_value=now):
                try: logic.tick()
                except StopTick: pass
        self.assertEqual(node.par.reload.count, 1)

if __name__ == '__main__': unittest.main()
