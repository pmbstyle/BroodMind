from __future__ import annotations

import asyncio

import broodmind.tools.browser.actions as browser_actions


class _LocatorStub:
    def __init__(self, text: str = "", should_fail: bool = False) -> None:
        self._text = text
        self._should_fail = should_fail
        self.wait_calls: list[tuple[str, int]] = []

    def nth(self, _index: int):
        return self

    @property
    def first(self):
        return self

    async def wait_for(self, *, state: str, timeout: int) -> None:
        self.wait_calls.append((state, timeout))
        if self._should_fail:
            raise RuntimeError("missing")

    async def inner_text(self, timeout: int = 5000) -> str:
        if self._should_fail:
            raise RuntimeError("cannot extract")
        return self._text


class _PageStub:
    def __init__(self) -> None:
        self.url = "https://example.com/page"
        self.refs = {
            ("button", "Save", True): _LocatorStub(text="Save"),
        }
        self.text_locator = _LocatorStub()
        self.body_locator = _LocatorStub(text="Page body content")

    def get_by_role(self, role: str, name: str | None = None, exact: bool = False):
        return self.refs[(role, name, exact)]

    def get_by_text(self, text: str, exact: bool = False):
        assert text == "Done"
        assert exact is False
        return self.text_locator

    def locator(self, selector: str):
        assert selector == "body"
        return self.body_locator

    async def title(self) -> str:
        return "Example title"


class _ManagerStub:
    def __init__(self, page: _PageStub) -> None:
        self._page = page

    async def get_page(self, chat_id: int):
        assert chat_id == 7
        return self._page


def test_browser_wait_for_uses_text_lookup(monkeypatch) -> None:
    page = _PageStub()
    monkeypatch.setattr(browser_actions, "get_browser_manager", lambda: _ManagerStub(page))

    async def scenario() -> None:
        result = await browser_actions.browser_wait_for(
            {"text": "Done", "state": "visible", "timeout_ms": 1234},
            {"chat_id": 7},
        )
        assert result == "Text appeared: Done"
        assert page.text_locator.wait_calls == [("visible", 1234)]

    asyncio.run(scenario())


def test_browser_extract_returns_page_summary(monkeypatch) -> None:
    page = _PageStub()
    monkeypatch.setattr(browser_actions, "get_browser_manager", lambda: _ManagerStub(page))

    async def scenario() -> None:
        result = await browser_actions.browser_extract({"max_chars": 500}, {"chat_id": 7})
        assert result["ok"] is True
        assert result["source"] == "page"
        assert result["title"] == "Example title"
        assert result["text"] == "Page body content"

    asyncio.run(scenario())


def test_browser_extract_can_use_snapshot_ref(monkeypatch) -> None:
    page = _PageStub()
    monkeypatch.setattr(browser_actions, "get_browser_manager", lambda: _ManagerStub(page))
    monkeypatch.setattr(
        browser_actions,
        "_SESSION_REFS",
        {7: {"e1": {"role": "button", "name": "Save", "nth": 0}}},
    )

    async def scenario() -> None:
        result = await browser_actions.browser_extract({"ref": "e1"}, {"chat_id": 7})
        assert result == {"ok": True, "source": "ref", "ref": "e1", "text": "Save"}

    asyncio.run(scenario())
