# Bond Graph Ontology Core — v0.1.0 draft

An OWL 2 DL axiomatisation of the bond graph formalism, written as a standalone core
with a separate chemical-domain extension for physiological modelling.

## Files

| File | Contents |
|---|---|
| [bondgraph-core.ttl](bondgraph-core.ttl) | The core ontology. 93 classes, 27 object properties, 5 data properties, 16 annotation properties, 11 named individuals, 1348 triples. |
| [bondgraph-biochem.ttl](bondgraph-biochem.ttl) | Chemical/physiological extension: Ce, Re, chemostat, flowstat, stoichiometric and electrogenic transducers, compartments. 14 classes, 191 triples. |
| [bondgraph-bfo.ttl](bondgraph-bfo.ttl) | Bridge pinning the ontology to BFO, via IAO and RO. 49 new classes, 1 new object property, 601 triples. |
| [example-reaction-chain.ttl](example-reaction-chain.ttl) | Exemplar model: the reversible chain A ⇌ B ⇌ C, with species B on a shared common-potential node. |
| [tests/](tests/) | Nine regression models: two well-formed (`test-ok-rl-circuit`, `test-ok-derivative-causality`) and seven deliberately malformed (`test-conflict-*`). The other three consistent models in the validation table are the two ontology modules and the exemplar, which live outside this directory. |
| [reasoner-report.md](reasoner-report.md) | HermiT output for every model and entailment test. |
| [build_models.py](scripts/build_models.py) | Generates the exemplar and the test models. |
| [validate.py](scripts/validate.py) | Resolves imports, runs HermiT, writes the report. |
| [dl_checks.py](scripts/dl_checks.py) | Structural OWL 2 DL checks (punning, non-simple properties). |

Namespaces: `https://w3id.org/bondgraph/core#` (`bg:`),
`https://w3id.org/bondgraph/biochem#` (`bgb:`) and `https://w3id.org/bondgraph/bfo#`
(`bgf:`). **All three are placeholders** — no w3id redirect has been registered, and
`dct:license` is deliberately unset.

## Design decisions

### Standalone core, alignment by annotation

The core imports nothing. Correspondences to external vocabularies are carried as
`skos:closeMatch` / `skos:relatedMatch` / `skos:editorialNote`, never as subsumption.
A mapping module can therefore be layered on without touching the axiomatisation, and
reasoning does not drag in an import closure.

Only IRIs that were resolved against a live service are asserted. The SBO terms used
(`SBO:0000176` biochemical reaction, `SBO:0000247` simple chemical, `SBO:0000303`
biochemical potential, `SBO:0000612` rate of reaction, `SBO:0000361` amount of an
entity pool, `SBO:0000355` conservation law, `SBO:0000147` thermodynamic temperature,
`SBO:0000259` voltage, `SBO:0000290` physical compartment, `SBO:0000655` transport
reaction, `SBO:0000001` rate law, `SBO:0000009` kinetic constant, `SBO:0000463`
standard biochemical potential, `SBO:0000167` biochemical or transport reaction,
`SBO:0000196` concentration of an entity pool) were each retrieved from EBI's OLS and
checked by label before being written in.

The Ontology of Physics for Biology is the obvious second alignment target but is not
served by OLS, so no OPB IRIs are asserted here — inventing them would have been
worse than leaving the hooks empty. Units are given as UCUM strings
(`bg:ucumUnit`) rather than QUDT IRIs for the same reason; a units mapping module is
the right place for those.

### Top-level partition

Six disjoint branches under `bg:BondGraphEntity`: `StructuralEntity` (bond graph,
element, port, bond), `Quantity`, `ConstitutiveRelation`, `EnergyDomain`, `Causality`,
`CausalForm`. The last three are classifiers whose extensions are closed by
`owl:oneOf` where the formalism fixes them (`Causality` = {effortOut, flowOut},
`CausalForm` = {integral, derivative}) and left open where extension is expected
(`EnergyDomain`).

The core itself makes no upper-ontology commitment: the partition above is what the
formalism needs, and a bond is awkward under a continuant/occurrent split. The BFO
commitment lives in a separate importable module instead — see below.

### Pinning to BFO

`bondgraph-bfo.ttl` imports the core, the biochemical module, IAO and RO, and adds
two layers. Neither core file is modified; a user who does not want the import closure
simply does not import the bridge.

**Layer 1 — what the constructs are.** Every `bg:BondGraphEntity` is an IAO
information content entity, hence a BFO generically dependent continuant. Bond graphs,
elements, bonds, ports, variables, parameters and constitutive relations are all
representations. `bg:hasComponent` and `bg:hasPort` become sub-properties of BFO
`has part`, which is transitive, so a port is entailed to be a part of the graph its
element belongs to. Both stay simple properties, so the core's qualified cardinality
axioms are untouched. Ports and causalities are annotated as having no physical
referent at all — they are artefacts of the notation.

