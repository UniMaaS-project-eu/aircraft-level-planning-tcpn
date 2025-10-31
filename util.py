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
        for token in place["tokens"]:
            make_hashable(token)
    return j


def interactive_viewer(G):
    import networkx as nx
    from networkx_viewer import Viewer
    app = Viewer(G)
    app.mainloop()