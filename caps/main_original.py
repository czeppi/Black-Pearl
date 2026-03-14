""" The KLP lame sattle cap

This is a rebuild. 
The original use AutoDesk and four Bezier curves as ground plan.
Cause build123d does not support this, this is approximated with four circle segments.
"""

from klp_lame_saddle import CapKind, create_and_show_single_cap


create_and_show_single_cap(cap_kind=CapKind.ORIG, fname='lame-key-cap-orig.stl')