# HermiT reasoning report

Reasoner: HermiT (bundled with Owlready2 0.51); JVM: jdk4py 


## Consistency and class satisfiability

| model | triples (with import closure) | expected | HermiT |
|---|---|---|---|
| `core` | 1393 | consistent | consistent (ok) |
| `biochem` | 1575 | consistent | consistent (ok) |
| `example-reaction-chain` | 1943 | consistent | consistent (ok) |
| `ok-rl-circuit` | 1581 | consistent | consistent (ok) |
| `ok-derivative-causality` | 1436 | consistent | consistent (ok) |
| `conflict-two-effort-sources` | 1510 | inconsistent | INCONSISTENT (ok) |
| `conflict-sf-into-i` | 1464 | inconsistent | INCONSISTENT (ok) |
| `conflict-two-species` | 1716 | inconsistent | INCONSISTENT (ok) |
| `conflict-gyrator-causality` | 1446 | inconsistent | INCONSISTENT (ok) |
| `conflict-double-causality` | 1426 | inconsistent | INCONSISTENT (ok) |
| `conflict-signal-causality` | 1430 | inconsistent | INCONSISTENT (ok) |
| `conflict-bond-three-ends` | 1472 | inconsistent | INCONSISTENT (ok) |
| `bfo-bridge` | 18092 | consistent | consistent (ok) |
| `ok-bfo-example` | 18460 | consistent | consistent (ok) |
| `conflict-variable-as-quality` | 18461 | inconsistent | INCONSISTENT (ok) |
| `ok-multidomain-bearer` | 18109 | consistent | consistent (ok) |
| `conflict-effort-kind-clash` | 18099 | inconsistent | INCONSISTENT (ok) |
| `hydraulic` | 1566 | consistent | consistent (ok) |
| `thermal` | 1525 | consistent | consistent (ok) |
| `ok-rs-entropy` | 1576 | consistent | consistent (ok) |
| `conflict-rs-thermal-effort` | 1577 | inconsistent | INCONSISTENT (ok) |
| `ok-windkessel` | 1765 | consistent | consistent (ok) |

### Unsatisfiable classes

- `core`: none
- `biochem`: none
- `bfo-bridge`: none
- `hydraulic`: none
- `thermal`: none

## Entailment tests

| premise | conclusion | expected | HermiT |
|---|---|---|---|
| `example-reaction-chain` | Re port 1 of r1 is flow-determining | entailed | entailed (ok) |
| `example-reaction-chain` | the 0-junction port facing r1 is effort-determining | entailed | entailed (ok) |
| `example-reaction-chain` | the port of species pool A is effort-determining | entailed | entailed (ok) |
| `example-reaction-chain` | the junction on B is a non-degenerate junction | entailed | entailed (ok) |
| `example-reaction-chain` | bond b1 connects species pool A | entailed | entailed (ok) |
| `example-reaction-chain` | Ce:A and Re:r1 are bonded, in both directions | entailed | entailed (ok) |
| `example-reaction-chain` | the chain is NOT a model with derivative causality | not entailed | not entailed (ok) |
| `example-reaction-chain` | the chain is NOT provably fully causal (open world) | not entailed | not entailed (ok) |
| `example-reaction-chain` | the chain is NOT an open reaction network | not entailed | not entailed (ok) |
| `ok-rl-circuit` | the source port is effort-determining | entailed | entailed (ok) |
| `ok-rl-circuit` | the inertia port is flow-determining | entailed | entailed (ok) |
| `ok-rl-circuit` | the junction port facing the inertia is effort-determining | entailed | entailed (ok) |
| `ok-rl-circuit` | the resistor port is effort-determining (full assignment propagated) | entailed | entailed (ok) |
| `ok-rl-circuit` | the resistor is classified as a one-port element | entailed | entailed (ok) |
| `ok-derivative-causality` | the model is classified as having derivative causality | entailed | entailed (ok) |
| `ok-bfo-example` | species component Ce:A is an IAO information content entity | entailed | entailed (ok) |
| `ok-bfo-example` | Ce:A is a BFO generically dependent continuant | entailed | entailed (ok) |
| `ok-bfo-example` | the model has port p_A as a BFO part (transitive, via the element) | entailed | entailed (ok) |
| `ok-bfo-example` | the chemical-potential VARIABLE is NOT a BFO quality | not entailed | not entailed (ok) |
| `bfo-bridge` | molar flow rate profile is a BFO occurrent | entailed | entailed (ok) |
| `bfo-bridge` | chemical potential property is a BFO specifically dependent continuant | entailed | entailed (ok) |
| `bfo-bridge` | a rate process profile is NOT a BFO continuant | not entailed | not entailed (ok) |
| `bfo-bridge` | linear velocity is a BFO occurrent, not a quality | entailed | entailed (ok) |
| `bfo-bridge` | force is a BFO specifically dependent continuant | entailed | entailed (ok) |
| `bfo-bridge` | entropy flow rate is a profile of a heat transfer process | entailed | entailed (ok) |
| `bfo-bridge` | an electric current is NOT a BFO continuant | not entailed | not entailed (ok) |
| `bfo-bridge` | a conducting body is NOT necessarily a thermal body | not entailed | not entailed (ok) |
| `ok-rs-entropy` | the RS element is classified as a dissipative heat source | entailed | entailed (ok) |
| `ok-rs-entropy` | its thermal port is flow-determining | entailed | entailed (ok) |
| `ok-windkessel` | the compliance port is effort-determining | entailed | entailed (ok) |
| `ok-windkessel` | the junction port facing the compliance is flow-determining | entailed | entailed (ok) |
| `thermal` | heat conduction is NOT a dissipative heat source | not entailed | not entailed (ok) |

## OWL 2 DL structural checks

Targeted checks on punning and on non-simple properties in simple-only axioms; see `scripts/dl_checks.py` for scope.

### `bondgraph-core.ttl`

- triples: 1402
- non-simple object properties (chain or transitive): bondedTo, connectsElement
- illegal punning: none
- non-simple property in a simple-only axiom: none
- IRIs resolved against the import closure: no imports loaded
- undeclared IRIs in class/property position: none

### `bondgraph-core.ttl` + `bondgraph-biochem.ttl`

- triples: 1592
- non-simple object properties (chain or transitive): bondedTo, connectsElement
- illegal punning: none
- non-simple property in a simple-only axiom: none
- IRIs resolved against the import closure: no imports loaded
- undeclared IRIs in class/property position: none

### the two modules + `bondgraph-bfo.ttl`

- triples: 2184
- non-simple object properties (chain or transitive): bondedTo, connectsElement
- illegal punning: none
- non-simple property in a simple-only axiom: none
- IRIs resolved against the import closure: 1331 declared in imports
- undeclared IRIs in class/property position: none

### core + the hydraulic and thermal domain modules

- triples: 1722
- non-simple object properties (chain or transitive): bondedTo, connectsElement
- illegal punning: none
- non-simple property in a simple-only axiom: none
- IRIs resolved against the import closure: no imports loaded
- undeclared IRIs in class/property position: none

**Mismatches: 0**
