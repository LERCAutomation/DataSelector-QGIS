import os
import re

# --- string_functions.py ---
def strip_illegals(input_string, rep_char="_"):
    """Remove illegal/special characters from a string."""
    return re.sub(r'[\\%$:*/?<>\\|~\u00A3.]', rep_char, input_string)
