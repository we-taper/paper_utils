import unittest

from main import TextAnno


class MyTestCase(unittest.TestCase):
    def test_markdown(self):
        a = TextAnno('see comments', color=(255, 0, 255), comments='comments')
        assert a.to_markdown() == '<div title="comments"><span style="color:rgb(255, 0, 255)">see comments</span></div>'


if __name__ == '__main__':
    unittest.main()
