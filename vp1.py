from cpnpy.cpn.cpn_imp import CPN, Place, Transition, Arc, Marking, EvaluationContext
from cpnpy.cpn.colorsets import ColorSetParser
from cpnpy.visualization.visualizer import CPNGraphViz

# Define color sets
cs_defs = """
colset INT = int timed;
colset TIME = time;
colset STRING = string;

colset task = product(INT, product(INT, INT));
colset airplane = list task timed;

colset flight = product( STRING, product(INT, INT)) timed;

colset spec_element = product( INT, product(INT, INT));
colset spec = product(list spec_element, list INT);

colset log = STRING;
colset tok = STRING timed;
colset wg = INT timed;

"""
parser = ColorSetParser()
colorsets = parser.parse_definitions(cs_defs)
airplane =colorsets["airplane"]
flight =colorsets["flight"]
spec =colorsets["spec"]
tok =colorsets["tok"]
wg =colorsets["wg"]
log =colorsets["log"]

# PLACES
active_fleet = Place("active_fleet", airplane)
flights = Place("flights", flight)
specs = Place("specs", spec)
workgroup = Place("workgroup", wg)
logs = Place("logs", log)
unsafe = Place("unsafe", tok )



fly = Transition("fly", variables= ["a","f","s","w"], guard="not e(a,s[0]) or (e(a,s[0]) and w <= 0)",transition_delay=1)
maintenance = Transition("maintenance", variables=["a","w","s"],guard="e(a,s[0]) and w>0",transition_delay=0)
expire = Transition("expire", variables=["a","s"],guard="expire(a,s[0]) ",transition_delay=0)
cleanupfl = Transition("cleanupfl", variables= ["f"])


# Evaluation context with a user-defined function
user_code = """

def th1(a,s):
    return any(i>0.8*(j) for i,j in zip(a,s))


def th2(a,s):
    return any(i>0.6*(j) for i,j in zip(a,s))

def th_error(a,s):
    return any([i>=j for i,j in zip(a,s)])


def TH1(a,s):
    return [th1(i,j) for i,j in zip(a,s)]

def TH2(a,s):
    return [th2(i,j) for i,j in zip(a,s)]

def e(a,s):
    return any(TH1(a,s))

def add(x,y):
    return tuple([i+j for i,j in zip(x,y)])

def fl(a,f):
    return tuple([add(f[1:],i[:-1])+ (i[-1]+1,) for i in a])

def reset(a,s,d):
    return tuple([(0,0,0) if th else i[:-1]+(i[-1]+d,) for i,th in zip(a,TH2(a,s))])

def expire(a,s):
    return any([th_error(i,j) for i,j in zip(a,s)])

def Duration(th,d):
    return sum([i*j for i,j in zip(th,d)])
    """
# context = EvaluationContext()


am = Arc(active_fleet, maintenance, "[a]")
# ma = Arc(maintenance, active_fleet, "[reset(a,s[0])] @+888")
ma = Arc(maintenance, active_fleet, "[reset(a,s[0],Duration(TH2(a,s[0]),s[1]))] @+Duration(TH2(a,s[0]),s[1])")
sm = Arc(specs,maintenance,"[s]")
ms = Arc(maintenance,specs,"[s]")
af = Arc(active_fleet,fly,"[a]")
fa = Arc(fly,active_fleet,"[fl(a,f)]")
ff = Arc(flights,fly,"[f]")
wm = Arc(workgroup,maintenance,"[w]")
mw = Arc(maintenance,workgroup,"[w-1]")
wf = Arc(workgroup,fly,"[w]")
fw = Arc(fly,workgroup,"[w]")

ml = Arc(maintenance,logs,"[f'Plane: {a}, Tasks: {TH2(a,s[0])}, Duration: {Duration(TH2(a,s[0]),s[1])}']")
sf = Arc(specs,fly,"[s]")
fs = Arc(fly,specs,"[s]")
fc = Arc(flights,cleanupfl,"[f]")
ae = Arc(active_fleet,expire,"[a]")
se = Arc(specs,expire,"[s]")
eu = Arc(expire,unsafe,"'☠️'")



cpn = CPN()


cpn.add_place(active_fleet)
cpn.add_place(flights)
cpn.add_place(specs)
cpn.add_place(workgroup)
cpn.add_place(logs)
cpn.add_place(unsafe)

cpn.add_transition(fly)
cpn.add_transition(maintenance)
cpn.add_transition(expire)
cpn.add_transition(cleanupfl)

cpn.add_arc(am)
cpn.add_arc(ma)
cpn.add_arc(sm)
cpn.add_arc(ms)
cpn.add_arc(af)
cpn.add_arc(fa)
cpn.add_arc(ff)
cpn.add_arc(wm)
cpn.add_arc(mw)
cpn.add_arc(ml)
cpn.add_arc(sf)
cpn.add_arc(fs)
cpn.add_arc(ae)
cpn.add_arc(se)
cpn.add_arc(eu)
cpn.add_arc(wf)
cpn.add_arc(fw)
cpn.add_arc(fc)



marking = Marking()
schedule =[
    ('#0',0,0),
    ('#1',1,2),
    ('#2',1,2),
    ('#3',3,9),
    ('#4',2,2),
    ('#5',1,2),
    ('#6',1,2),
    ('#7',2,8),
    ('#8',1,4),
    ('#9',1,2),
    ('#10',1,2),
    ('#11',1,2),
    # ('#12',1,2)
]

marking.set_tokens("active_fleet", [((0, 0, 0),(0, 0, 0),(0, 0, 0))])  # both at time 0
marking.set_tokens("flights", schedule,timestamps=(range(len(schedule))))  # both at time 0
marking.set_tokens("specs", [(((5,15,20),(6,13,20),(20,30,50)),(4,4,9))])  # both at time 0
marking.set_tokens("workgroup", [2], timestamps=[0])  # both at time 0
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


path = viz.save("vp1")
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
        # print("Saved to:", path)
    prev_clock = None
    while (input("?\r") != 'x' and prev_clock != marking.global_clock):
        prev_clock = marking.global_clock
        print("\n\n")

        sequeun(cpn,marking,context)
        
    if len(marking.get_multiset("unsafe").tokens) != 0:
        print("UNSAFE") 
    else:print("SAFE") 
if argv[1] == "statespace":
    from cpnpy.analysis.analyzer import StateSpaceAnalyzer 
    analyzer = StateSpaceAnalyzer(cpn, marking, context)   
    report = analyzer.summarize()

    print("=== State Space Report ===")
    for key, val in report.items():
        print(f"{key}: {val}")