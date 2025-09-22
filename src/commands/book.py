import asyncio
import base64
import httpx
import os
from dotenv import load_dotenv

from src.utils import text_formatter

load_dotenv()


class Book:
    def __init__(self, subject: str):
        self.subject = subject
        self.BASE_URL = "https://raw.githubusercontent.com/mdonmez/study-agent/refs/heads/master/data/books"
        self.API_BASE_URL = (
            "https://api.github.com/repos/mdonmez/study-agent/contents/data/books"
        )

        self.HEADERS = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "study-agent/1.0",
            **(
                {"Authorization": f"token {token}"}
                if (token := os.getenv("GITHUB_API_KEY"))
                else {}
            ),
        }

    @classmethod
    async def list_books(cls) -> list[str]:
        instance = cls("list_books")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                instance.API_BASE_URL, headers=instance.HEADERS, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return sorted(item["name"] for item in data if item["type"] == "dir")

    async def list_pages(self) -> list[int]:
        url = f"{self.API_BASE_URL}/{self.subject}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            return sorted(
                int(item["name"])
                for item in data
                if item["type"] == "dir" and item["name"].isdigit()
            )

    async def get_page_content(self, page_num: int) -> dict[str, str | list[str]]:
        async with httpx.AsyncClient() as client:
            text_url = f"{self.BASE_URL}/{self.subject}/{page_num}/page.md"
            text_response = await client.get(text_url, timeout=10)
            text_response.raise_for_status()

            api_url = f"{self.API_BASE_URL}/{self.subject}/{page_num}"
            response = await client.get(api_url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()

            images = [
                item
                for item in response.json()
                if item["type"] == "file" and item["name"].endswith(".webp")
            ]

            image_data = []
            for file_info in sorted(images, key=lambda x: x["name"]):
                img_url = (
                    f"{self.BASE_URL}/{self.subject}/{page_num}/{file_info['name']}"
                )
                try:
                    img_response = await client.get(img_url, timeout=10)
                    img_response.raise_for_status()
                    image_data.append(base64.b64encode(img_response.content).decode())
                except Exception as e:
                    print(f"Warning: Failed to fetch {file_info['name']}: {e}")

            return {
                "text": text_formatter.format_text(text_response.text),
                "images": image_data,
            }


if __name__ == "__main__":

    async def main():
        print("Subjects:", await Book.list_books())
        book = Book("fizik")
        pages = await book.list_pages()
        print(f"Total pages: {len(pages)}")

        page = pages[47]

        content = await book.get_page_content(page)
        print(
            f"Page {page} text length: {len(content['text'])}, images: {len(content['images'])}"
        )

        for img_data in content["images"]:
            print(f"Image data: {img_data[:30]}...")
        print(content["text"])

    asyncio.run(main())
