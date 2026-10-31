"""Generate the exemplar bond graph model and the reasoner test cases as Turtle.

Each model is a standalone Turtle file that owl:imports the core (and the biochemical
module where needed).  Individuals are always declared pairwise distinct: without
owl:AllDifferent the qualified cardinality axioms in the core cannot bite, because the
reasoner stays free to merge two ports into one.
"""

from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD

BG = Namespace("https://w3id.org/bondgraph/core#")
BGB = Namespace("https://w3id.org/bondgraph/biochem#")
CORE = URIRef("https://w3id.org/bondgraph/core")
BIOCHEM = URIRef("https://w3id.org/bondgraph/biochem")

OUT = Path(__file__).resolve().parent.parent


def new_graph(iri, imports, title):
    g = Graph()
    ex = Namespace(iri + "#")
    g.bind("bg", BG)
    g.bind("bgb", BGB)
    g.bind("ex", ex)
    ont = URIRef(iri)
    g.add((ont, RDF.type, OWL.Ontology))
    for i in imports:
        g.add((ont, OWL.imports, i))
    g.add((ont, RDFS.label, Literal(title, lang="en")))
    return g, ex


def declare(g, node, cls):
    g.add((node, RDF.type, OWL.NamedIndividual))
    g.add((node, RDF.type, cls))
    return node


def all_different(g, individuals):
    node, coll = BNode(), BNode()
    g.add((node, RDF.type, OWL.AllDifferent))
    Collection(g, coll, list(dict.fromkeys(individuals)))
    g.add((node, OWL.distinctMembers, coll))


def power_port(g, ex, name, owner, index, effort_cls, flow_cls, domain, symbol):
    """Declare a power port together with its conjugate effort/flow pair."""
    p = declare(g, ex[name], BG.PowerPort)
    e = declare(g, ex["e_" + name], effort_cls)
    f = declare(g, ex["f_" + name], flow_cls)
    g.add((p, BG.portOf, owner))
    g.add((p, BG.portIndex, Literal(index, datatype=XSD.nonNegativeInteger)))
    g.add((p, BG.inEnergyDomain, domain))
    g.add((p, BG.hasEffort, e))
    g.add((p, BG.hasFlow, f))
    g.add((e, BG.symbol, Literal("e_" + symbol, datatype=XSD.string)))
    g.add((f, BG.symbol, Literal("f_" + symbol, datatype=XSD.string)))
    g.add((e, BG.conjugateTo, f))
    return p, e, f


def bond(g, ex, name, source_port, sink_port, domain):
    b = declare(g, ex[name], BG.PowerBond)
    g.add((b, BG.hasEnd, source_port))
    g.add((b, BG.hasEnd, sink_port))
    g.add((b, BG.hasPowerSource, source_port))
    g.add((b, BG.hasPowerSink, sink_port))
    g.add((b, BG.inEnergyDomain, domain))
    return b


