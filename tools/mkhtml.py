from robotide.version import VERSION
import docutils.core

docutils.core.publish_file(
    source_path="../doc/releasenotes/ride-"+".".join([str(x) for x in VERSION.split('.')[:2]]).replace('v','')+".rst",
    destination_path="../src/robotide/application/release_notes.html",
    writer_name="html")

# Replace { by 	&#123; and } by &#125;
print("Now paste content of ../src/robotide/application/release_notes.html to"
      " RELEASE_NOTES in ../src/robotide/application/releasenotes.py")

source_path = "../CHANGELOG.adoc"
directory = "../src/robotide/application"
destination_path = directory + "/CHANGELOG.html"

from subprocess import run

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
