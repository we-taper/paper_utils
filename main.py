import os
import re
from pathlib import Path
from typing import List, Tuple

import PyQt5
import arxiv
import popplerqt5
from loguru import logger
from pdfminer.pdffont import PDFUnicodeNotDefined
from pdftitle import get_title_from_file

_WHITE = (255, 255, 255)


class TextAnno:
    def __init__(self, main_text, color: Tuple[int, int, int] = _WHITE, comments=''):
        self.comments = comments
        self.color = color
        self.main_text = main_text

    def to_markdown(self) -> str:
        txt = '<span style="background-color:rgb' + str(self.color) + '">' + self.main_text + '</span>'
        if self.comments != '':
            txt = '<div title="' + self.comments + '">' + txt + '</div>'
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
                contents = annotation.contents()
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
                    if contents:
                        ret.append(TextAnno(txt, color=color, comments=contents))
                    else:
                        ret.append(TextAnno(txt, color=color))
                elif isinstance(annotation, popplerqt5.Poppler.TextAnnotation):
                    if contents:
                        ret.append(TextAnno(contents))
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
        file_link = f'<a href="{self.pdf_path}">{self.pdf_path.name}</a>'
        main = '<br>\n'.join('- ' + a.to_markdown() for a in self.annotations)
        ret = f"""\
<details>
<summary>{title}</summary>
<p>
{file_link}<br>
{main}
</p>
</details>
        """
        return ret


_arxiv_pattern = re.compile(r"\d*\.\d*\.pdf")


def guess_pdf_title_batched(pdf_path_list: List[str]) -> List[str]:
    arxiv_id_list = []
    arxiv_list = []
    other_list = []
    for idx, pdf_path in enumerate(pdf_path_list):
        pdf_path = Path(pdf_path)
        if _arxiv_pattern.match(pdf_path.name):
            arxiv_id_list.append((idx, pdf_path.name[:-4]))  # strip ".pdf"
        else:
            try:
                title = get_title_from_file(pdf_path)
            except PDFUnicodeNotDefined as e:
                logger.error(f"Error in {guess_pdf_title_batched.__name__}: {e}")
                # TODO: can we fix this?
                title = ''
            other_list.append((idx, title))
    if len(arxiv_id_list) > 0:
        out = arxiv.query(id_list=[_[1] for _ in arxiv_id_list])
        titles = [_['title'].strip().replace('\n', '') for _ in out]
        arxiv_list = [(arxiv_id_list[i][0], titles[i]) for i in range(len(arxiv_id_list))]

    ret = [''] * len(pdf_path_list)
    for idx, title in other_list:
        ret[idx] = title
    for idx, title in arxiv_list:
        ret[idx] = title
    return ret


# Adding open all and close all buttons.
_extra_html = """
<style>
  details > summary {
    padding: 4px;
    background-color: #eeeeee;
    border: none;
    box-shadow: 1px 1px 2px #bbbbbb;
    cursor: pointer;
  }
  
  details > p {
    background-color: #eeeeee;
    padding: 4px;
    margin: 0;
    box-shadow: 1px 1px 2px #bbbbbb;
  }
</style>
<script>
  function openAll() {
    var x = document.getElementsByTagName("details");
    var i;
    for (i = 0; i < x.length; i++) {
      x[i].open = true

    }
  }
  function closeAll() {
    var x = document.getElementsByTagName("details");
    var i;
    for (i = 0; i < x.length; i++) {
      x[i].open = false
    }
  }
</script>
<button onclick="openAll()">Expand All</button>
<button onclick="closeAll()">Close All</button>
"""


def scan_dir(directory):
    pdf_list = []
    for path, directories, files in os.walk(directory, topdown=True):
        for file in files:
            if file.endswith('.pdf'):
                file = os.path.join(path, file)
                pdf_list.append(file)
    titles = guess_pdf_title_batched(pdf_list)
    ret = []
    for idx, file in enumerate(pdf_list):
        annotation = read_annotations(file)
        ret.append(Document(file, annotations=annotation, title=titles[idx]))

    ret = '\n'.join(doc.to_markdown() for doc in ret)
    ret = _extra_html + ret
    return ret


if __name__ == "__main__":
    # test = '1704.05018.pdf'
    # anno = read_annotations(test)
    # doc = Document(test, annotations=anno, title=guess_pdf_title(test))
    # print(doc.to_markdown())
    # print(scan_dir('.'))
    target = '/workdir'
    os.chdir(target)
    target_md = scan_dir('.')
    print(target_md)
