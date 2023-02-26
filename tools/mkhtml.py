import sys
from os.path import exists
from subprocess import run
import docutils.core
# Requires sudo dnf install pandoc and pip install pypandoc
import pypandoc

from pathlib import Path
assert Path.cwd().resolve() == Path(__file__).resolve().parent

sys.path.insert(0, '../src')
from robotide.version import VERSION
from robotide.application.releasenotes import RELEASE_NOTES
source_path = "../doc/releasenotes/ride-"+".".join([str(x) for x in VERSION.split('.')[:2]]).replace('v','')+".rst"

# Reverted flow: First edit ../src/robotide/application/releasenotes.py and then generate ride-VERSION.rst
if exists(source_path):
    print(f"Release notes exists: {source_path}")
else:
    destination_path = source_path.replace(".rst", ".html")
    with open(destination_path, "w") as rn:
        rn.write("<HTML>\n<BODY>\n\n")
        rn.write(f"{RELEASE_NOTES}\n")
        rn.write("\n</BODY>\n</HTML>\n")
    # With an input file: it will infer the input format from the filename
    output = pypandoc.convert_file(destination_path, 'rst', format='html')
    with open(source_path, "w") as rst:
        rst.write(output)

docutils.core.publish_file(
    source_path=source_path,
    destination_path="../src/robotide/application/release_notes.html",
    writer_name="html")

# Replace { by 	&#123; and } by &#125;
print("Now paste content of ../src/robotide/application/release_notes.html to"
      " RELEASE_NOTES in ../src/robotide/application/releasenotes.py")

source_path = "../CHANGELOG.adoc"
directory = "../src/robotide/application"
destination_path = directory + "/CHANGELOG.html"

run(["a2x3", "-f", "xhtml", "-D", directory, source_path])

# Remove ToC
import re
# <div class="toc"> <p>All notable
with open(destination_path, "r") as sources:
    lines = sources.readlines()
with open(destination_path, "w") as sources:
    for line in lines:
        sources.write(re.sub(r'<div class=\"toc\">.*<p>All notable', '<p>All notable', line))

print(f"Check quality of {destination_path}")
