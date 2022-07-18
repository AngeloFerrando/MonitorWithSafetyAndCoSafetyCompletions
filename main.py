import sys
sys.path.insert(0,'/usr/local/lib/python3.7/site-packages/')
import spot
import buddy
from enum import Enum
from automata.fa.nfa import NFA
from automata.fa.dfa import DFA
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
        self.__autP, self.__outP = self.setup(phi)
        self.__autN, self.__outN = self.setup(spot.formula('!(' + phi + ')').to_str())
        self.autP = self.__autP
        self.outP = self.__outP
        self.autN = self.__autN
        self.outN = self.__outN
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
        self.__autP.initial_state = self.__autP.transitions[self.__autP.initial_state][ev]
        self.__autN.initial_state = self.__autN.transitions[self.__autN.initial_state][ev]

        if self.__outP[self.__autP.initial_state] == Verdict.ff:
            return Verdict.ff
        if self.__outN[self.__autN.initial_state] == Verdict.ff:
            return Verdict.tt
        if self.__outP[self.__autP.initial_state] == Verdict.tt and self.__outN[self.__autN.initial_state] == Verdict.tt:
            return Verdict.giveUp
        if self.__outP[self.__autP.initial_state] == Verdict.tt and self.__outN[self.__autN.initial_state] == Verdict.unknown:
            return Verdict.nf
        if self.__outP[self.__autP.initial_state] == Verdict.unknown and self.__outN[self.__autN.initial_state] == Verdict.tt:
            return Verdict.nt
        else:
            return Verdict.unknown

def main(args):
    ltl = args[1]
    ap = set(args[2].replace('[','').replace(']','').replace(' ', '').split(','))
    filename = args[3]
    print('ltl ' + str(ltl))
    print('ap ' + str(ap))
    print('filename ' + str(filename))

    monitor = Monitor(ltl, ap)
    verdict = None
    try:
        with open(filename, 'r') as file:
            while True:
                event = file.readline().replace('\n', '')
                if not event:
                    break
                verdict = monitor.next(event)
        print('\nVerdict: ' + str(verdict))
    except KeyError:
        print('\nError: the event ', event, ' is not part of the allowed atomic propositions', ap)

if __name__ == '__main__':
    main(sys.argv)
