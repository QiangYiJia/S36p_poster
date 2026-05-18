#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image


URL = "https://qiangyijia.github.io/S36p_poster/"
OUT_DIR = Path(__file__).resolve().parent / "qr"
PNG_PATH = OUT_DIR / "S36p_poster_QR.png"
SVG_PATH = OUT_DIR / "S36p_poster_QR.svg"

VERSION = 3
SIZE = 17 + 4 * VERSION
DATA_CODEWORDS = 55
EC_CODEWORDS = 15
EC_LEVEL_BITS = 0b01


def gf_tables() -> tuple[list[int], list[int]]:
    exp = [0] * 512
    log = [0] * 256
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        exp[i] = exp[i - 255]
    return exp, log


GF_EXP, GF_LOG = gf_tables()


def gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return GF_EXP[GF_LOG[a] + GF_LOG[b]]


def poly_mul(a: list[int], b: list[int]) -> list[int]:
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        for j, bv in enumerate(b):
            out[i + j] ^= gf_mul(av, bv)
    return out


def rs_generator(degree: int) -> list[int]:
    poly = [1]
    for i in range(degree):
        poly = poly_mul(poly, [1, GF_EXP[i]])
    return poly


def rs_encode(data: list[int], degree: int) -> list[int]:
    gen = rs_generator(degree)
    msg = data + [0] * degree
    for i, coef in enumerate(data):
        if coef == 0:
            continue
        for j, gv in enumerate(gen):
            msg[i + j] ^= gf_mul(coef, gv)
    return msg[-degree:]


def append_bits(bits: list[int], value: int, count: int) -> None:
    for i in range(count - 1, -1, -1):
        bits.append((value >> i) & 1)


def data_codewords(text: str) -> list[int]:
    payload = text.encode("utf-8")
    bits: list[int] = []
    append_bits(bits, 0b0100, 4)
    append_bits(bits, len(payload), 8)
    for byte in payload:
        append_bits(bits, byte, 8)

    capacity = DATA_CODEWORDS * 8
    terminator = min(4, capacity - len(bits))
    append_bits(bits, 0, terminator)
    while len(bits) % 8:
        bits.append(0)

    codewords: list[int] = []
    for i in range(0, len(bits), 8):
        value = 0
        for bit in bits[i : i + 8]:
            value = (value << 1) | bit
        codewords.append(value)

    pads = [0xEC, 0x11]
    p = 0
    while len(codewords) < DATA_CODEWORDS:
        codewords.append(pads[p % 2])
        p += 1
    return codewords


def new_matrix() -> tuple[list[list[int | None]], list[list[bool]]]:
    matrix: list[list[int | None]] = [[None for _ in range(SIZE)] for _ in range(SIZE)]
    reserved = [[False for _ in range(SIZE)] for _ in range(SIZE)]
    return matrix, reserved


def set_module(
    matrix: list[list[int | None]],
    reserved: list[list[bool]],
    row: int,
    col: int,
    value: int,
    reserve: bool = True,
) -> None:
    if 0 <= row < SIZE and 0 <= col < SIZE:
        matrix[row][col] = value
        if reserve:
            reserved[row][col] = True


def add_finder(matrix: list[list[int | None]], reserved: list[list[bool]], row: int, col: int) -> None:
    for r in range(row - 1, row + 8):
        for c in range(col - 1, col + 8):
            if not (0 <= r < SIZE and 0 <= c < SIZE):
                continue
            if row <= r < row + 7 and col <= c < col + 7:
                rr = r - row
                cc = c - col
                value = int(
                    rr in (0, 6)
                    or cc in (0, 6)
                    or (2 <= rr <= 4 and 2 <= cc <= 4)
                )
            else:
                value = 0
            set_module(matrix, reserved, r, c, value)


def add_alignment(matrix: list[list[int | None]], reserved: list[list[bool]], row: int, col: int) -> None:
    for r in range(row - 2, row + 3):
        for c in range(col - 2, col + 3):
            rr = abs(r - row)
            cc = abs(c - col)
            value = int(max(rr, cc) in (0, 2))
            set_module(matrix, reserved, r, c, value)


def add_function_patterns(matrix: list[list[int | None]], reserved: list[list[bool]]) -> None:
    add_finder(matrix, reserved, 0, 0)
    add_finder(matrix, reserved, 0, SIZE - 7)
    add_finder(matrix, reserved, SIZE - 7, 0)
    add_alignment(matrix, reserved, 22, 22)

    for i in range(8, SIZE - 8):
        value = int(i % 2 == 0)
        set_module(matrix, reserved, 6, i, value)
        set_module(matrix, reserved, i, 6, value)

    set_module(matrix, reserved, 4 * VERSION + 9, 8, 1)

    for i in range(9):
        if i != 6:
            reserved[8][i] = True
            reserved[i][8] = True
    for i in range(8):
        reserved[8][SIZE - 1 - i] = True
        reserved[SIZE - 1 - i][8] = True


