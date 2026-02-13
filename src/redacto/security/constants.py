
# Basic HTML allowed tags (for rich content)
BASIC_HTML_ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "s",
    "sup",
    "sub",
    "code",
    "blockquote",
    "pre",
    "h1",
    "h2",
    "ul",
    "ol",
    "li",
    "hr",
    "a",
    "img",
    "video",
    "iframe",
    "div",
    "span",
]

BASIC_HTML_ALLOWED_ATTRIBUTES = {
    "a": ["href", "target", "rel"],
    "img": ["src", "alt"],
    "iframe": ["src", "width", "height", "frameborder", "allow", "allowfullscreen"],
    "*": ["class", "style"],
}

# Simple HTML tags (for basic formatting)
HTML_STRING_INPUT_ALLOWED_TAGS = ["b", "i", "u", "strong", "em", "p"]

# Quill editor allowed tags (for rich text editor content)
QUILL_STRING_INPUT_ALLOWED_TAGS = [
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "del",
    "sup",
    "sub",
    "code",
    "a",
    "span",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "pre",
    "ul",
    "ol",
    "li",
    "img",
    "br",
    "div",
    "table",
    "thead",
    "tbody",
    "tr",
    "td",
    "th",
]

QUILL_STRING_INPUT_ALLOWED_ATTRIBUTES = {
    "*": ["class", "style"],
    "a": ["href", "target", "rel"],
    "img": ["src", "alt", "width", "height"],
    "li": ["data-list"],
    "pre": ["spellcheck"],
}

QUILL_STRING_INPUT_ALLOWED_CSS_PROPERTIES = ["color", "background-color"]

