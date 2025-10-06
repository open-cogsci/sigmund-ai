import re
import logging
from .model import BaseModel
logger = logging.getLogger('sigmund')


def normalize_bullet_points(text: str) -> str:
    return re.sub(r"^(\s*)[•–♦○└─]\s+", r"\1- ", text, flags=re.MULTILINE)

def add_blank_line_after_colon_headers(text: str) -> str:
    """
    Insert a blank line after lines ending with a colon when they are immediately
    followed by a list, to improve Markdown compatibility.

    This function detects "header-like" lines that end with a colon (e.g., "Notes:")
    and ensures there is exactly one empty line between that line and a following list
    item (either a bullet list starting with "-" or a numbered list like "1. ...").
    It does not modify lines that are themselves list items or cases where a blank
    line already exists before the list.

    Parameters
    ----------
    text : str
        The full Markdown string to process.

    Returns
    -------
    str
        The modified Markdown string with a blank line inserted between colon-
        terminated headers and immediately following list items, when applicable.

    Notes
    -----
    - A "list item" is considered any line that, ignoring leading whitespace,
      begins with "- " or "<number>. ".
    - Matching is done line-by-line using multiline regular expressions.
    - The function is conservative and only inserts a blank line when the
      colon-terminated header is immediately followed by a list item.

    Examples
    --------
    Input:
        Title:
        - First
        - Second

    Output:
        Title:

        - First
        - Second
    """
    return re.sub(
        r"^(?!\s*(?:-\s|\d+\.\s)).*?$\n(?=[ \t]*(?:-\s|\d+\.\s))",
        r"\g<0>\n",
        text,
        flags=re.MULTILINE,
    )

#second level formatting inssues
def fix_list_formatting_1(text: str) -> str:
    return re.sub(r"^(?: -)\s+", "    - ", text, flags=re.MULTILINE)

def fix_list_formatting_2(text: str) -> str:
    return re.sub(r"^(?:  -)\s+", "    - ", text, flags=re.MULTILINE)

def fix_list_formatting_3(text: str) -> str:
    return re.sub(r"^(?:   -)\s+", "    - ", text, flags=re.MULTILINE)

#third level formatting issues
def fix_list_formatting_4(text: str) -> str:
    return re.sub(r"^(?:     -)\s+", "        - ", text, flags=re.MULTILINE)

def fix_list_formatting_5(text: str) -> str:
    return re.sub(r"^(?:      -)\s+", "        - ", text, flags=re.MULTILINE)

def fix_list_formatting_6(text: str) -> str:
    return re.sub(r"^(?:       -)\s+", "        - ", text, flags=re.MULTILINE)

#ordinal list formatting issues
def replace_round_bracket_with_dot(text: str) -> str:
    # Match: start of line (^), optional spaces (\s*), number (\d+), closing bracket (\))
    # Replace the bracket with a dot, preserve spaces and number
    return re.sub(r'^(\s*\d+)\)', r'\1.', text, flags=re.MULTILINE)

#second level
def fix_list_formatting_7(text: str) -> str:
    # Match: start of line (^), exactly one space, then digits and dot
    return re.sub(r'^ (\d+\.)', r'    \1', text, flags=re.MULTILINE)

def fix_list_formatting_8(text: str) -> str:
    # Match: start of line (^), exactly two spaces, then digits and dot
    return re.sub(r'^  (\d+\.)', r'    \1', text, flags=re.MULTILINE)

def fix_list_formatting_9(text: str) -> str:
    # Match: start of line (^), exactly three spaces, then digits and dot
    return re.sub(r'^   (\d+\.)', r'    \1', text, flags=re.MULTILINE)

#third level
def fix_list_formatting_10(text: str) -> str:
    # Match: start of line (^), exactly 5 spaces, then digits and dot
    return re.sub(r'^     (\d+\.)', r'        \1', text, flags=re.MULTILINE)

def fix_list_formatting_11(text: str) -> str:
    # Match: start of line (^), exactly 6 spaces, then digits and dot
    return re.sub(r'^      (\d+\.)', r'        \1', text, flags=re.MULTILINE)