Layer 1 alone is nearly vacuous: everything lands in one BFO branch. The work is in
layer 2.

**Layer 2 — what they are about.** The bridge introduces the physical side and links
it with IAO `is about`: compartments and reservoirs as material entities, species
pools as object aggregates, reactions and transport as processes, and the capacity to
store, dissipate or transduce energy as dispositions. Elements denote dispositions,
power bonds denote energy transfer processes, species components denote pools,
reaction components denote reaction processes, and junctions denote the single shared
quantity they enforce.

The distinction this buys is one bond graph practice assumes but cannot state: an
**effort** denotes a quality of an enduring thing, while a **flow** denotes a rate,
which in BFO is a *process profile* of an occurrent. Effort and flow are not two
species of one kind of property — they sit in different BFO branches. The reasoner
confirms both placements, and confirms that a rate process profile is not a
continuant.

Because information content entities and qualities are disjoint in BFO, asserting that
a model variable *is* the quality it denotes makes the ontology inconsistent. That is
the `conflict-variable-as-quality` test.

Dispositions are related to their processes with `owl:allValuesFrom`, not
`someValuesFrom`: a disposition need not ever be realised, so asserting a realising
process would be wrong.

**Version pinning.** `bfo.owl` resolves to the 2019-08-26 release, which declares
classes only and no object properties, so every relation comes from IAO
(2026-03-30) or RO (2026-09-04); the BFO classes arrive through the IAO release.
`bfo.owl` is deliberately not imported alongside, to avoid two axiomatisations of the
same IRIs. Note that current RO renames `inheres in` to `characteristic of`
(`RO_0000052`, functional) and `bearer of` to `has characteristic` (`RO_0000053`).
BFO 2020's `has process profile` has no counterpart in that closure, so
`bgf:processProfileOf` is declared locally and flagged for replacement.

**Domain coverage.** The reality layer is worked out for the chemical, electrical,
mechanical (translation and rotation), hydraulic and thermal domains. Each contributes
a bearer (`bgf:ConductingBody`, `bgf:MechanicalBody`, `bgf:FluidBody`,
`bgf:ThermalBody`, `bgf:SpeciesPool`), a process, the intensive properties borne by
the bearer, the extensive properties that accumulate, and the rate process profiles of
the process. Every domain-specific effort, flow, displacement and momentum class in
the core is pinned to one of them. The magnetic domain is not extended.

Two deliberate choices in that layer. The bearers are **not** pairwise disjoint: one
material entity routinely bears qualities in several domains at once -- a coil is a
conducting body and a thermal body -- and that overlap is exactly what a transformer or
gyrator represents. The qualities and rate profiles themselves **are** pairwise
disjoint, so asserting that one quality is both a force and an electric potential is
inconsistent. Separately, classification of processes by domain cuts across their
classification by energetic role (transfer, storage, dissipation, transduction): a
fluid flow through a resistance is both, so only the role grouping is declared
disjoint.

The OBO files are fetched on demand into `imports/` by `scripts/validate.py` rather
than vendored; `imports/` is gitignored.

### Instances are model variables, not quantity kinds

A `bg:Quantity` individual is "the chemical potential at port `p_A` of this model",
not the universal "chemical potential". The quantity kind is the individual's class
(`bg:ChemicalPotential`). This keeps `bg:parameterValue`, `bg:initialValue` and
`bg:unitCode` as straightforward functional data properties on the individual.

### Ports are first class

Elements have ports; bonds join exactly two ports. `bg:portOf` and `bg:attachedTo` are
functional, so a port belongs to one element and carries at most one bond — which is
what makes `bg:DanglingPort` (the external interface of a composite element) a
well-defined defined class. `bg:portIndex` orders the ports of elements whose
constitutive relation is not symmetric in them: transformers, gyrators, reaction
components.

The power sign convention is carried by `bg:hasPowerSource` and `bg:hasPowerSink`,
two disjoint functional sub-properties of `bg:hasEnd` — the half-arrow, as structure
rather than a diagram attribute.

### Where OWL stops

OWL has no arithmetic. Constitutive relations are carried as
`bg:constitutiveEquation` annotation strings on classes and on
`bg:ConstitutiveRelation` individuals, for a tool to parse or dereference, e.g.
`"v = kappa*(exp(A_f/(R*T)) - exp(A_r/(R*T)))"` on `bgb:ReactionComponent`. What the
logic does carry is the structure those relations presuppose: arity, attachment,
conjugacy, the tetrahedron-of-state relations (`bg:integralOf`), and causality.

### Causality is the logical payload

Causality assignment is purely combinatorial, so it is decidable, and it is where the
axiomatisation earns its keep. Two defined classes do the work:

`bg:EffortDeterminingPort ≡ PowerPort ⊓ ∃hasCausality.{effortOut}`
and `bg:FlowDeterminingPort ≡ PowerPort ⊓ ∃hasCausality.{flowOut}`.

