# Monitor with Safety and CoSafety Completions

## What to install
- SPOT: https://spot.lrde.epita.fr/
- Automata: https://github.com/caleb531/automata#class-dfafa
- GraphViz: https://pypi.org/project/graphviz/

## How to run

```bash
$- python main.py <LTL_property> <Atomic_Propositions> <Trace_File>
```

where:
- <LTL_property> is the LTL property to verify
- <Atomic_Propositions> is the set of atomic propositions used in the property and the trace file
- <Trace_File> is the name of the file containing the trace of events to be analysed by the monitor

## Example of use

Safety property: G p ("p always holds")
```bash
$- python main.py 'G p' '[p,q]' trace1.txt
ltl G p
ap {'p', 'q'}
filename trace1.txt

Verdict: False
```

Co-Safety property: F q ("q eventually holds")
```bash
$- python main.py 'F q' '[p,q]' trace1.txt
ltl F q
ap {'p', 'q'}
filename trace1.txt

Verdict: True
```

Non-Monitorable property: GF p ("it always true that eventually p holds")
```bash
$- python main.py 'GF q' '[p,q]' trace1.txt
ltl GF q
ap {'p', 'q'}
filename trace1.txt

Verdict: Give Up
```

Safety property: G p ("p always holds")
```bash
$- python main.py 'G p' '[p,q]' trace2.txt
ltl G p
ap {'q', 'p'}
filename trace2.txt

Verdict: Unknown (but it will not ever be True)
```

Co-Safety property: F q ("q eventually holds")
```bash
$- python main.py 'F q' '[p,q]' trace2.txt
ltl F q
ap {'p', 'q'}
filename trace2.txt

Verdict: Unknown (but it will not ever be False)
```

Both Safety and Co-Safety property: X p ("p holds in next step")
```bash
$- python main.py 'X p' '[p,q]' trace2.txt
ltl X p
ap {'p', 'q'}
filename trace2.txt

Verdict: Unknown
```

The tool also generates a .dot file that can be visualised, for instance as follows:
```bash
$- dot -Tps monitor.dot -o monitor.ps
```
