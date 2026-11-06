import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'td' / 'browser_logic.py'
spec = importlib.util.spec_from_file_location('browser_logic', path)
logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logic)


class TagsTest(unittest.TestCase):
    def test_trim_and_deduplicate(self):
        tags, status = logic.parse_tags(' riding, Riding,  beside,, ')
        self.assertEqual(tags, ('riding', 'beside'))
        self.assertEqual(status, 'Duplicate tags removed')

    def test_reject_empty_and_excess(self):
        for text in (' , ', 'x' * 101, ','.join('tag%d' % i for i in range(33))):
            self.assertEqual(logic.parse_tags(text)[0], ())

    def test_yolo_classes_are_checked(self):
        self.assertEqual(logic.parse_objects('person, Person, horse')[0], ('person', 'horse'))
        self.assertEqual(logic.parse_objects('person, unicorn')[0], ())
        self.assertEqual(logic.parse_objects('person, leather shoe', ('person', 'leather shoe'))[0],
                         ('person', 'leather shoe'))


if __name__ == '__main__':
    unittest.main()
