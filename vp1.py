from cpnpy.cpn.cpn_imp import CPN, Place, Transition, Arc, Marking, EvaluationContext
from cpnpy.cpn.colorsets import ColorSetParser
from cpnpy.visualization.visualizer import CPNGraphViz



# Create CPN
cpn = CPN()


# Define color sets
cs_defs = """
colset INT = int timed;
colset TIME = time;
colset STRING = string;

colset task = product(product(INT, STRING), product(INT, INT));
colset airplane = list task timed;

colset flight = product( STRING, product(INT, INT)) timed;

colset spec_element = product( INT, product(INT, INT));
colset spec = product(list spec_element, list INT);

colset log = STRING;
colset tok = STRING timed;
colset wg = product(STRING , INT) timed;

"""
parser = ColorSetParser()
colorsets = parser.parse_definitions(cs_defs)
airplane =colorsets["airplane"]
flight =colorsets["flight"]
spec =colorsets["spec"]
tok =colorsets["tok"]
wg =colorsets["wg"]
log =colorsets["log"]


# Evaluation context with a user-defined function
user_code = """

def th1(a,s):
    return any(i>0.8*(j) for i,j in zip(a[1:],s[1:]))
def th2(a,s):
    return any(i>0.6*(j) for i,j in zip(a[1:],s[1:]))
def th_error(a,s):
    return any([i>=j for i,j in zip(a[1:],s[1:])])

def TH1(a,s):
    return [th1(i,j) for i,j in zip(a,s)]
def TH2(a,s):
    return [th2(i,j) for i,j in zip(a,s)]
def e(a,s):
    return any(TH1(a,s))

def add(x,y):
    return tuple([i+j for i,j in zip(x,y)])

def fl(a,f):
    return tuple([(i[0],) + add(f[1:],i[1:-1])+ (i[-1]+1,) for i in a])
def reset(a,s,d):
    return tuple([(i[0],0,0,0) if th else i[:-1]+(i[-1]+d,) for i,th in zip(a,TH2(a,s))])
def expire(a,s):
    return any([th_error(i,j) for i,j in zip(a,s)])

def Duration(th,d):
    return sum([i*j for i,j in zip(th,d)])
    """
context = EvaluationContext(user_code=user_code)


# PLACES
active_fleet = Place("active_fleet", airplane)
cpn.add_place(active_fleet)

flights = Place("flights", flight)
cpn.add_place(flights)

specs = Place("specs", spec)
cpn.add_place(specs)

workgroup = Place("workgroup", wg)
cpn.add_place(workgroup)

logs = Place("logs", log)
cpn.add_place(logs)

unsafe = Place("unsafe", tok )
cpn.add_place(unsafe)


# TRANSITIONS
fly = Transition("fly", variables= ["a","f","s","w"], guard="not e(a,s[0]) or (e(a,s[0]) and w[-1] <= 0)",transition_delay=1)
cpn.add_transition(fly)

maintenance = Transition("maintenance", variables=["a","w","s"],guard="e(a,s[0]) and w[-1]>0",transition_delay=0)
cpn.add_transition(maintenance)

expire = Transition("expire", variables=["a","s"],guard="expire(a,s[0]) ",transition_delay=0)
cpn.add_transition(expire)

cleanup_wg = Transition("cleanup_wg", variables=["w","w0"],guard="w0[-1] <= 0")
cpn.add_transition(cleanup_wg)

cleanupfl = Transition("cleanupfl", variables= ["f"])
cpn.add_transition(cleanupfl)


# Arcs
am = Arc(active_fleet, maintenance, "[a]")
cpn.add_arc(am)

ma = Arc(maintenance, active_fleet, "[reset(a,s[0],Duration(TH2(a,s[0]),s[1]))] @+Duration(TH2(a,s[0]),s[1])")
cpn.add_arc(ma)

sm = Arc(specs,maintenance,"[s]")
cpn.add_arc(sm)

ms = Arc(maintenance,specs,"[s]")
cpn.add_arc(ms)

af = Arc(active_fleet,fly,"[a]")
cpn.add_arc(af)

