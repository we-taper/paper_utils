from pathlib import Path
from typing import List, Tuple

import PyQt5
import popplerqt5
import os

_WHITE = (255, 255, 255)


class TextAnno:
    def __init__(self, main_text, color: Tuple[int, int, int] = _WHITE, comments=''):
        self.comments = comments
        self.color = color
        self.main_text = main_text

    def to_markdown(self) -> str:
        txt = '<span style="color:rgb' + str(self.color) + '">' + self.main_text + '</span>'
        if self.comments != '':
            txt = r'<div title="' + self.comments + '">' + txt + '</div>'
        return txt


def read_annotations(pdf_path) -> List[TextAnno]:
    doc = popplerqt5.Poppler.Document.load(pdf_path)
    ret = []

    for i in range(doc.numPages()):
        page = doc.page(i)
        annotations = page.annotations()
        pwidth, pheight = page.pageSize().width(), page.pageSize().height()
        for annotation in annotations:
            if isinstance(annotation, popplerqt5.Poppler.Annotation):
                if isinstance(annotation, popplerqt5.Poppler.HighlightAnnotation):
                    quads = annotation.highlightQuads()
                    txt = ""
                    for quad in quads:
                        rect = (quad.points[0].x() * pwidth,
                                quad.points[0].y() * pheight,
                                quad.points[2].x() * pwidth,
                                quad.points[2].y() * pheight)
                        # noinspection PyUnresolvedReferences
                        bdy = PyQt5.QtCore.QRectF()
                        bdy.setCoords(*rect)
                        txt = txt + str(page.text(bdy)) + ' '

                    # Get color. Note that getRgb returns a tuple of (R,G,B,Alpha)
                    color = annotation.style().color().getRgb()[:3]
                    if annotation.contents():
                        ret.append(TextAnno(txt, color=color, comments=annotation.contents))
                    else:
                        ret.append(TextAnno(txt, color=color))
                elif isinstance(annotation, popplerqt5.Poppler.TextAnnotation):
                    if annotation.contents():
                        ret.append(TextAnno(annotation.contents()))
    return ret


class Document:
    def __init__(self, pdf_path, annotations: List[TextAnno], title=''):
        self.pdf_path = Path(pdf_path)
        self.annotations = annotations
        self.title = title

    def to_markdown(self) -> str:
        if self.title != '':
            title = self.title
        else:
            title = self.pdf_path.name
        summary = f'<a href="{self.pdf_path}">{title}</a>'
        ret = _template.replace('SUMMARY', summary)
        ret = ret + _template_2.replace("MAIN", '<br>\n'.join('- ' + a.to_markdown() for a in self.annotations))
        return ret


_template = """<details>
  <summary>SUMMARY</summary>"""
_template_2 = """<p>
MAIN
</p>
</details>
"""


def guess_pdf_title(pdf_path):
    # TODO: make better guess
    return pdf_path

def scan_dir(directory):
    ret = []
    for path, directories, files in os.walk(directory, topdown=True):
        for file in files:
            if file.endswith('.pdf'):
                file = os.path.join(path, file)
                annotation = read_annotations(file)
                ret.append(Document(file, annotations=annotation, title=''))

    ret = '\n'.join(a.to_markdown() for a in ret)
    return ret
if __name__ == "__main__":
    # test = '1704.05018.pdf'
    # anno = read_annotations(test)
    # doc = Document(test, annotations=anno, title=guess_pdf_title(test))
    # print(doc.to_markdown())
    # print(scan_dir('.'))
    target = '/workdir'
    target_md = scan_dir(target)
    print(target_md)
