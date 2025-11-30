import pytest

from getgather.selector import CSS, HasText, XPath


def test_xpath_can_handle():
    """Test XPath selector detection."""
    xpath = XPath()
    assert xpath.can_handle("//div[@id='foo']") is True
    assert xpath.can_handle("div.class") is False


def test_css_can_handle():
    """Test CSS selector handles everything."""
    css = CSS()
    assert css.can_handle("div.class") is True
    assert css.can_handle("//xpath") is True
    assert css.can_handle("anything") is True


def test_hastext_can_handle():
    """Test :has-text() selector detection."""
    hastext = HasText()
    assert hastext.can_handle('h5:has-text("Cart")') is True
    assert hastext.can_handle("button:has-text('Continue')") is True
    assert hastext.can_handle("div.class") is False


def test_hastext_parse_selector():
    """Test :has-text() selector parsing."""
    hastext = HasText()

    # Single :has-text()
    base, filters = hastext._parse_selector('h5:has-text("Cart")')
    assert base == "h5"
    assert filters == ["Cart"]

    # Multiple :has-text()
    base, filters = hastext._parse_selector('div:has-text("foo"):has-text("bar")')
    assert base == "div"
    assert filters == ["foo", "bar"]

    # With CSS class
    base, filters = hastext._parse_selector('button.primary:has-text("Submit")')
    assert base == "button.primary"
    assert filters == ["Submit"]


def test_hastext_parse_selector_invalid():
    """Test :has-text() parsing with invalid selectors."""
    hastext = HasText()

    # No base selector
    with pytest.raises(ValueError, match="must have a base element"):
        hastext._parse_selector(':has-text("text")')

    # Malformed
    with pytest.raises(ValueError, match="Malformed"):
        hastext._parse_selector("div:has-text(no-quotes)")
