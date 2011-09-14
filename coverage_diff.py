import os
import re

comment_line_matcher = re.compile(r'^\s*#[^$]*$')
filename_matcher = re.compile(r'^\+\+\+ b/([\w/\._]+)\s+.+$')
diff_line_matcher = re.compile(r'^@@ -\d+,\d+ \+(\d+),(\d+) @@$')

def report_diffs(diff):
    for line in diff:
        name_match = filename_matcher.match(line)
        if name_match:
            filename = name_match.group(1)
            continue
        diff_line_match = diff_line_matcher.match(line)
        if diff_line_match:
            start_line = int(diff_line_match.group(1))
            number_of_lines = int(diff_line_match.group(2))
            if filename.startswith('src') and not is_covered(filename, start_line, number_of_lines):
                sys.exit(1)

def is_covered(filename, start_line, number_of_lines):
    cover_file_name = filename+',cover'
    if not os.path.isfile(cover_file_name):
        return False
    start_line -= 1
    with open(cover_file_name) as annotation:
        lines = annotation.readlines()[start_line:start_line+number_of_lines]
    lines_not_covered = []
    for index, line in enumerate(lines):
        if not line.startswith('>') and \
           not comment_line_matcher.match(line) and \
           line.strip():
            lines_not_covered += [(index, line)]
    if not lines_not_covered:
        return True
    print 'In file %s all lines not covered!' % filename
    for index, line in lines_not_covered:
        print index+1, line.replace('\n','')
    return False

if __name__ == '__main__':
    import sys
    diff_file = sys.argv[1]
    with open(diff_file) as diff:
        report_diffs(diff)
    print 'All lines covered'