# ------------------------------------------------------------------- exemplar
def build_reaction_chain():
    """A = B = C: two reversible elementary reactions sharing species B.

        Ce:A --b1--> Re:r1 --b2--> 0:J_B --b3--> Re:r2 --b4--> Ce:C
                                     |
                                     b5
                                     v
                                   Ce:B
    """
    iri = "https://w3id.org/bondgraph/examples/reaction-chain"
    g, ex = new_graph(iri, [CORE, BIOCHEM],
                      "Exemplar: reversible reaction chain A = B = C")
    model = declare(g, ex["abcChain"], BGB.ReactionNetwork)
    D = BG.chemicalDomain
    ports, inds = {}, [model]

    for sp, amount in (("A", 1.0e-3), ("B", 1.0e-4), ("C", 1.0e-5)):
        ce = declare(g, ex["Ce_" + sp], BGB.SpeciesComponent)
        q = declare(g, ex["q_" + sp], BG.MolarAmount)
        k = declare(g, ex["K_" + sp], BGB.SpeciesThermodynamicConstant)
        g.add((ce, RDFS.label, Literal(f"species pool {sp}", lang="en")))
        g.add((ce, BG.hasCausalForm, BG.integralCausality))
        g.add((ce, BG.hasGeneralizedDisplacement, q))
        g.add((ce, BG.hasParameter, k))
        g.add((ce, BG.inEnergyDomain, D))
        g.add((q, BG.initialValue, Literal(amount, datatype=XSD.double)))
        g.add((q, BG.unitCode, Literal("mol", datatype=XSD.string)))
        g.add((q, BG.symbol, Literal("q_" + sp, datatype=XSD.string)))
        g.add((k, BG.parameterValue, Literal(1.0e3, datatype=XSD.double)))
        g.add((k, BG.unitCode, Literal("/mol", datatype=XSD.string)))
        g.add((model, BG.hasElement, ce))
        p, e, f = power_port(g, ex, "p_" + sp, ce, 0, BG.ChemicalPotential,
                             BG.MolarFlowRate, D, "mu_" + sp)
        g.add((q, BG.integralOf, f))
        ports[sp] = p
        inds += [ce, q, k, p, e, f]

    for rx, kappa in (("r1", 2.0), ("r2", 0.5)):
        re_ = declare(g, ex["Re_" + rx], BGB.ReactionComponent)
        kp = declare(g, ex["kappa_" + rx], BGB.ReactionRateConstant)
        g.add((re_, BG.hasParameter, kp))
        g.add((re_, BG.inEnergyDomain, D))
        g.add((kp, BG.parameterValue, Literal(kappa, datatype=XSD.double)))
        g.add((kp, BG.unitCode, Literal("mol/s", datatype=XSD.string)))
        g.add((model, BG.hasElement, re_))
        inds += [re_, kp]
        for i in (1, 2):
            nm = f"p_{rx}_{i}"
            p, e, f = power_port(g, ex, nm, re_, i - 1, BG.ChemicalPotential,
                                 BG.MolarFlowRate, D, f"{rx}_{i}")
            ports[nm] = p
            inds += [p, e, f]

    jb = declare(g, ex["J_B"], BG.ZeroJunction)
    g.add((jb, RDFS.label, Literal("common-potential node for species B", lang="en")))
    g.add((jb, BG.inEnergyDomain, D))
    g.add((model, BG.hasElement, jb))
    con = declare(g, ex["c_J_B"], BG.CommonEffortConstraint)
    g.add((con, BG.constitutiveEquation,
           Literal("mu_B = mu_r1_2 = mu_r2_1 ; v_r1 - v_r2 - dq_B/dt = 0")))
    g.add((jb, BG.hasConstitutiveRelation, con))
    g.add((jb, BG.hasCommonEffort, ex["e_p_B"]))
    inds += [jb, con]
    for i in (1, 2, 3):
        nm = f"p_JB_{i}"
        p, e, f = power_port(g, ex, nm, jb, i - 1, BG.ChemicalPotential,
                             BG.MolarFlowRate, D, f"JB_{i}")
        ports[nm] = p
        inds += [p, e, f]

    bonds = [bond(g, ex, "b1", ports["A"], ports["p_r1_1"], D),
             bond(g, ex, "b2", ports["p_r1_2"], ports["p_JB_1"], D),
             bond(g, ex, "b3", ports["p_JB_2"], ports["p_r2_1"], D),
             bond(g, ex, "b4", ports["p_r2_2"], ports["C"], D),
             bond(g, ex, "b5", ports["p_JB_3"], ports["B"], D)]
    for x in bonds:
        g.add((model, BG.hasBond, x))
    inds += bonds

    all_different(g, inds)
    return "example-reaction-chain.ttl", g


