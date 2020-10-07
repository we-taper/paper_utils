import os
import re
import sys
from pathlib import Path
from typing import Tuple, List

import PyQt5
import arxiv
import popplerqt5
from loguru import logger
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


HTML_ID = "Folder"
CSS_STYLE = """\
#{HTML_ID} {
    padding: 4px;
    background-color: #27d327;
    border: none;
    box-shadow: 1px 1px 2px #bbbbbb;
    cursor: pointer;
}
""".replace("HTML_ID", HTML_ID)

# Adding open all and close all buttons.
_extra_html = """
<style>
  #HTML_ID {
    padding: 8px;
    background-color: #e0e0e0;
    border: none;
    box-shadow: 1px 1px 2px #bbbbbb;
    cursor: pointer;
  }
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
""".replace("HTML_ID", HTML_ID)


def _scan_dir2(directory, check_arxiv=False) -> str:
    dir_contents = sorted(os.listdir(directory))
    pdf_list = []
    sub_dirs = []
    for c in dir_contents:
        c = os.path.join(directory, c)
        if os.path.isdir(c):
            sub_dirs.append(c)
        elif c.endswith('.pdf'):
            pdf_list.append(c)
        else:
            pass
    sub_dirs = '\n'.join(_scan_dir2(_) for _ in sub_dirs)
    file_titles = guess_pdf_title_batched(pdf_list, check_arxiv=check_arxiv)
    docs = []
    for idx, file in enumerate(pdf_list):
        annotation = read_annotations(file)
        docs.append(Document(file, annotations=annotation, title=file_titles[idx]))
    docs = '\n'.join(doc.to_markdown() for doc in docs)
    if docs == '' and sub_dirs == '':
        return ''
    folder_name = Path(directory).name
    text = f"""\
<details id="{HTML_ID}">
<summary>{folder_name}</summary>
<p>
{docs}
{sub_dirs}
</p>
</details>
"""
    return text


def scan_dir2(directory, check_arxiv=False) -> str:
    text = _scan_dir2(directory, check_arxiv=check_arxiv)
    return _extra_html + text


def _guess_title_1(pdf_path_list):
    ret = []
    for pdf_path in pdf_path_list:
        try:
            title = get_title_from_file(pdf_path)
            ret.append(title)
        except Exception as e:
            logger.error(f"Error guess title for {pdf_path}: {type(e)}({e})")
            ret.append('')
    return ret


_arxiv_pattern = re.compile(r"\d*\.\d*\.pdf")


def guess_pdf_title_batched(pdf_path_list: List[str], check_arxiv=False) -> List[str]:
    if not check_arxiv:
        return _guess_title_1(pdf_path_list)
    # else
    arxiv_id_list = []
    other_list_pdf_path = []
    other_list_idx = []
    for idx, pdf_path in enumerate(pdf_path_list):
        pdf_path = Path(pdf_path)
        if _arxiv_pattern.match(pdf_path.name):
            arxiv_id_list.append((idx, pdf_path.name[:-4]))  # strip ".pdf"
        else:
            other_list_pdf_path.append(pdf_path)
            other_list_idx.append(idx)
            # other_list.append((idx, pdf_path))
            # try:
            #     title = get_title_from_file(pdf_path)
            # except PDFUnicodeNotDefined as e:
            #     logger.error(f"Error in {guess_pdf_title_batched.__name__}: {e}")
            #     # TODO: can we fix this?
            #     title = ''
            # other_list.append((idx, title))
    other_list = zip(other_list_idx, _guess_title_1(other_list_pdf_path))
    ret = [''] * len(pdf_path_list)
    for idx, title in other_list:
        ret[idx] = title

    if len(arxiv_id_list) > 0:
        out = arxiv.query(id_list=[_[1] for _ in arxiv_id_list])
        titles = [_['title'].strip().replace('\n', '') for _ in out]
        arxiv_list = [(arxiv_id_list[i][0], titles[i]) for i in range(len(arxiv_id_list))]
        for idx, title in arxiv_list:
            ret[idx] = title
    return ret
