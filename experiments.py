import sys
import os
sys.path.insert(0,'/usr/local/lib/python3.7/site-packages/')
import spot
import buddy
from enum import Enum
from automata.fa.nfa import NFA
from automata.fa.dfa import DFA
import graphviz
import pylab
import time
import datetime
import random
import string
spot.setup()

class Verdict(Enum):
    ff = 0
    tt = 1
    nf = 2
    nt= 3
    unknown = 4
    giveUp = 5
    def __str__(self):
        if self.value == 0:
            return 'False'
        elif self.value == 1:
            return 'True'
        elif self.value == 2:
            return 'Unknown (but it won\'t ever be False)'
        elif self.value == 3:
            return 'Unknown (but it won\'t ever be True)'
        elif self.value == 4:
            return 'Unknown'
        else:
            return 'Give Up'

class Monitor:
    def __init__(self, phi, aps):
        self.__aps = aps
        autP, outP = self.setup(phi)
        autN, outN = self.setup(spot.formula('!(' + phi + ')').to_str())
        self.__aut, self.__out = self.combine(autP, outP, autN, outN)
    def setup(self, phi):
        aut = spot.degeneralize(spot.translate(phi, 'complete'))
        states = set()
        statesAux = set()
        fin1 = set()
        init = aut.get_init_state_number()
        states.add(aut.get_init_state_number())
        statesAux.add(aut.get_init_state_number())
        while statesAux:
            s0 = statesAux.pop()
            for t in aut.out(s0):
                if t.dst not in states:
                    states.add(t.dst)
                    statesAux.add(t.dst)

        for s in states:
            aut.set_init_state(s)
            if not aut.is_empty():
                fin1.add(s)
        aut.set_init_state(init)

        transitions = {}
        for s in states:
            transitions[str(s)] = {}
            for t in aut.out(s):
                for ap in self.__aps:
                    bdd = buddy.bddtrue
                    for ap1 in self.__aps:
                        if ap == ap1:
                            p = aut.register_ap(ap1)
                            bdd = bdd & buddy.bdd_ithvar(p)
                        else:
                            p = aut.register_ap(ap1)
                            bdd = bdd & buddy.bdd_nithvar(p)
                    if (t.cond & bdd) != buddy.bddfalse:
                        if ap not in transitions[str(s)]:
                            transitions[str(s)][ap] = set()
                        transitions[str(s)][ap].add(str(t.dst))

        nfa = NFA(
            states=set([str(s) for s in states]),
            input_symbols=set(self.__aps),
            transitions=transitions,
            initial_state=str(aut.get_init_state_number()),
            final_states=set([str(s) for s in fin1])
        )
        dfa = DFA.from_nfa(nfa).minify()

        fin2 = set()
        for s in dfa.final_states:
            nope = False
            statesAux1 = set()
            statesAux2 = set()
            statesAux1.add(s)
            statesAux2.add(s)
            while statesAux2:
                s0 = statesAux2.pop()
                if s0 not in dfa.final_states:
                    nope = True
                    break
                for ev in dfa.transitions[s0]:
                    if dfa.transitions[s0][ev] not in statesAux1:
                        statesAux1.add(dfa.transitions[s0][ev])
                        statesAux2.add(dfa.transitions[s0][ev])
            if not nope:
                fin2.add(s)

        out = {}
        for s in dfa.states:
            if s not in dfa.final_states:
                out[s] = Verdict.ff
            elif s in fin2:
                out[s] = Verdict.tt
            else:
                out[s] = Verdict.unknown
        return dfa, out
    def next(self, ev):
        self.__aut.initial_state = self.__aut.transitions[self.__aut.initial_state][ev]
        return self.__out[self.__aut.initial_state]
        # autP.initial_state = autP.transitions[autP.initial_state][ev]
        # autN.initial_state = autN.transitions[autN.initial_state][ev]
        # if outP[autP.initial_state] == Verdict.ff:
        #     return Verdict.ff
        # if outN[autN.initial_state] == Verdict.ff:
        #     return Verdict.tt
        # if outP[autP.initial_state] == Verdict.tt and outN[autN.initial_state] == Verdict.tt:
        #     return Verdict.giveUp
        # if outP[autP.initial_state] == Verdict.tt and outN[autN.initial_state] == Verdict.unknown:
        #     return Verdict.nf
        # if outP[autP.initial_state] == Verdict.unknown and outN[autN.initial_state] == Verdict.tt:
        #     return Verdict.nt
        # else:
        #     return Verdict.unknown
    def combine(self, autP, outP, autN, outN):
        states = set()
        for s1 in autP.states:
            for s2 in autN.states:
                states.add((s1, s2))
        initial_state = str((autP.initial_state, autN.initial_state))
        final_states = set()
        for s1 in autP.final_states:
            for s2 in autN.final_states:
                final_states.add(str((s1, s2)))
        transitions = {}
        for (s1, s2) in states:
            transitions[str((s1,s2))] = {}
            for ev in autP.transitions[s1]:
                if ev in autN.transitions[s2]:
                    transitions[str((s1,s2))][ev] = str((autP.transitions[s1][ev], autN.transitions[s2][ev]))
        aut = DFA(
            states=set([str(s) for s in states]),
            input_symbols=set(self.__aps),
            transitions=transitions,
            initial_state=initial_state,
            final_states=final_states
        )
        aut._remove_unreachable_states()
        out = {}
        for (s1, s2) in states:
            if str((s1, s2)) not in aut.states: continue
            if outP[s1] == Verdict.ff:
                out[str((s1, s2))] = Verdict.ff
            elif outN[s2] == Verdict.ff:
                out[str((s1, s2))] = Verdict.tt
            elif outP[s1] == Verdict.tt and outN[s2] == Verdict.tt:
                out[str((s1, s2))] = Verdict.giveUp
            elif outP[s1] == Verdict.tt and outN[s2] == Verdict.unknown:
                out[str((s1, s2))] = Verdict.nf
            elif outP[s1] == Verdict.unknown and outN[s2] == Verdict.tt:
                out[str((s1, s2))] = Verdict.nt
            else:
                out[str((s1, s2))] = Verdict.unknown
        return aut, out
    def show(self):
        dot = graphviz.Digraph('Monitor')
        d = {}
        i = 0
        for s in self.__aut.states:
            d[s] = str(i)
            if self.__out[s] == Verdict.tt:
                if s == self.__aut.initial_state:
                    dot.node(str(i), label=str(i), color='green', style='filled', shape='doublecircle')
                else:
                    dot.node(str(i), label=str(i), color='green', style='filled')
            elif self.__out[s] == Verdict.ff:
                if s == self.__aut.initial_state:
                    dot.node(str(i), label=str(i), color='red', style='filled', shape='doublecircle')
                else:
                    dot.node(str(i), label=str(i), color='red', style='filled')
            elif self.__out[s] == Verdict.giveUp:
                if s == self.__aut.initial_state:
                    dot.node(str(i), label=str(i), color='azure4', style='filled', shape='doublecircle')
                else:
                    dot.node(str(i), label=str(i), color='azure4', style='filled')
            elif self.__out[s] == Verdict.nf:
                if s == self.__aut.initial_state:
                    dot.node(str(i), label=str(i), color='aquamarine3', style='filled', shape='doublecircle')
                else:
                    dot.node(str(i), label=str(i), color='aquamarine3', style='filled')
            elif self.__out[s] == Verdict.nt:
                if s == self.__aut.initial_state:
                    dot.node(str(i), label=str(i), color='coral1', style='filled', shape='doublecircle')
                else:
                    dot.node(str(i), label=str(i), color='coral1', style='filled')
            else:
                if s == self.__aut.initial_state:
                    dot.node(str(i), label=str(i), color='yellow', style='filled', shape='doublecircle')
                else:
                    dot.node(str(i), label=str(i), color='yellow', style='filled')
            i = i + 1
        for s in self.__aut.states:
            for ev in self.__aut.transitions[s]:
                dot.edge(d[s], d[self.__aut.transitions[s][ev]], label=ev)
        with open('monitor.dot', 'w') as file:
            file.write(str(dot))