# ------------------------------------------------------------------ test cases
def t_ok_rl_circuit():
    """Se -- 1-junction -- {R, I}: a consistent model using the core alone."""
    g, ex = new_graph("https://w3id.org/bondgraph/tests/ok-rl-circuit", [CORE],
                      "Consistent: Se -- 1-junction -- {R, I}")
    D = BG.electricalDomain
    se = declare(g, ex["Se_v"], BG.EffortSource)
    r = declare(g, ex["R_coil"], BG.Resistor)
    ind = declare(g, ex["I_coil"], BG.InertialStorage)
    j = declare(g, ex["J1"], BG.OneJunction)
    rp = declare(g, ex["R_param"], BG.Resistance)
    ip = declare(g, ex["I_param"], BG.Inertance)
    lam = declare(g, ex["lambda_coil"], BG.FluxLinkage)
    cf = declare(g, ex["c_J1"], BG.CommonFlowConstraint)
    g.add((ind, BG.hasCausalForm, BG.integralCausality))
    g.add((r, BG.hasParameter, rp))
    g.add((ind, BG.hasParameter, ip))
    g.add((ind, BG.hasGeneralizedMomentum, lam))
    g.add((j, BG.hasConstitutiveRelation, cf))

    pse, e0, f0 = power_port(g, ex, "p_se", se, 0, BG.Voltage, BG.ElectricCurrent, D, "se")
    pr, e1, f1 = power_port(g, ex, "p_r", r, 0, BG.Voltage, BG.ElectricCurrent, D, "r")
    pi, e2, f2 = power_port(g, ex, "p_i", ind, 0, BG.Voltage, BG.ElectricCurrent, D, "i")
    g.add((lam, BG.integralOf, e2))
    js = []
    inds = [se, r, ind, j, rp, ip, lam, cf, pse, e0, f0, pr, e1, f1, pi, e2, f2]
    for i in (1, 2, 3):
        p, e, f = power_port(g, ex, f"p_j{i}", j, i - 1, BG.Voltage, BG.ElectricCurrent, D, f"j{i}")
        js.append(p)
        inds += [p, e, f]
    g.add((j, BG.hasCommonFlow, f0))
    inds += [bond(g, ex, "b1", pse, js[0], D),
             bond(g, ex, "b2", js[1], pr, D),
             bond(g, ex, "b3", js[2], pi, D)]
    all_different(g, inds)
    return "test-ok-rl-circuit.ttl", g


def t_ok_derivative_causality():
    g, ex = new_graph("https://w3id.org/bondgraph/tests/ok-derivative-causality", [CORE],
                      "Consistent: a model holding a C element in derivative causality")
    model = declare(g, ex["m"], BG.BondGraph)
    c = declare(g, ex["C1"], BG.CapacitiveStorage)
    cp = declare(g, ex["C_param"], BG.Capacitance)
    q = declare(g, ex["q_c"], BG.ElectricCharge)
    g.add((c, BG.hasCausalForm, BG.derivativeCausality))
    g.add((c, BG.hasParameter, cp))
    g.add((c, BG.hasGeneralizedDisplacement, q))
    g.add((model, BG.hasElement, c))
    p, e, f = power_port(g, ex, "p_c", c, 0, BG.Voltage, BG.ElectricCurrent,
                         BG.electricalDomain, "c")
    g.add((q, BG.integralOf, f))
    all_different(g, [model, c, cp, q, p, e, f])
    return "test-ok-derivative-causality.ttl", g


def t_conflict_two_effort_sources():
    g, ex = new_graph("https://w3id.org/bondgraph/tests/conflict-two-effort-sources", [CORE],
                      "Causality conflict: two effort sources on one 0-junction")
    D = BG.electricalDomain
    j = declare(g, ex["J"], BG.ZeroJunction)
    con = declare(g, ex["c_J"], BG.CommonEffortConstraint)
    g.add((j, BG.hasConstitutiveRelation, con))
    inds = [j, con]
    for k in (1, 2):
        s = declare(g, ex[f"Se{k}"], BG.EffortSource)
        ps, e, f = power_port(g, ex, f"p_s{k}", s, 0, BG.Voltage, BG.ElectricCurrent, D, f"s{k}")
        pj, ej, fj = power_port(g, ex, f"p_j{k}", j, k - 1, BG.Voltage, BG.ElectricCurrent, D, f"j{k}")
        inds += [s, ps, e, f, pj, ej, fj, bond(g, ex, f"b{k}", ps, pj, D)]
    all_different(g, inds)
    return "test-conflict-two-effort-sources.ttl", g


