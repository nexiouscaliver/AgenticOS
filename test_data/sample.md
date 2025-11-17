# Multi-Format Parser Agent Test

## Overview

This is a **Markdown** file created to test the multi-format parser agent's markdown parsing capabilities.

## Features

The parser should handle:

- **Headers** (H1 through H6)
- *Italic text* and **bold text**
- Lists (ordered and unordered)
- Code blocks and inline `code`
- Links and references
- Tables

## Code Example

```python
def test_parser(file_path):
    """Test the multi-format parser"""
    parser = MultiFormatFileParser()
    result = parser.parse_file(file_path)
    return result
```

## Data Table

| Feature | Status | Priority |
|---------|--------|----------|
| PDF Parsing | ✅ Implemented | High |
| DOCX Parsing | ✅ Implemented | High |
| CSV Parsing | ✅ Implemented | Medium |
| XLSX Parsing | ✅ Implemented | Medium |

## Links

- [Agno Framework](https://agno.com)
- [Documentation](https://docs.agno.com)

## Conclusion

This markdown file tests various markdown features including:

1. Multiple heading levels
2. Text formatting (bold, italic)
3. Code blocks with syntax highlighting
4. Tables with alignment
5. Lists and nested content

> Blockquote: The multi-format parser should preserve markdown structure and formatting.

---

**End of Test Document**
