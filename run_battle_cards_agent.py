from pathlib import Path
from datetime import datetime, timezone


def escape_pdf_text(text: str) -> str:
    return text.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


def build_simple_pdf(lines: list[str], out_path: Path) -> None:
    y_start = 760
    y_step = 18
    content_lines = ["BT", "/F1 12 Tf"]

    y = y_start
    for line in lines:
        safe = escape_pdf_text(line)
        content_lines.append(f"72 {y} Td ({safe}) Tj")
        content_lines.append("0 0 Td")
        y -= y_step

    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
    )
    objects.append(
        f"4 0 obj << /Length {len(content)} >> stream\n".encode("ascii")
        + content
        + b"\nendstream endobj\n"
    )
    objects.append(b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")

    header = b"%PDF-1.4\n"
    pdf = bytearray(header)
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        (
            "trailer << /Size {size} /Root 1 0 R >>\n"
            "startxref\n{xref}\n%%EOF\n"
        ).format(size=len(offsets), xref=xref_pos).encode("ascii")
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(pdf)


if __name__ == "__main__":
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "Battle Cards Agent Run Result",
        "",
        f"Run timestamp: {now}",
        "Status: Agent files were not found in this repository.",
        "Action taken: Generated this PDF status report.",
        "",
        "If you expected a specific agent, add its code/config to this repo",
        "and rerun this script.",
    ]
    build_simple_pdf(lines, Path("output/battle_cards_result.pdf"))
    print("Generated: output/battle_cards_result.pdf")
