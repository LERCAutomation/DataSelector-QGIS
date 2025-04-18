import os
import re

# --- string_functions.py ---
def strip_illegals(input_string, rep_char="_"):
    """Remove illegal/special characters from a string."""
    return re.sub(r'[\\%$:*/?<>\\|~\u00A3.]', rep_char, input_string)

def fnmatch_to_regex(wildcard_string, schema=None):
    """
    Converts a wildcard string with optional |-separated patterns into a combined regex.
    Optionally prepends schema (e.g. 'dbo.') to each pattern.
    """
    if not wildcard_string:
        return None

    patterns = wildcard_string.split('|')
    regex_patterns = []

    for pattern in patterns:
        # Escape and convert wildcards
        regex = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')
        # Prepend schema if needed
        if schema:
            regex = re.escape(schema) + r'\.' + regex
        regex_patterns.append(f'^{regex}$')

    return '|'.join(regex_patterns)
