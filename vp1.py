from cpnpy.cpn.cpn_imp import CPN, Place, Transition, Arc, Marking, EvaluationContext
from cpnpy.cpn.colorsets import ColorSetParser
from cpnpy.visualization.visualizer import CPNGraphViz

# Define color sets
cs_defs = """
colset INT = int timed;
colset TIME = time;
colset STRING = string;
colset airplane = product(INT, product(INT, INT)) timed;
colset flight = product( STRING, product(INT, INT)) timed;
colset spec = product( INT, product(INT, INT));
colset log = STRING;
colset wg = STRING timed;

"""
parser = ColorSetParser()
colorsets = parser.parse_definitions(cs_defs)
airplane =colorsets["airplane"]
flight =colorsets["flight"]
spec =colorsets["spec"]
wg =colorsets["wg"]
log =colorsets["log"]

# PLACES
active_fleet = Place("active_fleet", airplane)
flights = Place("flights", flight)
specs = Place("specs", spec)
workgroup = Place("workgroup", wg)
logs = Place("logs", log)


fly = Transition("fly", variables= ["a","f","s"], guard="ne(a,s)",transition_delay=1)
maintenance = Transition("maintenance", variables=["a","w","s"],guard="e(a,s,w)",transition_delay=0)


# Evaluation context with a user-defined function
user_code = """

# def th1(a,s):
#     return a>0.8*s
# def th2(a,s):
#     return a>0.6*s

# def TH1(a,s):
#     return [th1(i,j) for i,j in zip(a,s)]

def TH2(a,s):
    return "all tasks"

# def TH2(a,s):
#     return [th2(i,j) for i,j in zip(a,s)]
def e(a,s,w):
    # print(f'a : {a}, s : {s}')
    return any([i==j for i,j in zip(a,s)])
def ne(a,s):
    # print(f'a : {a}, s : {s}')
    return not any([i==j for i,j in zip(a,s)])
def fl(a,f):
    return tuple([(i+j) for i,j in zip(a[:-1],f[1:])]+[a[-1] +1])
def reset(a,s):
    #     return ([i*j for i,j in zip(a,TH2(a,s))])
    return tuple([0 for _ in a])

    """
# context = EvaluationContext()


am = Arc(active_fleet, maintenance, "[a]")
ma = Arc(maintenance, active_fleet, "[reset(a,s)]")
sm = Arc(specs,maintenance,"[s]")
ms = Arc(maintenance,specs,"[s]")
af = Arc(active_fleet,fly,"[a]")
fa = Arc(fly,active_fleet,"[fl(a,f)]")
ff = Arc(flights,fly,"[f]")
wm = Arc(workgroup,maintenance,"[w]")
ml = Arc(maintenance,logs,"[f'maintenance : {a} {TH2(a,s)}']")
sf = Arc(specs,fly,"[s]")
fs = Arc(fly,specs,"[s]")


cpn = CPN()


cpn.add_place(active_fleet)
cpn.add_place(flights)
cpn.add_place(specs)
cpn.add_place(workgroup)
cpn.add_place(logs)

cpn.add_transition(fly)
cpn.add_transition(maintenance)

cpn.add_arc(am)
cpn.add_arc(ma)
cpn.add_arc(sm)
cpn.add_arc(ms)
cpn.add_arc(af)
cpn.add_arc(fa)
cpn.add_arc(ff)
cpn.add_arc(wm)
cpn.add_arc(ml)
cpn.add_arc(sf)
cpn.add_arc(fs)


marking = Marking()
schedule =[
    ('#1',1,2),
    ('#2',1,2),
    ('#3',1,2),
    ('#4',1,2),
    ('#5',1,2),
    ('#6',1,2),
    ('#7',1,2),
    ('#8',1,2),
    ('#9',1,2),
    ('#10',1,2),
    ('#11',1,2),
    ('#12',1,2)
    ]

marking.set_tokens("active_fleet", [(0, 0, 0)])  # both at time 0
marking.set_tokens("flights", schedule,timestamps=(range(1,len(schedule)-1)))  # both at time 0
marking.set_tokens("specs", [(5,15,20)])  # both at time 0
marking.set_tokens("workgroup", ['a','a'], timestamps=[1,1])  # both at time 0
context = EvaluationContext(user_code=user_code)
from cpnpy.cpn.exporter import export_cpn_to_json

# # Assuming you have a CPN, marking, and context objects as before
exported_json = export_cpn_to_json(cpn, marking, context, "vp1.json", "usercode_vp1.py")
print ("exporeded JSON")


def prettymarking(m):
    res = ""
    for place,tokens in m._marking.items():
        res += f"{place} : [\n"
        for token in tokens.tokens:
            res += f"{token} \n"
        res += "\n]"
    return res
viz = CPNGraphViz().apply(cpn, marking, format="png")
    # viz.view()


path = viz.save("vizout")
print("Saved to:", path)
print("Initial marking:")
print(prettymarking(marking))  
from sys import argv

if argv[1] == "manual":
    def sequeun(cpn,marking,context):
        transitions = cpn.transitions
        for t in transitions:
            if cpn.is_enabled(t,marking,context):
                cpn.fire_transition(t,marking,context)
        cpn.advance_global_clock(marking)
        print (f"time:{marking.global_clock}\n marking:{prettymarking(marking)}")
        viz = CPNGraphViz().apply(cpn, marking, format="png")
        # viz.view()
        path = viz.save("vizout")
        print("Saved to:", path)

    while (input("next:?") != 'x'):
        sequeun(cpn,marking,context)
if argv[1] == "statespace":
    from cpnpy.analysis.analyzer import StateSpaceAnalyzer 
    analyzer = StateSpaceAnalyzer(cpn, marking, context)   
    report = analyzer.summarize()

    print("=== State Space Report ===")
    for key, val in report.items():
        print(f"{key}: {val}")