
from lasapp import SyntaxNode

def get_file_content(file_name):
    with open(file_name, encoding="utf-8") as f:
        file_content = f.read()
        return file_content

def get_utf8_substr(s, start, end):
    return s[start:end].decode('utf-8')

def print_source_highlighted(file_content, highlights):
    highlights = list(set(highlights))
    highlights.sort(key=lambda x: x[0])
    print(highlights)
    unique_highlights = []
    for highlight in highlights:
        # if highlight is not contained in other highlight
        if not any(other[0] <= highlight[0] and highlight[1] <= other[1] for other in unique_highlights):
            unique_highlights.append(highlight)
    highlights = unique_highlights
    for i in range(len(highlights)-1):
        assert highlights[i][1] < highlights[i+1][0]

    current = 0
    file_content_utf8 = file_content.encode('utf-8')
    for (fb, lb, c) in highlights:
        print(get_utf8_substr(file_content_utf8, current, fb), end="")
        print(f"\033[{c}" + get_utf8_substr(file_content_utf8, fb, lb) + "\033[0m", end="")
        current = lb
    print(get_utf8_substr(file_content_utf8, current, len(file_content_utf8)), end="\n")

def highlight_in_node(node: SyntaxNode, fb, lb, c):
    text = node.source_text.encode('utf-8')
    fb = fb - node.first_byte
    lb = lb - node.first_byte
    return get_utf8_substr(text, 0, fb) + f"\033[{c}" + get_utf8_substr(text, fb, lb) + "\033[0m" + get_utf8_substr(text, lb, len(text))

def is_descendant(parent: SyntaxNode, child: SyntaxNode):
    return parent.first_byte <= child.first_byte and child.last_byte <= parent.last_byte