Every `bg:PowerBond` then has *exactly one* end of each kind — asserted
unconditionally, because it holds of the formalism whether or not a modeller has drawn
the strokes. Element causality constraints are stated the same way:

- `Se`: one effort-determining port, zero flow-determining ones; `Sf` the mirror.
- `0`-junction: exactly one flow-determining port. `1`-junction: exactly one
  effort-determining port.
- `TF`: exactly one effort-determining port (through causality). `GY`: a general class
  inclusion forcing two if there is one (crossed causality).
- `C` and `I`: four general class inclusions conditioned on `bg:hasCausalForm`, giving
  the integral and derivative cases.
- `Re` (biochem): both ports flow-determining, fixed, because the exponential relation
  is not invertible port-wise. This is what forces integral causality on the species
  components around a reaction.

Two consequences, both verified on the test models. First, a reasoner *propagates* a
causal assignment: in the `Se — 1 — {R, I}` test, asserting nothing but the element
types and the integral causality of `I`, HermiT entails the causality of all five power
ports, including the resistor's. Second, a causality conflict is an **inconsistency**,
not a missing inference — two effort sources on a 0-junction, or a flow source bonded
to an inertia in integral causality, each force two distinct ports to be identical and
contradict the bond's cardinality.

### Models must declare their individuals distinct

Qualified cardinality restrictions cannot bite while the reasoner is free to merge two
ports. Every model emitted by [build_models.py](scripts/build_models.py) therefore carries an
`owl:AllDifferent` over all of its individuals. Without it the conflict tests all come
back consistent. Any tool writing instance data against this core has to do the same.

### What belongs in SHACL instead

Three constraints are deliberately absent from the OWL, because they are closed-world
integrity constraints rather than entailments:

- a bond's energy domain agreeing with its two ports' domains;
- a bond graph's element and bond lists being complete (which is why
  `bg:FullyCausalBondGraph` is satisfiable but never entailed — see the negative test
  in the report);
- sign-convention consistency of the signed sums at a junction.

## Validation

[reasoner-report.md](reasoner-report.md) records, with zero mismatches:

- 17 consistency checks — 8 models consistent as intended, 9 malformed models detected
  as inconsistent (two effort sources on a 0-junction; flow source into an integral-causality
  inertia; two species pools on one common-potential node; gyrator with a single causal
  stroke; one port with both causalities; causality on a signal port; a bond with three
  ends; a model variable asserted to be a BFO quality; one quality asserted to be both a
  force and an electric potential).
- No unsatisfiable classes in the core, the biochemical module, or the BFO bridge
  under the full IAO + RO import closure (up to 18,408 triples).
- 27 entailment checks — 20 expected entailments confirmed and 7 expected
  non-entailments confirmed, via HermiT's `--checkEntailment`.
- Structural OWL 2 DL checks: no punning, no undeclared IRIs, and the two non-simple
  properties (`bg:connectsElement`, `bg:bondedTo`, both defined by property chains)
  appear in no cardinality, functionality, disjointness or asymmetry axiom.

The DL check is targeted, not a full profile validation: the OWL API's `OWL2DLProfile`
needs a JDK and only a JRE was available. HermiT's clean run is corroborating evidence,
since it rejects non-simple properties in number restrictions outright.

To reproduce: `python scripts/build_models.py && python scripts/validate.py`
(needs `rdflib`, `owlready2` for its bundled HermiT, and a JVM).

## Known gaps

- Multiport storage fields (`C`- and `I`-fields) and multiport `R`-fields are not
  modelled; only one-port storage and one- and two-port dissipators.
- Bond activation (`bg:SignalBond`) is declared but no modulation semantics links a
  signal to the parameter it modulates — `bg:ModulatedElement` is currently defined
  only by the presence of an input signal port.
- Pseudo bond graphs (the non-power-conjugate temperature/heat-flow pair common in
  physiological thermal models) are excluded by `bg:thermalDomain`; they need their own
  explicitly-pseudo domain and a relaxed `bg:PowerBond` sibling.
- No SHACL shapes yet for the three constraints listed above.
- The magnetic domain (`bg:magneticDomain`, `bg:MagnetomotiveForce`,
  `bg:MagneticFluxRate`) has no reality-layer counterpart; the other six domains do.
- Force and linear displacement are modelled as plain qualities of a single body.
  Both are really two-place — a force is exerted by one body on another, a position is
  relative to a frame — so both are candidates for BFO `relational quality` once
  reference frames and two-body interactions are modelled.
- `bgf:processProfileOf` is a local stand-in for BFO 2020's `has process profile`,
  which is absent from the IAO/RO closure at the pinned versions.
- No reality-layer referent is offered for `bg:Transducer` beyond a transductive
  disposition, and none at all for `bg:Port` — deliberate, but worth revisiting if
  ports turn out to denote fiat boundaries of a system.
- Junction sign conventions are documented in annotations but carry no formal
  representation of which ends count positive.
