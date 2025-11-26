def prettymarking(m):
    res = ""
    for place,tokens in m._marking.items():
        res += f"{place} : [\n"
        for token in tokens.tokens:
            res += f"{token} \n"
        res += "\n]"
    return res

def make_hashable(obj):
    if isinstance(obj, list):
        return tuple(make_hashable(x) for x in obj)
    elif isinstance(obj, tuple):
        return tuple(make_hashable(x) for x in obj)
    else:
        return obj
def json2marking(j):
    for place in j.values():
        for idx,token in enumerate(place["tokens"]):
            place["tokens"][idx] = make_hashable(token)
    return j


def interactive_viewer(G):
    import networkx as nx
    from networkx_viewer import Viewer
    app = Viewer(G)
    app.mainloop()

import networkx as nx

def hierarchy_pos(G, root=None, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5):


    if not nx.is_tree(G):
        # Use a spanning tree to approximate hierarchy
        if root is None:
            root = list(G.nodes)[0]
        T = nx.bfs_tree(G, root)
    else:
        T = G
        if root is None:
            root = next(iter(nx.topological_sort(G))) if isinstance(G, nx.DiGraph) else list(G.nodes)[0]

    def _hierarchy_pos(T, root, left, right, vert_loc, pos):
        children = list(T.neighbors(root))
        if len(children) != 0:
            dx = (right - left) / len(children)
            nextx = left
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(T, child, nextx - dx, nextx, vert_loc - vert_gap, pos)
        pos[root] = (xcenter if root == root_node else (left + right) / 2, vert_loc)
        return pos

    root_node = root
    return _hierarchy_pos(T, root, 0, width, vert_loc, {})


def labels2indices(G):

    # Step 1: Create index <-> label mappings
    index_to_label = {i: label for i, label in enumerate(G.nodes())}
    label_to_index = {v: k for k, v in index_to_label.items()}

    # Step 2: Relabel graph to use integer nodes temporarily
    G_int = nx.relabel_nodes(G, label_to_index)
 

    return G_int,index_to_label

def sk_detect(label):
        import re
        label = f"{label}"
        parts = re.split(r'(?=sk\d+)', label)
        sks  = [int(re.findall(r'\d+', p)[2]) for p in parts[1:]]
        skds = [int(re.findall(r'\d+', p)[1]) for p in parts[1:]]
        skdays = []
        for start, dur in zip(sks, skds):
            skdays.extend(range(start, start + dur))
        return skdays
def color_nodes(G, index_to_label, unsafe_key="unsafe"):
    import re
    skdays = sk_detect(list(index_to_label.items())[0])
    colors = []
    for idx, original_label in index_to_label.items():
        # original node has attributes here

        is_unsafe = "unsafe" in f"{original_label}"
        is_undermaintenance = "🔧" in f"{original_label}"
        is_sk = int(re.findall(r'\d+', f"{original_label}")[0]) in skdays
        is_leaf = G.out_degree(idx) == 0

        if is_unsafe:
            colors.append("red")
        elif is_sk and is_undermaintenance:
            colors.append("orange")
        elif is_sk:
            colors.append("yellow")
        elif is_undermaintenance:
            colors.append("gray")
        elif is_leaf:
            colors.append("green")
        else:
            colors.append("lightblue")

    return colors

def custom_marking(m):
    if args.fullmarking:
        return(prettymarking(m))
    else:
        return _custom_marking(m._marking)
def _custom_marking(m):
    # if args.fullmarking:
    #     return(prettymarking(m))
    res = "\n"
    for place,tokens in m.items():
        # if place == "active_fleet":
        #     res += f"Active : {'🛩️'*len(tokens.tokens)}\n"
        if place == "flights":
            res += f"Flights : {len(tokens.tokens)}\n"
        # elif place == "workgroup":
        #     res += f"Workpackages : {len([i for i in tokens.tokens if '@' not in str(i)])}\n"
        elif place == "in_maintenance":
            res += f"maintenance : {'🛩️'*len(tokens.tokens)}\n"
        elif place == "logs":
            res += f"LOGS :[\n"
            for token in tokens.tokens:
                res += f"{token} \n"
            res += "\n]\n"
        elif place == "specs":
            continue
        elif len(tokens.tokens) == 0:
            continue
        else:
            res += f"{place} : [\n"
            for token in tokens.tokens:
                res += f"{token} \n"
            res += "\n]\n"
    return res

def nx_draw(G):
    import re
    import networkx as nx
    from json import dump
    from matplotlib.pyplot  import show
    G_int,labels =  labels2indices(G)

    node_colors = color_nodes(G_int, labels)
    labels_dict = dict(labels)
    # input(labels_dict[8])
    G_int = nx.relabel_nodes(G_int, {n: f"{n}@"+re.findall(r'\d+',f"{(labels_dict[n])}")[0] for n in G_int.nodes()})
    start = [node for node, in_degree in G_int.in_degree() if in_degree == 0][0]
   
    pos = hierarchy_pos(G_int, root=start)
    edge_labels = dict([((n1, n2), d['transition'])
                    for n1, n2, d in G_int.edges(data=True)])

    nx.draw(G_int,pos,with_labels=True,node_color=node_colors)
    nx.draw_networkx_edge_labels(G_int,pos,edge_labels=edge_labels)
   
    dump(labels,open('statespacelabels.json','w'))
    show()