def fix_list_formatting_12(text: str) -> str:
    # Match: start of line (^), exactly 7 spaces, then digits and dot
    return re.sub(r'^       (\d+\.)', r'        \1', text, flags=re.MULTILINE)

# Fixing indentation after colon headers
def fix_indentation_after_colon(text: str) -> str:
    lines = text.split('\n')
    fixed_lines = []
    inside_intro_block = False

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        #indent = len(line) - len(stripped)

        # Detect start of a paragraph that ends with ":" but not already a list item
        if stripped.endswith(':') and not stripped.startswith('-') and not re.match(r'^\d+\.', stripped) and not lines[-1] == line:
            inside_intro_block = True
            fixed_lines.append(line)
            indent = len(lines[i+1]) - len(lines[i+1].lstrip())
            continue

        # If we're inside a block and see an over-indented list item
        if inside_intro_block and re.match(r'^\s+- ', line):
            # Dedent by adj. spaces
            fixed_lines.append(line[indent:])
        elif inside_intro_block and re.match(r'^\s+\d+\.', line):
            # Dedent by adj. spaces
            fixed_lines.append(line[indent:])
        elif not re.match(r'^\s*-\s', line):
            # If it's a valid list item, reset the block context
            inside_intro_block = False
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)

def fix_markdown_headings(text: str) -> str:
    """
    Converts text with heading lines of repeated '─' or '-' surrounding a heading
    into valid Markdown headings, ensuring each heading is non-empty and followed by
    a blank line.
    
    Example:
      ────────────────────────────────────────────────────────────────────────
      Why you’re getting “Bad file descriptor”
      ────────────────────────────────────────────────────────────────────────
      
    becomes:
      ## Why you’re getting “Bad file descriptor”
      
      (with a blank line after)
    """
    lines = text.splitlines()
    output = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Check if the current line is a "rule" line
        if re.fullmatch(r'[─-]{10,}', line):
            # Make sure we have at least two more lines to consider
            if i + 2 < len(lines):
                heading_candidate = lines[i + 1].rstrip()
                next_line = lines[i + 2].rstrip()
                
                # Check if the line after next is also a "rule" line
                if re.fullmatch(r'[─-]{10,}', next_line):
                    # Check if the heading candidate is non-empty
                    if heading_candidate.strip():
                        # It's a heading: turn the middle line into a heading
                        output.append(f"## {heading_candidate.strip()}")
                        output.append("")  # blank line after heading
                        i += 3
                        continue
        
        # If it's not a heading section, just add the line as is
        output.append(line)
        i += 1
    
    return "\n".join(output)

def dedent_code_blocks(message: str) -> str:
    """
    Dedent code blocks (triple backticks or triple tildes) if *all* lines
    in the block share the same leading indentation, including the fence lines.
    Handles optional language specifiers like ```python or ~~~javascript.
    """

    lines = message.splitlines(keepends=True)  # preserve line endings
    n = len(lines)
    i = 0
    result = []

    while i < n:
        line = lines[i]
        # Attempt to match an opening fence: indentation + "```" or "~~~",
        # plus optional language specifier, and then end-of-line.
        mo_open = re.match(r'^([ \t]*)(```|~~~)([^\n]*)\r?\n?$', line)
        if not mo_open:
            # Not an opening fence line => just append and move on
            result.append(line)
            i += 1
            continue
        # Extract fence info
        indent = mo_open.group(1)
        fence = mo_open.group(2)
        # The optional language spec is mo_open.group(3), but we don’t need to store it

        block_lines = [line]  # include opening fence line
        found_closing = False
        i_block = i + 1

        # Look for matching closing fence
        while i_block < n:
            candidate = lines[i_block]
            mo_close = re.match(
                rf'^([ \t]*)({re.escape(fence)})([^\n]*)\r?\n?$', 
                candidate
            )
            if mo_close and mo_close.group(1) == indent:
                # Same indentation, same fence => it's the closing fence
                block_lines.append(candidate)
                found_closing = True
                i_block += 1
                break
            else:
                # Not a closing fence => collect as part of the block
                block_lines.append(candidate)
                i_block += 1

        # If we found a closing fence, we can attempt to dedent
        if found_closing:
            # Check uniform indentation for ALL lines in block (opening + content + closing)
            all_share_indent = True
            for bline in block_lines:
                # Ignore empty lines
                if not bline.strip():
                    continue                
                mo_line = re.match(r'^([ \t]*)(.*)$', bline)
                if mo_line:
                    line_indent = mo_line.group(1)
                    if line_indent < indent:
                        all_share_indent = False
                        break

            if all_share_indent:
                # Dedent each line by removing the common indent
                dedented = [bline[len(indent):] if bline.strip() else bline
                            for bline in block_lines]
                result.extend(dedented)
            else:
                # Keep block as-is
                result.extend(block_lines)

            i = i_block
        else:
            # No closing fence found => keep everything as-is
            result.extend(block_lines)
            i = i_block

    return "".join(result)


