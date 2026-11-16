"""Untrusted evidence validation: subprocess only, no diagnostics or metadata output."""

import io
import resource
import sys


def main():
    limit = int(sys.argv[1])
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    resource.setrlimit(resource.RLIMIT_CPU, (20, 21))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4096, 4096))
    data = sys.stdin.buffer.read(5 * 1024 * 1024 + 1)
    if not 0 < len(data) <= 5 * 1024 * 1024:
        return
    if data.startswith(b"%PDF-"):
        import pdfplumber

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            if not pdf.pages:
                return
            for page in pdf.pages:
                _ = page.width, page.height
        print("application/pdf")
        return
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = 20_000_000
    with Image.open(io.BytesIO(data)) as image:
        if (
            image.format not in ("JPEG", "PNG")
            or image.width * image.height > 20_000_000
            or getattr(image, "n_frames", 1) != 1
        ):
            return
        mime = "image/jpeg" if image.format == "JPEG" else "image/png"
        image.verify()
    with Image.open(io.BytesIO(data)) as image:
        image.load()
    print(mime)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
