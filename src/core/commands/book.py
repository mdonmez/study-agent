import base64
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Book:
    def __init__(self, subject: str):
        self.subject = subject
        self.base_url = "https://raw.githubusercontent.com/mdonmez/study-agent/refs/heads/master/data/books"
        self.api_base_url = (
            "https://api.github.com/repos/mdonmez/study-agent/contents/data/books"
        )
        self.github_token = os.getenv("GITHUB_API_KEY")

    def _get_api_headers(self) -> dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "study-agent/1.0",
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    @classmethod
    def list_books(cls) -> list[str]:
        """Fetch available book subjects from GitHub API."""
        api_url = "https://api.github.com/repos/mdonmez/study-agent/contents/data/books"

        # Create a temporary instance to get headers
        temp_instance = cls.__new__(cls)
        temp_instance.github_token = os.getenv("GITHUB_API_KEY")
        headers = temp_instance._get_api_headers()

        response = httpx.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extract directory names (subjects)
        subjects = [item["name"] for item in data if item["type"] == "dir"]
        return sorted(subjects)

    def get_page_content(self, page_num: int) -> dict[str, str | list[str]]:
        """Fetch page content from GitHub repository."""
        try:
            text_content = self._fetch_page_text(page_num)
            image_contents = self._fetch_page_images(page_num)
            return {
                "text": text_content,
                "images": image_contents,
            }
        except Exception as e:
            raise FileNotFoundError(
                f"Page {page_num} not found for {self.subject}: {e}"
            )

    def _fetch_page_text(self, page_num: int) -> str:
        """Fetch page.md content from GitHub."""
        url = f"{self.base_url}/{self.subject}/{page_num}/page.md"
        try:
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise IOError(f"Error fetching page text from {url}: {e}")

    def _fetch_page_images(self, page_num: int) -> list[str]:
        """Fetch and encode .webp images from GitHub repository using GitHub API."""
        images = []

        # Use GitHub API to list files in the page directory
        api_url = f"{self.api_base_url}/{self.subject}/{page_num}"
        headers = self._get_api_headers()

        try:
            response = httpx.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Filter for .webp files
            webp_files = [
                item
                for item in data
                if item["type"] == "file" and item["name"].lower().endswith(".webp")
            ]

            # Sort by filename to ensure consistent ordering
            webp_files.sort(key=lambda x: x["name"])

            # Fetch each image and encode as base64
            for file_info in webp_files:
                try:
                    img_url = (
                        f"{self.base_url}/{self.subject}/{page_num}/{file_info['name']}"
                    )
                    img_response = httpx.get(img_url, timeout=10)
                    img_response.raise_for_status()
                    encoded_image = base64.b64encode(img_response.content).decode()
                    images.append(encoded_image)
                except Exception as e:
                    print(f"Warning: Error fetching image {file_info['name']}: {e}")
                    continue

        except Exception as e:
            # Fallback to the old guessing method if API fails
            print(f"Warning: GitHub API failed, falling back to filename guessing: {e}")
            return self._fetch_page_images_fallback(page_num)

        return images

    def _fetch_page_images_fallback(self, page_num: int) -> list[str]:
        """Fallback method to fetch images by guessing filenames."""
        images = []
        patterns = [lambda i: f"{i}.webp"]

        for pattern in patterns:
            for i in range(1, 6):  # Try up to 5 images per pattern
                url = f"{self.base_url}/{self.subject}/{page_num}/{pattern(i)}"
                try:
                    response = httpx.get(url, timeout=10)
                    response.raise_for_status()
                    encoded_image = base64.b64encode(response.content).decode()
                    images.append(encoded_image)
                except httpx.HTTPStatusError:
                    # Image doesn't exist, continue to next
                    continue
                except Exception as e:
                    # Log error but continue
                    print(f"Warning: Error fetching image {url}: {e}")
                    continue

        return images

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
        """Get list of available pages for the subject using GitHub API."""
        api_url = f"{self.api_base_url}/{self.subject}"
        headers = self._get_api_headers()

        try:
            response = httpx.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract directory names that are numeric (page numbers)
            pages = []
            for item in data:
                if item["type"] == "dir" and item["name"].isdigit():
                    pages.append(int(item["name"]))

            return sorted(pages)

        except Exception as e:
            print(
                f"Warning: GitHub API failed, falling back to existence checking: {e}"
            )
            # Fallback to the old method
            available_pages = []
            for page_num in range(1, 201):
                if self.page_exists(page_num):
                    available_pages.append(page_num)
                    if len(available_pages) >= 50:  # Limit to prevent too many requests
                        break
            return available_pages

    def get_page_count(self) -> int:
        """Get total number of pages available."""
        return len(self.list_pages())

    def page_exists(self, page_num: int) -> bool:
        """Check if a page exists by trying to fetch its page.md file."""
        url = f"{self.base_url}/{self.subject}/{page_num}/page.md"
        try:
            response = httpx.head(
                url, timeout=5
            )  # Use HEAD to avoid downloading content
            return response.status_code == 200
        except Exception:
            return False


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