fa = Arc(fly,active_fleet,"[fl(a,f)]")
cpn.add_arc(fa)

ff = Arc(flights,fly,"[f]")
cpn.add_arc(ff)

wm = Arc(workgroup,maintenance,"[w]")
cpn.add_arc(wm)

mw = Arc(maintenance,workgroup,"[(w[0],w[1]-1)]")
cpn.add_arc(mw)

wf = Arc(workgroup,fly,"[w]")
cpn.add_arc(wf)

fw = Arc(fly,workgroup,"[w]")
cpn.add_arc(fw)

ml = Arc(maintenance,logs,"[f'Plane: {a}, Tasks: {TH2(a,s[0])}, Duration: {Duration(TH2(a,s[0]),s[1])}']")
cpn.add_arc(ml)

sf = Arc(specs,fly,"[s]")
cpn.add_arc(sf)

fs = Arc(fly,specs,"[s]")
cpn.add_arc(fs)

fc = Arc(flights,cleanupfl,"[f]")
cpn.add_arc(fc)

ae = Arc(active_fleet,expire,"[a]")
cpn.add_arc(ae)

se = Arc(specs,expire,"[s]")
cpn.add_arc(se)

eu = Arc(expire,unsafe,"'☠️'")
cpn.add_arc(eu)

wc = Arc(workgroup,cleanup_wg,"[w,w0]")
cpn.add_arc(wc)

cw = Arc(cleanup_wg,workgroup,"[w]")
cpn.add_arc(cw)


print (f"PN ready")
# Generate Initial Marking
schedule =[(f"#{i}",1,2) for i in range(20)]

marking = Marking()
marking.set_tokens("active_fleet", [(('t1',0, 0, 0),('t2',0, 0, 0),('t3',0, 0, 0))])  
marking.set_tokens("flights", schedule,timestamps=(range(len(schedule))))  
marking.set_tokens("specs", [((('t1',5,15,20),('t2',6,13,20),('t3',20,30,50)),(4,4,9))])  
marking.set_tokens("workgroup", [('2025',2),('2026',2)], timestamps=[0,25])  

print("Applied Marking")



from cpnpy.cpn.exporter import export_cpn_to_json
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
path = viz.save("vp1")
print("Saved vizualisation to:", path)


print("Initial marking:")
print(prettymarking(marking))  
from sys import argv

if argv[1] == "manual":
    def sequeun(cpn,marking,context):
        transitions = cpn.transitions
        for t in transitions:
            print (t.name,end=' : ')
            if cpn.is_enabled(t,marking,context):
                print("OK",end = '')
                cpn.fire_transition(t,marking,context)
            print("\n")
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

if argv[1] == "sim":
    def sequeun(cpn,marking,context):
        transitions = cpn.transitions
        for t in transitions:
            if cpn.is_enabled(t,marking,context):
                cpn.fire_transition(t,marking,context)
        cpn.advance_global_clock(marking)
        if argv[-1] == "-v":print (f"time:{marking.global_clock}\n marking:{prettymarking(marking)}")
        viz = CPNGraphViz().apply(cpn, marking, format="png")
        # viz.view()
        path = viz.save("vizout")
        # print("Saved to:", path)
    prev_clock = None
    print("Running....")
    while (prev_clock != marking.global_clock):
        prev_clock = marking.global_clock
        if argv[-1] == "-v":print("\n\n")

        sequeun(cpn,marking,context)
        
    print("Final marking:")
    print(prettymarking(marking)) 
    if len(marking.get_multiset("unsafe").tokens) != 0:
        print("UNSAFE") 
    else:print("SAFE") 
if argv[1] == "statespace":
    print ("STATE SPACE !!")
    from cpnpy.analysis.analyzer import StateSpaceAnalyzer 
    print ("creating analyzer ...")  

    analyzer = StateSpaceAnalyzer(cpn, marking, context) 
    print ("OK")  
    
    print ("analyzing ...")  
    report = analyzer.summarize()
    print ("OK")  

    print("=== State Space Report ===")
    for key, val in report.items():
        print(f"{key}: {val}")