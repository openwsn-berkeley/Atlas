"""
Algorithmic implementation of robot motion planning algorithms.
E.g., BFS, Djikstra's, A*, D* Lite, RRT

Created by: Felipe Campos, fmrcampos@berkeley.edu
Date: Mon, Oct 4, 2021
"""

import abc

from typing import List, Any

'''
NOTES:
- Maybe include abstract graph representation (list of nodes or otherwise idk) that easily maps back to Atlas rep
- This allows for more general algorithmic implementation, but may not make sense if we're always doing 2D stuff
- It's likely that each implementation will define it's own graph structure (with or without costs etc.)
- So maybe we define a basic graph class and extend from there?
'''

class PathPlanner(abc.ABC):
    @abc.abstractmethod
    def computePath(self, *args, **kwargs) -> List[Any]:
        ...

# TODO: implementations here