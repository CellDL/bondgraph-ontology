# HermiT reasoning report

Reasoner: HermiT (bundled with Owlready2 0.51); JVM: jdk4py 


## Consistency and class satisfiability

| model | triples (with import closure) | expected | HermiT |
|---|---|---|---|
| `core` | 1340 | consistent | consistent (ok) |
| `biochem` | 1522 | consistent | consistent (ok) |
| `example-reaction-chain` | 1890 | consistent | consistent (ok) |
| `ok-rl-circuit` | 1528 | consistent | consistent (ok) |
| `ok-derivative-causality` | 1383 | consistent | consistent (ok) |
| `conflict-two-effort-sources` | 1457 | inconsistent | INCONSISTENT (ok) |
| `conflict-sf-into-i` | 1411 | inconsistent | INCONSISTENT (ok) |
| `conflict-two-species` | 1663 | inconsistent | INCONSISTENT (ok) |
| `conflict-gyrator-causality` | 1393 | inconsistent | INCONSISTENT (ok) |
| `conflict-double-causality` | 1373 | inconsistent | INCONSISTENT (ok) |
| `conflict-signal-causality` | 1377 | inconsistent | INCONSISTENT (ok) |
| `conflict-bond-three-ends` | 1419 | inconsistent | INCONSISTENT (ok) |
| `bfo-bridge` | 18039 | consistent | consistent (ok) |
| `ok-bfo-example` | 18407 | consistent | consistent (ok) |
| `conflict-variable-as-quality` | 18408 | inconsistent | INCONSISTENT (ok) |
| `ok-multidomain-bearer` | 18056 | consistent | consistent (ok) |
| `conflict-effort-kind-clash` | 18046 | inconsistent | INCONSISTENT (ok) |

### Unsatisfiable classes

- `core`: none
- `biochem`: none
- `bfo-bridge`: none

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

## OWL 2 DL structural checks

Targeted checks on punning and on non-simple properties in simple-only axioms; see `scripts/dl_checks.py` for scope.

### `bondgraph-core.ttl`

- triples: 1349
- non-simple object properties (chain or transitive): bondedTo, connectsElement
- illegal punning: none
- non-simple property in a simple-only axiom: none
- IRIs resolved against the import closure: no imports loaded
- undeclared IRIs in class/property position: none

### `bondgraph-core.ttl` + `bondgraph-biochem.ttl`

- triples: 1539
- non-simple object properties (chain or transitive): bondedTo, connectsElement
- illegal punning: none
- non-simple property in a simple-only axiom: none
- IRIs resolved against the import closure: no imports loaded
- undeclared IRIs in class/property position: none

### the two modules + `bondgraph-bfo.ttl`

- triples: 2131
- non-simple object properties (chain or transitive): bondedTo, connectsElement
- illegal punning: none
- non-simple property in a simple-only axiom: none
- IRIs resolved against the import closure: 1331 declared in imports
- undeclared IRIs in class/property position: none

**Mismatches: 0**
