from cpnpy.cpn.cpn_imp import CPN, Place, Transition, Arc, Marking, EvaluationContext
from cpnpy.cpn.colorsets import ColorSetParser


# Define color sets
cs_defs = """
colset INT = int timed;
colset TIME = time;
colset airplane = product(INT, product(INT, INT)) timed;
colset flight = product(INT, INT) timed;
colset spec = product( product(INT, INT), product(INT, INT));
"""

parser = ColorSetParser()
colorsets = parser.parse_definitions(cs_defs)
airplane =colorsets["airplane"]
flight =colorsets["flight"]
spec =colorsets["spec"]

# Create places and a transition
active_fleet = Place("active_fleet", airplane)
flights = Place("flights", flight)
specs = Place("specs", spec)
maintenance = Place("maintenance", airplane)
bring_down = Transition("bring_down", variables=["x"],guard = "x[0] <= 0 or x[1] <= 0", transition_delay=0)
fly = Transition("fly", variables= ["x","y"], guard="x[0] > 0 and x[1] > 0",transition_delay=1)
bring_up = Transition("bring_up", variables=["x","y"],transition_delay=3)

# Create arcs: consume 'x' from P_In, produce 'x+1' in P_Out after 2 time units
bd_in = Arc(active_fleet, bring_down, "[x]")
bd_out = Arc(bring_down, maintenance, "[x]")
bu_in = Arc(maintenance, bring_up, "[x]")
bu_out = Arc(bring_up, active_fleet, "[(y[0],y[1],y[2])]")
bu_in2 = Arc(specs, bring_up, "[y]")
bu_out2 = Arc(bring_up, specs, "[y]")

fl_in = Arc(active_fleet,fly,"[x]")
fl_out = Arc(fly,active_fleet,"[(x[0]-y[0],x[1]-y[1],x[2])]")
fl_in2 = Arc(flights,fly,"[y]")
# Build the net
cpn = CPN()
cpn.add_place(active_fleet)
cpn.add_place(maintenance)
cpn.add_place(specs)
cpn.add_place(flights)
cpn.add_transition(bring_up)
cpn.add_transition(fly)
cpn.add_transition(bring_down)
cpn.add_arc(bd_in)
cpn.add_arc(bd_out)
cpn.add_arc(bu_in)
cpn.add_arc(bu_out)
cpn.add_arc(fl_in)
cpn.add_arc(fl_out)
cpn.add_arc(fl_in2)
cpn.add_arc(bu_in2)
cpn.add_arc(bu_out2)
# Create a marking
marking = Marking()
schedule =[
    (1,1),
    (1,2),
    (1,3),
    (1,4),
    (1,5),
    (1,6),
    (1,7),
    (1,8),
    (1,9),
    (1,10),
    (1,11),
    (1,12)
    ]
marking.set_tokens("active_fleet", [(5, 15, 20)])  # both at time 0
marking.set_tokens("flights", schedule,timestamps=(range(1,len(schedule)-1)))  # both at time 0
marking.set_tokens("specs", [(5,15,20,3)])  # both at time 0

# Evaluation context with a user-defined function
# user_code = "def double(n): return n*2"
context = EvaluationContext()

# print("Initial marking:")
# print(marking)

from cpnpy.cpn.exporter import export_cpn_to_json

# # Assuming you have a CPN, marking, and context objects as before
exported_json = export_cpn_to_json(cpn, marking, context, "cpn_exported.json", "user_code_exported.py")
print ("exporeded JSON")

def prettymarking(m):
    res = ""
    for place,tokens in m._marking.items():
        res += f"{place} : [\n"
        for token in tokens.tokens:
            res += f"{token} \n"
        res += "\n]"
    return res


print("Initial marking:")
print(prettymarking(marking))  
def sequeun(cpn,marking,context):
    transitions = cpn.transitions
    for t in transitions:
        if cpn.is_enabled(t,marking,context):
            cpn.fire_transition(t,marking,context)
    cpn.advance_global_clock(marking)
    print (f"time:{marking.global_clock}\n marking:{prettymarking(marking)}")
while (input("next:?") != 'x'):
    sequeun(cpn,marking,context)











# # The exported_json dictionary will have all the data. 
# # Additionally, the JSON will be written to "cpn_exported.json".
# # If user code was embedded, it is exported to "user_code_exported.py".
# # Check enabling
# print("Is bd enabled?", cpn.is_enabled(bring_down, marking, context))
# # True, because x=1 is a positive token.

# # Fire the transition
# cpn.fire_transition(bring_down, marking, context)
# print("After firing bd:")
# print(marking)
# # Token (1) is consumed from P_In, token 2 (double(1)) is added to P_Out with timestamp = global_clock + 1 (transition_delay) + 2 (arc delay) = 3

# print("Is bu enabled?", cpn.is_enabled(bring_up, marking, context))
# # True, because x=1 is a positive token.

# # Fire the transition
# cpn.fire_transition(bring_up, marking, context)
# print("After firing bu:")
# print(marking)

# # Advance time
# cpn.advance_global_clock(marking)
# print("After advancing clock:", marking.global_clock)
# # global_clock = 3