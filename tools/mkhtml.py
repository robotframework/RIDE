from robotide.version import VERSION
import docutils.core

docutils.core.publish_file(
    source_path="../doc/releasenotes/ride-"+VERSION+".rst",
    destination_path="../src/robotide/application/release_notes.html",
    writer_name="html")

print("Now paste content of ../src/robotide/application/release_notes.html to"
      " RELEASE_NOTES in ../src/robotide/application/releasenotes.py")
