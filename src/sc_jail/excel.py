"""Preserve the displayed meaning of opaque spreadsheet identifiers."""

import math
import re

import xlrd

from .http import SourceError


def identifier(book, cell):
    if cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
        return ""
    if cell.ctype == xlrd.XL_CELL_TEXT:
        return str(cell.value).strip()
    if cell.ctype != xlrd.XL_CELL_NUMBER or not math.isfinite(cell.value):
        raise SourceError("Spreadsheet identifier has an unsupported cell type")
    if cell.value < 0 or cell.value != int(cell.value):
        raise SourceError("Spreadsheet identifier is not a nonnegative integer")
    result = str(int(cell.value))
    fmt = book.format_map[book.xf_list[cell.xf_index].format_key].format_str
    if re.fullmatch(r"0+", fmt):
        result = result.zfill(len(fmt))
    return result
