import re


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
    start_line -= 1
    with open(filename+',cover') as annotation:
        lines = annotation.readlines()[start_line:start_line+number_of_lines]
    for line in lines:
        if not line.startswith('>'):
            print 'Line not covered %r in file "%s"!!' % (line, filename)
            return False
    return True

if __name__ == '__main__':
    import sys
    diff_file = sys.argv[1]
    with open(diff_file) as diff:
        report_diffs(diff)
    print 'All lines covered'
