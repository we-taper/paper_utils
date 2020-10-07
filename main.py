#!/usr/bin/python3
import os
import sys

import click

# %% setup python path
try:
    from paperutils.core import read_annotations, Document, guess_pdf_title_batched
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from paperutils.core import read_annotations, Document, guess_pdf_title_batched

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


def scan_dir(directory, check_arxiv=False):
    pdf_list = []
    for path, directories, files in os.walk(directory, topdown=True):
        for file in files:
            if file.endswith('.pdf'):
                file = os.path.join(path, file)
                pdf_list.append(file)
    titles = guess_pdf_title_batched(pdf_list, check_arxiv=check_arxiv)
    ret = []
    for idx, file in enumerate(pdf_list):
        annotation = read_annotations(file)
        ret.append(Document(file, annotations=annotation, title=titles[idx]))

    ret = '\n'.join(doc.to_markdown() for doc in ret)
    ret = _extra_html + ret
    return ret


@click.command()
@click.argument('directory')
@click.option('--check_arxiv/--no_check_arxiv', default=False)
def main(directory, check_arxiv):
    print(scan_dir(directory, check_arxiv=check_arxiv))


if __name__ == "__main__":
    # print(scan_dir(os.path.dirname(__file__)))
    main()
