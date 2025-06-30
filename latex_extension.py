import re
import markdown
from markdown.preprocessors import Preprocessor

class LaTeXPreservationExtension(markdown.Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(LaTeXPreservationPreprocessor(md), 'latex_preservation', 25)

class LaTeXPreservationPreprocessor(Preprocessor):
    def run(self, lines):
        text = '\n'.join(lines)
        # Replace LaTeX delimiters with unique placeholders
        text = re.sub(r'\\\[(.*?)\\\]', lambda m: f'DISPLAYMATH_START{m.group(1)}DISPLAYMATH_END', text)
        text = re.sub(r'\\\((.*?)\\\)', lambda m: f'INLINEMATH_START{m.group(1)}INLINEMATH_END', text)
        # Split back into lines
        return text.split('\n')

def makeExtension(*args, **kwargs):
    return LaTeXPreservationExtension(*args, **kwargs)
