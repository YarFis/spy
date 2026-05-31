# -*- coding: utf-8 -*-
import pyautogui
import ctypes

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


class InputHandler:
    def handle(self, event: dict):
        kind = event.get("type")

        if kind == "mouse_move":
            pyautogui.moveTo(event["x"], event["y"])

        elif kind == "mouse_click":
            btn = event.get("button", "left")
            if event.get("double"):
                pyautogui.doubleClick(event["x"], event["y"], button=btn)
            else:
                pyautogui.click(event["x"], event["y"], button=btn)

        elif kind == "mouse_down":
            pyautogui.mouseDown(event["x"], event["y"], button=event.get("button", "left"))

        elif kind == "mouse_up":
            pyautogui.mouseUp(event["x"], event["y"], button=event.get("button", "left"))

        elif kind == "scroll":
            pyautogui.scroll(event.get("dy", 0), x=event["x"], y=event["y"])

        elif kind == "key_press":
            pyautogui.press(event["key"])

        elif kind == "key_down":
            pyautogui.keyDown(event["key"])

        elif kind == "key_up":
            pyautogui.keyUp(event["key"])

        elif kind == "type_text":
            pyautogui.typewrite(event["text"], interval=0.01)


class InputBlocker:
    """Блокирует физический ввод мыши и клавиатуры на удалённом ПК."""

    def block(self):
        # Работает только с правами администратора
        result = ctypes.windll.user32.BlockInput(True)
        return bool(result)

    def unblock(self):
        result = ctypes.windll.user32.BlockInput(False)
        return bool(result)
