import ctypes
import ctypes.wintypes


CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


def get_clipboard() -> str | None:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    if not user32.OpenClipboard(None):
        return None
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return None
        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def set_clipboard(text: str) -> bool:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    encoded = (text + "\x00").encode("utf-16-le")
    size = len(encoded)

    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
    if not h_mem:
        return False

    ptr = kernel32.GlobalLock(h_mem)
    ctypes.memmove(ptr, encoded, size)
    kernel32.GlobalUnlock(h_mem)

    if not user32.OpenClipboard(None):
        kernel32.GlobalFree(h_mem)
        return False
    try:
        user32.EmptyClipboard()
        user32.SetClipboardData(CF_UNICODETEXT, h_mem)
        return True
    finally:
        user32.CloseClipboard()