# def nextSpotMonitor(mon, aps, ev):
#     event = buddy.bddtrue
#     for ap in aps:
#         p = mon.register_ap(ap)
#         if ap == ev:
#             event = event & buddy.bdd_ithvar(p)
#         else:
#             event = event & buddy.bdd_nithvar(p)
#     for t in mon.out(mon.get_init_state_number()):
#         if (t.cond & event) != buddy.bddfalse:
#             mon.set_init_state(t.dst)
#             break
#     return

def length(f):
    global count
    if f._is(spot.op_And) or f._is(spot.op_Or) or f._is(spot.op_Xor) or f._is(spot.op_X) or f._is(spot.op_U) or f._is(spot.op_U) or f._is(spot.op_W) or f._is(spot.op_G) or f._is(spot.op_F) or f._is(spot.op_M):
        count = count + 1
    return False
def main(args):
    global count
    n = int(args[1])
    min_size_ltl = int(args[2])
    max_size_ltl = int(args[3])
    l_trace = int(args[4])
    n_times = int(args[5])

    times_gen = {}
    times_gen_spot = {}
    times_gen_lama = {}
    times_run = {}
    ap = list(string.ascii_lowercase)
    progress = 0
    init_n = n
    for ltl in spot.randltl(list(ap)):
        if n==0: break
        ltl = ltl.negative_normal_form()
        count = 0
        ltl.traverse(length)
        if count > max_size_ltl: continue
        if count < min_size_ltl: continue
        n = n - 1
        start = datetime.datetime.now()
        monitor = Monitor(str(ltl), ap)
        end = datetime.datetime.now()
        elapsed_time = (end - start)
        if count not in times_gen:
            times_gen[count] = [elapsed_time.microseconds/1000, 1]
        else:
            times_gen[count][1] = times_gen[count][1] + 1
            times_gen[count][0] = times_gen[count][0] + ((elapsed_time.microseconds/1000 - times_gen[count][0]) / times_gen[count][1])
        start = datetime.datetime.now()
        spot.translate(str(ltl), 'monitor', 'det')
        end = datetime.datetime.now()
        elapsed_time = (end - start)
        if count not in times_gen_spot:
            times_gen_spot[count] = [elapsed_time.microseconds/1000, 1]
        else:
            times_gen_spot[count][1] = times_gen_spot[count][1] + 1
            times_gen_spot[count][0] = times_gen_spot[count][0] + ((elapsed_time.microseconds/1000 - times_gen_spot[count][0]) / times_gen_spot[count][1])
        print(ltl)
        with open('tmp.sh', 'w') as file:
            file.write('java -jar /media/angelo/WorkData/lamaconv-snapshot-2016-09-07/rltlconv.jar "LTL=(' + str(ltl).replace('|','||').replace('&', '&&').replace('M', 'U').replace('W', 'U') + '),ALPHABET=' + str(ap).replace('\'', '') + '" --formula --nbas --min --nfas --dfas --min --moore')
            start = datetime.datetime.now()
            stream = os.popen('sh tmp.sh')
            output = stream.read()
            end = datetime.datetime.now()
            if count not in times_gen_lama:
                times_gen_lama[count] = [elapsed_time.microseconds/1000, 1]
            else:
                times_gen_lama[count][1] = times_gen_lama[count][1] + 1
                times_gen_lama[count][0] = times_gen_lama[count][0] + ((elapsed_time.microseconds/1000 - times_gen_lama[count][0]) / times_gen_lama[count][1])
        progress = (init_n - n) / init_n * 100
        sys.stdout.write("Generation progress: %.2f%%   \r" % (progress) )
        sys.stdout.flush()
    print('')
    monitor = Monitor(str(ltl), ap)
    progress = 0
    for l in range(1, l_trace+1):
        times_run[l] = 0
        for i in range(0, n_times):
            start = datetime.datetime.now()
            for j in range(0, l):
                monitor.next(ap[random.randint(0, len(ap)-1)])
            end = datetime.datetime.now()
            elapsed_time = (end - start)
            times_run[l] = times_run[l] + elapsed_time.microseconds/1000
        times_run[l] = times_run[l] / n_times

        progress = l / l_trace * 100
        sys.stdout.write("Verification progress: %.2f%%   \r" % (progress) )
        sys.stdout.flush()
    print('')
    keys = list(times_gen.keys())
    keys.sort()
    with open('generation.csv', 'w') as file:
        for k in keys:
            file.write(str(k) + '; ' + str(times_gen[k][0]) + '; ' + str(times_gen_spot[k][0]) + '; ' + str(times_gen_lama[k][0]) + '\n')
    keys = list(times_run.keys())
    keys.sort()
    with open('verification.csv', 'w') as file:
        for k in keys:
            file.write(str(k) + '; ' + str(times_run[k]) + '\n')



if __name__ == '__main__':
    main(sys.argv)
