#!/usr/bin/python3
import os
import sys

import click

# %% setup python path
try:
    from paperutils.core import read_annotations, Document, guess_pdf_title_batched, scan_dir2
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from paperutils.core import read_annotations, Document, guess_pdf_title_batched, scan_dir2


@click.command()
@click.argument('directory')
@click.option('--check_arxiv/--no_check_arxiv', default=False)
def main(directory, check_arxiv):
    print(scan_dir2(directory, check_arxiv=check_arxiv))


if __name__ == "__main__":
    # print(scan_dir2(os.path.dirname(__file__)))
    main()