def mask_bit(mask: int, row: int, col: int) -> int:
    if mask == 0:
        return int((row + col) % 2 == 0)
    if mask == 1:
        return int(row % 2 == 0)
    if mask == 2:
        return int(col % 3 == 0)
    if mask == 3:
        return int((row + col) % 3 == 0)
    if mask == 4:
        return int((row // 2 + col // 3) % 2 == 0)
    if mask == 5:
        return int(((row * col) % 2 + (row * col) % 3) == 0)
    if mask == 6:
        return int((((row * col) % 2 + (row * col) % 3) % 2) == 0)
    return int((((row + col) % 2 + (row * col) % 3) % 2) == 0)


def add_data(
    matrix: list[list[int | None]],
    reserved: list[list[bool]],
    all_codewords: list[int],
    mask: int,
) -> None:
    bits: list[int] = []
    for codeword in all_codewords:
        append_bits(bits, codeword, 8)

    bit_index = 0
    upward = True
    col = SIZE - 1
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(SIZE - 1, -1, -1) if upward else range(SIZE)
        for row in rows:
            for c in (col, col - 1):
                if reserved[row][c]:
                    continue
                bit = bits[bit_index] if bit_index < len(bits) else 0
                matrix[row][c] = bit ^ mask_bit(mask, row, c)
                bit_index += 1
        upward = not upward
        col -= 2


def format_bits(mask: int) -> int:
    data = (EC_LEVEL_BITS << 3) | mask
    value = data << 10
    generator = 0x537
    for i in range(14, 9, -1):
        if (value >> i) & 1:
            value ^= generator << (i - 10)
    return ((data << 10) | value) ^ 0x5412


def add_format(matrix: list[list[int | None]], mask: int) -> None:
    bits = format_bits(mask)
    positions_1 = [
        (8, 0),
        (8, 1),
        (8, 2),
        (8, 3),
        (8, 4),
        (8, 5),
        (8, 7),
        (8, 8),
        (7, 8),
        (5, 8),
        (4, 8),
        (3, 8),
        (2, 8),
        (1, 8),
        (0, 8),
    ]
    positions_2 = [(SIZE - 1 - i, 8) for i in range(8)] + [(8, SIZE - 7 + i) for i in range(7)]
    for i, (row, col) in enumerate(positions_1):
        matrix[row][col] = (bits >> i) & 1
    for i, (row, col) in enumerate(positions_2):
        matrix[row][col] = (bits >> i) & 1


def penalty(matrix: list[list[int | None]]) -> int:
    m = [[int(v or 0) for v in row] for row in matrix]
    score = 0

    for row in range(SIZE):
        run_color = m[row][0]
        run_len = 1
        for col in range(1, SIZE):
            if m[row][col] == run_color:
                run_len += 1
            else:
                if run_len >= 5:
                    score += 3 + run_len - 5
                run_color = m[row][col]
                run_len = 1
        if run_len >= 5:
            score += 3 + run_len - 5

    for col in range(SIZE):
        run_color = m[0][col]
        run_len = 1
        for row in range(1, SIZE):
            if m[row][col] == run_color:
                run_len += 1
            else:
                if run_len >= 5:
                    score += 3 + run_len - 5
                run_color = m[row][col]
                run_len = 1
        if run_len >= 5:
            score += 3 + run_len - 5

    for row in range(SIZE - 1):
        for col in range(SIZE - 1):
            block = m[row][col] + m[row + 1][col] + m[row][col + 1] + m[row + 1][col + 1]
            if block in (0, 4):
                score += 3

    patterns = ([1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1])
    for row in range(SIZE):
        line = m[row]
        for i in range(SIZE - 10):
            if line[i : i + 11] in patterns:
                score += 40
    for col in range(SIZE):
        line = [m[row][col] for row in range(SIZE)]
        for i in range(SIZE - 10):
            if line[i : i + 11] in patterns:
                score += 40

    dark = sum(sum(row) for row in m)
    percent = dark * 100 / (SIZE * SIZE)
    score += int(abs(percent - 50) // 5) * 10
    return score


def make_matrix(text: str) -> list[list[int]]:
    data = data_codewords(text)
    ec = rs_encode(data, EC_CODEWORDS)
    all_codewords = data + ec

    best: list[list[int | None]] | None = None
    best_score: int | None = None
    for mask in range(8):
        matrix, reserved = new_matrix()
        add_function_patterns(matrix, reserved)
        add_data(matrix, reserved, all_codewords, mask)
        add_format(matrix, mask)
        score = penalty(matrix)
        if best_score is None or score < best_score:
            best = matrix
            best_score = score

    assert best is not None
    return [[int(v or 0) for v in row] for row in best]


def save_png(matrix: list[list[int]], path: Path, scale: int = 20, border: int = 4) -> None:
    modules = SIZE + border * 2
    image = Image.new("RGB", (modules * scale, modules * scale), "white")
    pixels = image.load()
    for row in range(SIZE):
        for col in range(SIZE):
            if matrix[row][col]:
                y0 = (row + border) * scale
                x0 = (col + border) * scale
                for y in range(y0, y0 + scale):
                    for x in range(x0, x0 + scale):
                        pixels[x, y] = (0, 0, 0)
    image.save(path)


def save_svg(matrix: list[list[int]], path: Path, border: int = 4) -> None:
    modules = SIZE + border * 2
    rects = []
    for row in range(SIZE):
        for col in range(SIZE):
            if matrix[row][col]:
                rects.append(f'<rect x="{col + border}" y="{row + border}" width="1" height="1"/>')
    content = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {modules} {modules}" shape-rendering="crispEdges">',
            '<rect width="100%" height="100%" fill="#fff"/>',
            '<g fill="#000">',
            *rects,
            "</g>",
            "</svg>",
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    matrix = make_matrix(URL)
    save_png(matrix, PNG_PATH)
    save_svg(matrix, SVG_PATH)
    print(URL)
    print(PNG_PATH)
    print(SVG_PATH)


if __name__ == "__main__":
    main()
