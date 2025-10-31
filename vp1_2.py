import sys, os
import pandas as pd
import math
import copy

sys.path.append(os.path.join(os.path.dirname(__file__), "cpn-py"))

from cpnpy.cpn.cpn_imp import CPN, Place, Transition, Arc, Marking, EvaluationContext
from cpnpy.cpn.cpn_imp import Token
from cpnpy.cpn.colorsets import ColorSetParser
from cpnpy.visualization.visualizer import CPNGraphViz
from cpnpy.cpn.exporter import export_cpn_to_json

# Convert lists to tuples
def make_hashable(obj):
    if isinstance(obj, list):
        return tuple(make_hashable(x) for x in obj)
    elif isinstance(obj, tuple):
        return tuple(make_hashable(x) for x in obj)
    else:
        return obj

# Load Dataset and create tokens
df = pd.read_excel("new_dataset_changed.xlsx", sheet_name="Aircraft_1")

airplane_token = [(int(row["clocks_cycles"]), int(row["clocks_hours"]), int(row["clocks_days"])) for _, row in df.iterrows()]

spec_elements = [(int(row["frequency_flight_cycles"]), int(row["frequency_flight_hours"]), int(row["frequency_days"])) for _, row in df.iterrows()]

workhrs_list = [float(row["workhrs"]) for _, row in df.iterrows()]

spec_token = (spec_elements, workhrs_list)


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
airplane = colorsets["airplane"]
flight = colorsets["flight"]
spec = colorsets["spec"]
tok = colorsets["tok"]
wg = colorsets["wg"]
log = colorsets["log"]

# PLACES
active_fleet = Place("active_fleet", airplane)
flights = Place("flights", flight)
specs = Place("specs", spec)
workgroup = Place("workgroup", wg)
logs = Place("logs", log)
unsafe = Place("unsafe", tok)

# TRANSITIONS 
fly = Transition("fly", variables=["a", "f", "s", "w"],
                 guard="not e(a,s[0]) or (e(a,s[0]) and w <= 0)", transition_delay=1)
maintenance = Transition("maintenance", variables=["a", "w", "s"],
                         guard="e(a,s[0]) and w>0", transition_delay=0)
expire = Transition("expire", variables=["a", "s"],
                    guard="expire(a,s[0])", transition_delay=0)

# Evaluation context with a user-defined function
user_code = """
import math

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
    return [add(f[1:],i[:-1])+ (i[-1]+1,) for i in a]

def reset(a,s,d):
    return [(0,0,0) if th else i[:-1]+(i[-1]+d,) for i,th in zip(a,TH2(a,s))]

def expire(a,s):
    return any([th_error(i,j) for i,j in zip(a,s)])

def Duration(th,d):
    return math.ceil(sum([i*j for i,j in zip(th,d)]) / 8)
"""

cpn = CPN()

for p in [active_fleet, flights, specs, workgroup, logs, unsafe]:
    cpn.add_place(p)

for t in [fly, maintenance, expire]:
    cpn.add_transition(t)

arcs = [
    Arc(active_fleet, maintenance, "[a]"),
    Arc(maintenance, active_fleet, "[reset(a,s[0],Duration(TH2(a,s[0]),s[1]))] @+Duration(TH2(a,s[0]),s[1])"),
    Arc(specs, maintenance, "[s]"),
    Arc(maintenance, specs, "[s]"),
    Arc(active_fleet, fly, "[a]"),
    Arc(flights, fly, "[f]"),
    Arc(fly, active_fleet, "[fl(a,f)]"),
    Arc(workgroup, maintenance, "[w]"),
    Arc(maintenance, workgroup, "[w-1]"),
    Arc(workgroup, fly, "[w]"),
    Arc(fly, workgroup, "[w]"),
    Arc(maintenance, logs, "[f'Plane: {a}, Tasks: {TH2(a,s[0])}, Duration: {Duration(TH2(a,s[0]),s[1])}']"),
    Arc(specs, fly, "[s]"),
    Arc(fly, specs, "[s]"),
    Arc(active_fleet, expire, "[a]"),
    Arc(specs, expire, "[s]"),
    Arc(expire, unsafe, "'☠️'")
]
for a in arcs:
    cpn.add_arc(a)

#hashable_airplane_token = make_hashable(airplane_token)
hashable_spec_token = make_hashable(spec_token)
# Initial Marking 
marking = Marking()
marking.set_tokens("active_fleet", [tuple(airplane_token)])  # Aircraft utilization clocks
marking.set_tokens("specs", [hashable_spec_token])
marking.set_tokens("workgroup", [1], timestamps=[1])

num_days = 68000
flight_schedule = []
flight_id = 0
for day in range(num_days):
    flight_hours = 3  
    flight_cycles = 1  
    flight_schedule.append((f'#{flight_id}', flight_cycles, flight_hours))
    flight_id += 1

marking.set_tokens("flights", flight_schedule, timestamps=(range(len(flight_schedule))))

context = EvaluationContext(user_code=user_code)

# Export JSON 
# exported_json = export_cpn_to_json(cpn, marking, context, "vp1.json", "usercode_vp1.py")
# print("Exported JSON")

# Visualization 
def prettymarking(m):
    res = ""
    for place, tokens in m._marking.items():
        res += f"{place} : [\n"
        for token in tokens.tokens:
            res += f"{token} \n"
        res += "\n]"
    return res

# viz = CPNGraphViz().apply(cpn, marking, format="png")
# path = viz.save("vp1")
# print("Saved to:", path)
print("Initial marking:")
print(prettymarking(marking))

from sys import argv

if len(argv) > 1 and argv[1] == "manual":
    def sequeun(cpn, marking, context):
        transitions = cpn.transitions
        for t in transitions:
            if cpn.is_enabled(t, marking, context):
                cpn.fire_transition(t, marking, context)
        cpn.advance_global_clock(marking)
        print(f"time:{marking.global_clock}\n active_fleet:{(marking.get_multiset("active_fleet").tokens)}")
        print(f"time:{marking.global_clock}\n specs:{(marking.get_multiset("specs").tokens)}")
        print(f"time:{marking.global_clock}\n logs:{(marking.get_multiset("logs").tokens)}")
        viz = CPNGraphViz().apply(cpn, marking, format="png")
        path = viz.save("vizout")

    prev_clock = None
    while (input("?\r") != 'x' and prev_clock != marking.global_clock):
        prev_clock = marking.global_clock
        #print("\n\n")
        sequeun(cpn, marking, context)

    if len(marking.get_multiset("unsafe").tokens) != 0:
        print("UNSAFE")
    else:
        print("SAFE")

elif len(argv) > 1 and argv[1] == "statespace":
    from cpnpy.analysis.analyzer import StateSpaceAnalyzer
    analyzer = StateSpaceAnalyzer(cpn, marking, context)
    report = analyzer.summarize()

    # print("=== State Space Report ===")
    # for key, val in report.items():
    #     print(f"{key}: {val}")

    # Check if unsafe is ever reached
    unsafe_states = []
    for node in analyzer.RG.nodes(data=True):
        # input(node[1])
        marking_state = node[1]['marking']
        tokens = marking_state.get_multiset("unsafe").tokens
        # print(tokens)
        if tokens:  # if there are any tokens in unsafe
            unsafe_states.append((node[0], tokens))

    if unsafe_states:
        print("\n⚠️  UNSAFE")
        # for state_id, tokens in unsafe_states:
        #     print(f"State {state_id}: {tokens}")
    else:
        print("\n✅ SAFE")