def escape_html_tags(message: str) -> str:
    """
    Escapes HTML by replacing &, <, and > with their HTML entities, except:
    - fenced code blocks (``` or ~~~) with optional language spec
    - <div> elements whose class includes one of:
      thinking_block_signature, thinking_block_content, message-info
    """
    # Match fenced code blocks (``` or ~~~), non-greedy across newlines
    code_block_pattern = r'(?:```[^\n]*\n.*?```|~~~[^\n]*\n.*?~~~)'
    # Match allowed divs we should NOT escape (class contains any of the target
    # classes.
    allowed_div_pattern = (
        r'(?:<div\b[^>]*class="[^"]*\b(?:thinking_block_signature|thinking_block_content|message-info|image-generation)\b[^"]*"[^>]*>.*?</div>)'
    )
    # Combined pattern: capture protected segments so we can preserve them
    protected_pattern = f'({code_block_pattern}|{allowed_div_pattern})'
    
    parts = re.split(protected_pattern, message, flags=re.DOTALL | re.IGNORECASE)
    result = []
    for i, part in enumerate(parts):
        if part is None:
            continue
        if i % 2 == 0:
            # Outside protected segments: escape &, <, >
            escaped = (part
                       .replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;'))
            result.append(escaped)
        else:
            # Inside protected segments: leave as-is
            result.append(part)
    return ''.join(result)


def process_ai_message(msg):
    try:
        msg, signature, content = BaseModel.extract_thinking_block(msg)
        msg = normalize_bullet_points(msg)
        msg = replace_round_bracket_with_dot(msg)
        msg = fix_indentation_after_colon(msg)
        msg = add_blank_line_after_colon_headers(msg)
        # If the message doesn't start with a letter, then it may start with some 
        # markdown character that we should properly interpret, and thus needs to 
        # be on a newline preceded by an empty line.
        if msg and not msg[0].isalpha():
            msg = '\n\n' + msg
        msg = dedent_code_blocks(msg)
        msg = fix_markdown_headings(msg)
        msg = fix_list_formatting_1(msg)
        msg = fix_list_formatting_2(msg)
        msg = fix_list_formatting_3(msg)
        msg = fix_list_formatting_4(msg)
        msg = fix_list_formatting_5(msg)
        msg = fix_list_formatting_6(msg)
        msg = fix_list_formatting_7(msg)
        msg = fix_list_formatting_8(msg)
        msg = fix_list_formatting_9(msg)
        msg = fix_list_formatting_10(msg)
        msg = fix_list_formatting_11(msg)
        msg = fix_list_formatting_12(msg)
        msg = escape_html_tags(msg)
    except Exception as e:
        logger.error(f"Error processing AI message: {e}")
    return msg


def process_workspace_content(msg):
    try:
        if msg:
            msg = escape_html_tags(msg)
    except Exception as e:
        logger.error(f"Error processing AI message: {e}")
    return msg
