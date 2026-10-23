"""Первая цена, названная менеджером (этап 4, шаг 3). Без LLM — правила."""

from __future__ import annotations

import re

from chat_turns import Turn, manager_turns

# Контекст «менеджер называет цену изделия», не часы работы / предоплата %.
_PRICE_CUE = re.compile(
    r"(?i)"
    r"(?:"
    r"цен[аыуе]\s+с\s+уч[её]том"
    r"|стоимост"
    r"|итоговая"
    r"|специальн\w*\s+цен"
    r"|цен[аыуе]\s*:"
    r")"
)

# Сумма цифрами с денежным маркером либо прописью (тысяч/миллион).
_AMOUNT_DIGITS = re.compile(r"(?i)\d.*(?:руб|₽|тыс|млн)|(?:руб|₽|тыс|млн).*\d")
_AMOUNT_WORDS = re.compile(r"(?i)(?:тысяч|миллион)")


def is_manager_price_utterance(text: str) -> bool:
    """True, если реплика менеджера называет цену изделия.

    Учитываем:
    - цифры с пробелами/точками и «руб» / «₽» / «тыс» / «млн»;
    - пропись («сто пятьдесят восемь тысяч рублей»).
    Не считаем ценой: «2-3 платежа», «предоплата 30%», часы работы шоурума.
    """
    if _PRICE_CUE.search(text) is None:
        return False
    return (
        _AMOUNT_DIGITS.search(text) is not None
        or _AMOUNT_WORDS.search(text) is not None
    )


def first_manager_price_turn(turns: list[Turn]) -> Turn | None:
    """Первая по порядку реплика менеджера с ценой; иначе None."""
    for turn in manager_turns(turns):
        if is_manager_price_utterance(turn.text):
            return turn
    return None


def first_manager_price_index(turns: list[Turn]) -> int | None:
    """Индекс первой ценовой реплики менеджера в общем списке turns."""
    turn = first_manager_price_turn(turns)
    return None if turn is None else turn.index
