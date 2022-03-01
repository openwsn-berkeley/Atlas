

def computeSuccess(links, lastTree = None, newLinks=None):
    sender              = None
    tree                = []
    rootBranches        = []
    pdrPerNode          = {}
    processedRootNodes  = []
    sucessProbabilities = {}
    endBranch           = False

    sender = (list(links.keys())[0],list(links.values())[0])



    if not lastTree:
        for item in links.items():
            if item[0][0] == sender[0][0]:
                if item[1] != 0:
                    rootBranches += [item]

        for rb in rootBranches:
            rbExtendedBranch = []
            while True:
                connectingNode = rb
                branch            = {}
                branch[rb[0]] = rb[1]
                idx = 0
                while idx <= len(rootBranches):
                    for link in links.items():

                        if link[0] in rbExtendedBranch:
                            continue
                        if link[0] in branch.keys():
                            continue
                        if link[0][1] == connectingNode[0][0]:
                            continue
                        if link[0][1] in [b[0] for b in branch.keys()]:
                            continue
                        if link[0][0] == connectingNode[0][1]:
                            connectingNode = link
                            branch[link[0]] = link[1]
                            break
                    idx += 1
                if branch == {rb[0]:rb[1]} or endBranch:
                    endBranch = False
                    break
                else:
                    tree += [branch]
                    rbExtendedBranch += branch
    elif newLinks:
        for rb in lastTree:
            rbExtendedBranch = []
            while True:
                connectingNode = (list(rb.keys())[0],list(rb.values())[0])
                branch = rb
                idx = 0
                while idx <= len(rootBranches):
                    for link in newLinks.items():

                        if link[0] in rbExtendedBranch:
                            continue
                        if link[0] in branch.keys():
                            continue
                        if link[0][1] == connectingNode[0][0]:
                            continue
                        if link[0][1] in [b[0] for b in branch.keys()]:
                            continue
                        if link[0][0] == connectingNode[0][1]:
                            connectingNode = link
                            branch[link[0]] = link[1]
                            break
                    idx += 1
                if branch == rb or endBranch:
                    endBranch = False
                    break
                else:
                    tree += [branch]
                    rbExtendedBranch += branch
    else:
        tree = lastTree

    for b in tree:

        pdr = 1
        pdrPerNode[sender[0][0]] = [pdr]

        for node in b.items():

            pdr = pdr * node[1]

            if node in processedRootNodes:
                continue

            if node[0][0] == sender[0][0]:
                processedRootNodes += [node]

            if node[0][1] not in pdrPerNode.keys():
                pdrPerNode[node[0][1]] = [round(pdr,4)]
            else:
                pdrPerNode[node[0][1]] += [round(pdr,4)]


    for node in pdrPerNode.items():
        failureProbability = 1
        for pdr in node[1]:
            failureProbability = failureProbability * (1-round(pdr,4))
        successProbability = 1 - failureProbability
        sucessProbabilities[node[0]] = round(successProbability,4)

    return [sucessProbabilities, tree]

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
        if computeSuccess(test['input']) == test['output']:
            print("=========== PASS ==============")
        else:
            print("=========== FAIL ===============")

if __name__=='__main__':
    main()
