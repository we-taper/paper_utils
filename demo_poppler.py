import PyQt5
import popplerqt5

resolution = 150


def main():
    doc = popplerqt5.Poppler.Document.load('1704.05018.pdf')
    total_annotations = 0

    for i in range(doc.numPages()):
        print("========= PAGE {} =========".format(i + 1))
        page = doc.page(i)
        annotations = page.annotations()
        (pwidth, pheight) = (page.pageSize().width(), page.pageSize().height())
        count = 0

        if len(annotations) > 0:

            for annotation in annotations:

                if isinstance(annotation, popplerqt5.Poppler.Annotation):
                    total_annotations += 1

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

                        # print("========= ANNOTATION =========")
                        print(txt)
                        # Get color. Note that getRgb returns a tuple of (R,G,B,Alpha)
                        print(f"[{annotation.style().color().getRgb()[:3]}]")
                        if annotation.contents():
                            print("\t - {}".format(annotation.contents()))

                    if isinstance(annotation, popplerqt5.Poppler.GeomAnnotation):
                        count += 1
                        bounds = annotation.boundary()

                        # default we have height/width as per 72p rendering so converting to different resolution
                        (width, height) = (pwidth * resolution / 72, pheight * resolution / 72)

                        # noinspection PyUnresolvedReferences
                        bdy = PyQt5.QtCore.QRectF(
                            bounds.left() * width,
                            bounds.top() * height,
                            bounds.width() * width,
                            bounds.height() * height
                        )

                        page.renderToImage(resolution, resolution, bdy.left(), bdy.top(), bdy.width(),
                                           bdy.height()).save("page{}_image{}.png".format(i, count))
                        print("page{}_image{}.png".format(i, count))
                        if annotation.contents():
                            print(annotation.contents())

                    if isinstance(annotation, popplerqt5.Poppler.TextAnnotation):
                        if annotation.contents():
                            print(annotation.contents())

    if total_annotations > 0:
        pass
    else:
        print("no annotations found")


if __name__ == "__main__":
    main()