def t_conflict_sf_into_inertia():
    g, ex = new_graph("https://w3id.org/bondgraph/tests/conflict-sf-into-i", [CORE],
                      "Causality conflict: flow source bonded to an inertia in integral causality")
    D = BG.mechanicalTranslationDomain
    sf = declare(g, ex["Sf_v"], BG.FlowSource)
    ind = declare(g, ex["I_mass"], BG.InertialStorage)
    ip = declare(g, ex["I_param"], BG.Inertance)
    mom = declare(g, ex["p_mom"], BG.LinearMomentum)
    g.add((ind, BG.hasCausalForm, BG.integralCausality))
    g.add((ind, BG.hasParameter, ip))
    g.add((ind, BG.hasGeneralizedMomentum, mom))
    p1, e1, f1 = power_port(g, ex, "p_sf", sf, 0, BG.Force, BG.LinearVelocity, D, "sf")
    p2, e2, f2 = power_port(g, ex, "p_i", ind, 0, BG.Force, BG.LinearVelocity, D, "i")
    g.add((mom, BG.integralOf, e2))
    all_different(g, [sf, ind, ip, mom, p1, e1, f1, p2, e2, f2,
                      bond(g, ex, "b1", p1, p2, D)])
    return "test-conflict-sf-into-i.ttl", g


def t_conflict_two_species_on_node():
    g, ex = new_graph("https://w3id.org/bondgraph/tests/conflict-two-species", [CORE, BIOCHEM],
                      "Causality conflict: two Ce components in integral causality "
                      "on one common-potential node")
    D = BG.chemicalDomain
    j = declare(g, ex["J"], BG.ZeroJunction)
    con = declare(g, ex["c_J"], BG.CommonEffortConstraint)
    g.add((j, BG.hasConstitutiveRelation, con))
    inds = [j, con]
    for k, sp in enumerate(("X", "Y"), start=1):
        ce = declare(g, ex["Ce_" + sp], BGB.SpeciesComponent)
        q = declare(g, ex["q_" + sp], BG.MolarAmount)
        kk = declare(g, ex["K_" + sp], BGB.SpeciesThermodynamicConstant)
        g.add((ce, BG.hasCausalForm, BG.integralCausality))
        g.add((ce, BG.hasGeneralizedDisplacement, q))
        g.add((ce, BG.hasParameter, kk))
        p, e, f = power_port(g, ex, "p_" + sp, ce, 0, BG.ChemicalPotential,
                             BG.MolarFlowRate, D, sp)
        g.add((q, BG.integralOf, f))
        pj, ej, fj = power_port(g, ex, f"p_j{k}", j, k - 1, BG.ChemicalPotential,
                                BG.MolarFlowRate, D, f"j{k}")
        inds += [ce, q, kk, p, e, f, pj, ej, fj, bond(g, ex, f"b{k}", p, pj, D)]
    all_different(g, inds)
    return "test-conflict-two-species.ttl", g


