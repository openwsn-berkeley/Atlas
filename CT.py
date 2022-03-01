
from numpy import prod
def _computeSuccess(all_nodes, links, last_tree=None, new_nodes=None, *args, **kwargs):
    all_nodes = all_nodes
    root_node = all_nodes.pop(0)


    tree = _updateTree(last_tree, root_node, all_nodes, new_nodes)

    updated_tree = tree
    print(updated_tree)

    node_pdrs = _updateNodesPDR(links, updated_tree, last_tree)
    sp = _findSuccessProbability(node_pdrs)
    return sp

def _updateTree(last_tree, root_node, all_nodes, new_nodes):
    extended_tree = _extendBranches(last_tree, root_node, all_nodes, new_nodes)
    return extended_tree

def _extendBranches(existing_branches, root_node, all_nodes, new_nodes):

    if not existing_branches:
        new_nodes = all_nodes
    else:
        new_nodes = new_nodes

    existing_branches = _addRootBranches(root_node, new_nodes)
    updated_branches = []

    i = 0
    while i < len(existing_branches):
        for (idx,node) in enumerate(all_nodes):
            if node in existing_branches[i]:
                continue

            new_branch = existing_branches[i] + [node]
            if len(new_branch) == (len(all_nodes) + 1):
                updated_branches.append(new_branch)
            existing_branches.append(new_branch)

        i += 1

    return updated_branches

def _addRootBranches( root_node, new_nodes):
    root = root_node
    root_branches = []
    for node in new_nodes:
        root_branches.append([root, node])

    return root_branches

def _updateNodesPDR(links, tree, last_tree):

    root = tree[0][0]
    node_pdrs = {root: [1]}


    for branch in tree:
        pdr_of_previous_node = 1
        for i in range(len(branch)-1):
            link_pdr = links[(str(branch[i]),str(branch[i+1]))]
            if str(branch[i+1]) not in node_pdrs.keys():
                node_pdrs[str(branch[i + 1])] = []
            node_pdr = round(link_pdr * pdr_of_previous_node,4)
            node_pdrs[str(branch[i+1])] += [node_pdr]
            pdr_of_previous_node = node_pdr

    return node_pdrs

def _findSuccessProbability(node_pdrs):
    nodes = node_pdrs.keys()
    final_pdrs = {}

    for node in nodes:
        failure_probability = round(prod([1-node_pdr for node_pdr in list(set(node_pdrs[node]))]),4)
        success_probability = 1 - failure_probability
        final_pdrs[node] = success_probability

    return final_pdrs







#============================ main ============================================

def main():

    tests = [

        # Test Case 1
        {
            'input'  :{
                       ('A', 'B'): 0.9, ('A', 'C'): 0.8, ('A', 'D'): 0.3,
                       ('B', 'A'): 0.9, ('B', 'C'): 0.7, ('B', 'D'): 0.6,
                       ('C', 'A'): 0.8, ('C', 'B'): 0.7, ('C', 'D'): 0.75,
                       ('D', 'A'): 0.3, ('D', 'B'): 0.6, ('D', 'C'): 0.75
                       },

            'output' : {'A': 1, 'B': 0.9805, 'C': 0.9702, 'D': 0.9549 }
        },

        # Test Case 2
        {
            'input': {
                      ('A','B'):0.95, ('A','C'):0  , ('A','D'):0,
                      ('B','A'):0.95, ('B','C'):0.3, ('B','D'):0.2,
                      ('C','A'):0   , ('C','B'):0.3, ('C','D'):0.95,
                      ('D','A'):0   , ('D','B'):0.2, ('D','C'):0.95
                     },

            'output': {'A': 1, 'B': 0.95, 'C': 0.4141, 'D': 0.4093}
        },

        # Test Case 3
        {
            'input': {
                ('A', 'B'): 0.9, ('A', 'C'): 0.6, ('A', 'D'): 0,
                ('B', 'A'): 0.9, ('B', 'C'): 0.9, ('B', 'D'): 0.6,
                ('C', 'A'): 0.6, ('C', 'B'): 0.9, ('C', 'D'): 0.9,
                ('D', 'A'): 0  , ('D', 'B'): 0.6, ('D', 'C'): 0.9
            },

            'output': {'A': 1, 'B': 0.9689, 'C': 0.9609, 'D': 0.9612}
        },




        ]
    for test in tests:
        if _computeSuccess(['A','B','C','D'],test['input']) == test['output']:
            print("=========== PASS ==============")
        else:
            print("=========== FAIL ===============")

if __name__=='__main__':
    main()
