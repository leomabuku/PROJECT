from __future__ import annotations

from dataclasses import dataclass, field
import queue
from typing import Callable


@dataclass
class RuntimeInputProvider:
    """
    Callable used as builtins.input during GUI execution.

    It notifies the GUI that input is needed, then waits until the GUI submits
    a value. The interpreter still receives a normal string from input().
    """

    on_prompt: Callable[[str], None]
    wait_for_value: Callable[[], str]
    history: list[tuple[str, str]] = field(default_factory=list)

    def __call__(self, prompt: str = "") -> str:
        visible_prompt = prompt or "bala() input requested"
        self.on_prompt(visible_prompt)
        value = self.wait_for_value()
        self.history.append((visible_prompt, value))
        return value


class QueueTextWriter:
    """
    File-like stdout writer that forwards output text to a callback.
    """

    def __init__(self, on_text: Callable[[str], None]):
        self.on_text = on_text

    def write(self, text: str) -> int:
        if text:
            self.on_text(text)
        return len(text)

    def flush(self) -> None:
        return None


class BlockingInputQueue:
    """
    Thread-safe handoff between the Tkinter UI thread and the execution thread.
    """

    def __init__(self):
        self._queue: queue.Queue[str] = queue.Queue()

    def submit(self, value: str) -> None:
        self._queue.put(value)

    def wait(self) -> str:
        return self._queue.get()
