from fpdf import FPDF


class PDF(FPDF):
    WIDTH = 210
    HEIGHT = 297

    def border(self, offset: int = 10):
        self.rect(offset, offset, self.WIDTH - offset * 2, self.HEIGHT - offset * 2)

    def add_image(self, img: str, x: int, y: int):
        self.set_xy(x, y)
        self.image(name=img, w=32, h=12)


if __name__ == '__main__':
    pdf = PDF(orientation="P", format="A4", unit="mm")
    pdf.add_page()
    pdf.add_image("logo.png", pdf.WIDTH - 32 - 2, 2)
    pdf.output('test.pdf', "F")