def t_conflict_gyrator_causality():
    g, ex = new_graph("https://w3id.org/bondgraph/tests/conflict-gyrator-causality", [CORE],
                      "Causality conflict: gyrator with exactly one effort-determining port")
    gy = declare(g, ex["GY"], BG.Gyrator)
    m = declare(g, ex["r_param"], BG.GyratorModulus)
    g.add((gy, BG.hasParameter, m))
    p1, e1, f1 = power_port(g, ex, "p_1", gy, 0, BG.Torque, BG.AngularVelocity,
                            BG.mechanicalRotationDomain, "1")
    p2, e2, f2 = power_port(g, ex, "p_2", gy, 1, BG.Voltage, BG.ElectricCurrent,
                            BG.electricalDomain, "2")
    g.add((p1, BG.hasCausality, BG.effortOut))
    g.add((p2, BG.hasCausality, BG.flowOut))
    all_different(g, [gy, m, p1, e1, f1, p2, e2, f2])
    return "test-conflict-gyrator-causality.ttl", g


def t_conflict_double_causality():
    g, ex = new_graph("https://w3id.org/bondgraph/tests/conflict-double-causality", [CORE],
                      "Malformed model: one port assigned both causalities")
    r = declare(g, ex["R1"], BG.Resistor)
    rp = declare(g, ex["R_param"], BG.Resistance)
    g.add((r, BG.hasParameter, rp))
    p, e, f = power_port(g, ex, "p_r", r, 0, BG.Voltage, BG.ElectricCurrent,
                         BG.electricalDomain, "r")
    g.add((p, BG.hasCausality, BG.effortOut))
    g.add((p, BG.hasCausality, BG.flowOut))
    all_different(g, [r, rp, p, e, f])
    return "test-conflict-double-causality.ttl", g


def t_conflict_signal_causality():
    g, ex = new_graph("https://w3id.org/bondgraph/tests/conflict-signal-causality", [CORE],
                      "Malformed model: causality assigned to a signal port")
    mr = declare(g, ex["MR1"], BG.ModulatedResistor)
    rp = declare(g, ex["R_param"], BG.Resistance)
    g.add((mr, BG.hasParameter, rp))
    sp = declare(g, ex["p_sig"], BG.InputSignalPort)
    g.add((sp, BG.portOf, mr))
    g.add((sp, BG.hasCausality, BG.effortOut))
    p, e, f = power_port(g, ex, "p_r", mr, 0, BG.Voltage, BG.ElectricCurrent,
                         BG.electricalDomain, "r")
    all_different(g, [mr, rp, sp, p, e, f])
    return "test-conflict-signal-causality.ttl", g


def t_conflict_bond_three_ends():
    g, ex = new_graph("https://w3id.org/bondgraph/tests/conflict-bond-three-ends", [CORE],
                      "Malformed model: a bond with three ends")
    D = BG.electricalDomain
    j = declare(g, ex["J"], BG.ZeroJunction)
    con = declare(g, ex["c_J"], BG.CommonEffortConstraint)
    g.add((j, BG.hasConstitutiveRelation, con))
    b = declare(g, ex["b1"], BG.PowerBond)
    g.add((b, BG.inEnergyDomain, D))
    inds = [j, con, b]
    for i in (1, 2, 3):
        p, e, f = power_port(g, ex, f"p_j{i}", j, i - 1, BG.Voltage, BG.ElectricCurrent, D, f"j{i}")
        g.add((b, BG.hasEnd, p))
        inds += [p, e, f]
    all_different(g, inds)
    return "test-conflict-bond-three-ends.ttl", g


BUILDERS = [build_reaction_chain, t_ok_rl_circuit, t_ok_derivative_causality,
            t_conflict_two_effort_sources, t_conflict_sf_into_inertia,
            t_conflict_two_species_on_node, t_conflict_gyrator_causality,
            t_conflict_double_causality, t_conflict_signal_causality,
            t_conflict_bond_three_ends]

if __name__ == "__main__":
    (OUT / "tests").mkdir(exist_ok=True)
    for fn in BUILDERS:
        name, g = fn()
        target = OUT / name if name.startswith("example") else OUT / "tests" / name
        g.serialize(destination=str(target), format="turtle")
        print(f"{target.relative_to(OUT)}: {len(g)} triples")
