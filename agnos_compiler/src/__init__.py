###############################################################################
# agnos compiler
#
# APIs:
#    * compile()
#    * load_spec()
#
# Usage: agnosc -t TARGET idlfile.xml
###############################################################################
from .compiler import compile, load_spec, IDLError


