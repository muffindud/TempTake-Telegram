from collections.abc import Sequence

from telegram import InlineKeyboardMarkup, InlineKeyboardButton


class KeyboardBuilder:
    def __init__(self):
        self.keyboard = []

    def add_row(self) -> 'KeyboardBuilder':
        self.keyboard.append([])
        return self

    def add_row_button(self, text: str, callback_data: str) -> 'KeyboardBuilder':
        if not self.keyboard:
            self.add_row()

        self.keyboard[-1].append(
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data
            )
        )

        return self

    def build(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(self.keyboard)
