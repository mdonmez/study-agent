import base64
from pathlib import Path


class Book:
    def __init__(self, subject: str):
        self.subject = subject
        self.project_root = Path(__file__).parents[3]
        self.books_path = self.project_root / "data" / "books" / subject
        if not self.books_path.exists():
            raise ValueError(
                f"Subject '{subject}' not found. Available: {self.list_books()}"
            )

    @classmethod
    def list_books(cls) -> list[str]:
        books_path = Path(__file__).parents[3] / "data" / "books"
        return (
            sorted(d.name for d in books_path.iterdir() if d.is_dir())
            if books_path.exists()
            else []
        )

    def get_page_content(self, page_num: int) -> dict[str, str | list[str]]:
        page_path = self.books_path / str(page_num)
        if not page_path.exists():
            raise FileNotFoundError(f"Page {page_num} not found for {self.subject}")
        return {
            "text": self._read_text(page_path),
            "images": self._read_images(page_path),
        }

    def _read_text(self, page_path: Path) -> str:
        page_md = page_path / "page.md"
        if not page_md.exists():
            raise FileNotFoundError(f"Page markdown file not found: {page_md}")
        try:
            return page_md.read_text(encoding="utf-8")
        except Exception as e:
            raise IOError(f"Error reading {page_md}: {e}")

    def _read_images(self, page_path: Path) -> list[str]:
        images = sorted(
            [
                f
                for f in page_path.iterdir()
                if f.is_file() and f.suffix.lower() in {".webp"}
            ],
            key=lambda f: f.name,
        )
        encoded = []
        for img in images:
            try:
                encoded.append(base64.b64encode(img.read_bytes()).decode())
            except Exception as e:
                raise IOError(f"Error encoding {img}: {e}")
        return encoded

    def get_context(self, pages: list[int]) -> dict[int, list[str]]:
        result = {}
        for p in pages:
            content = self.get_page_content(p)
            text = content["text"]
            images = content["images"]
            # text is a str, images is a list[str]
            if isinstance(text, str) and isinstance(images, list):
                result[p] = [text] + images
        return result

    def list_pages(self) -> list[int]:
        return (
            sorted(
                int(d.name)
                for d in self.books_path.iterdir()
                if d.is_dir() and d.name.isdigit()
            )
            if self.books_path.exists()
            else []
        )

    def get_page_count(self) -> int:
        return len(self.list_pages())

    def page_exists(self, page_num: int) -> bool:
        return (self.books_path / str(page_num)).exists()


if __name__ == "__main__":
    try:
        book = Book("matematik")
        pages = book.list_pages()
        print("Pages:", pages[:10], f"Total: {book.get_page_count()}")
        if pages:
            content = book.get_page_content(pages[0])
            print(
                f"Page {pages[0]} text len: {len(content['text'])}, images: {len(content['images'])}"
            )
        print("Subjects:", Book.list_books())
    except Exception as e:
        print("Error:", e)
