import javalang
from lm import JAVA_LINE_STRUCTURE, JAVA_WORDS
from JavaLine import JavaLine
import re
import itertools
import re
import difflib
import diff_match_patch
from unidiff import PatchSet
# import pyparsing as pp


def side_by_side_diff(old_text, new_text):
    """
    Calculates a side-by-side line-based difference view.
    
    Wraps insertions in <ins></ins> and deletions in <del></del>.
    """
    def yield_open_entry(open_entry):
        """ Yield all open changes. """
        ls, rs = open_entry
        # Get unchanged parts onto the right line
        if ls[0] == rs[0]:
            yield (False, ls[0], rs[0])
            for l, r in itertools.izip_longest(ls[1:], rs[1:]):
                yield (True, l, r)
        elif ls[-1] == rs[-1]:
            for l, r in itertools.izip_longest(ls[:-1], rs[:-1]):
                yield (l != r, l, r)
            yield (False, ls[-1], rs[-1])
        else:
            for l, r in itertools.izip_longest(ls, rs):
                yield (True, l, r)
 
    line_split = re.compile(r'(?:\r?\n)')
    dmp = diff_match_patch.diff_match_patch()

    diff = dmp.diff_main(old_text, new_text)
    dmp.diff_cleanupSemantic(diff)

    open_entry = ([None], [None])
    for change_type, entry in diff:
        assert change_type in [-1, 0, 1]

        entry = (entry.replace('&', '&amp;')
                      .replace('<', '&lt;')
                      .replace('>', '&gt;'))

        lines = line_split.split(entry)
        print entry
        print lines

        # Merge with previous entry if still open
        ls, rs = open_entry

        line = lines[0]
        if line:
            if change_type == 0:
                ls[-1] = ls[-1] or ''
                rs[-1] = rs[-1] or ''
                ls[-1] = ls[-1] + line
                rs[-1] = rs[-1] + line
            elif change_type == 1:
                rs[-1] = rs[-1] or ''
                rs[-1] += '<ins>%s</ins>' % line if line else ''
            elif change_type == -1:
                ls[-1] = ls[-1] or ''
                ls[-1] += '<del>%s</del>' % line if line else ''
                
        lines = lines[1:]

        if lines:
            if change_type == 0:
                # Push out open entry
                for entry in yield_open_entry(open_entry):
                    yield entry
                
                # Directly push out lines until last
                for line in lines[:-1]:
                    yield (False, line, line)
                
                # Keep last line open
                open_entry = ([lines[-1]], [lines[-1]])
            elif change_type == 1:
                ls, rs = open_entry
                
                for line in lines:
                    rs.append('<ins>%s</ins>' % line if line else '')
                
                open_entry = (ls, rs)
            elif change_type == -1:
                ls, rs = open_entry
                
                for line in lines:
                    ls.append('<del>%s</del>' % line if line else '')
                
                open_entry = (ls, rs)

    # Push out open entry
    for entry in yield_open_entry(open_entry):
        yield entry

def camel_case_split(a):
    return re.sub('([a-zA-Z])([A-Z0-9])', r'\1 \2', a).split()
    # matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z0-9])|$)', identifier)
    # return [m.group(0) for m in matches]

def main():
    # dmp = diff_match_patch.diff_match_patch()
    # text1 = "Hello\nWorld\nBao\nline is added"
    # text2 = "line is added\nBye\nTest"

    # diff = difflib.ndiff(text1.split('\n'), text2.split('\n'))
    # print list(diff)
    # for x in diff:
    #     print x

    # print PatchSet(diff)
    
    # diff = dmp.diff_main("Hello World.", "Goodbye World.")
    # a = dmp.diff_linesToChars(text1, text2)
    # print a
    # lineText1, lineText2, lineArray = a
    # diffs = dmp.diff_main(lineText1, lineText2, False)
    # dmp.diff_charsToLines(diffs, lineArray)
    # dmp.diff_cleanupSemantic(diffs)
    # print diffs
    # print re.sub('([a-zA-Z])([A-Z0-9])', r'\1 \2', 'ThisIsCamelCase123').split()
    
    s  = 'public class Bucky{'
    rule = r'(^public )?class .*'
    line = JavaLine(s)
    print s.split().index("class")
    print line.line_nospace
    print line.line

    print re.match(rule, s)

    # incorrects = set([w for w in line.get_filtered_words() if w not in JAVA_WORDS])
    # print incorrects
    # print line.struct, JAVA_LINE_STRUCTURE[line.struct]
    # print line.line, line.line_nospace

    # tokens = javalang.tokenizer.tokenize(s)
    # parser = javalang.parser.Parser(tokens)
    # for e in parser.parse_expression():
    #     print e
    

    

if __name__ == '__main__':
    main()