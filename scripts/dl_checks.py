"""Targeted OWL 2 DL structural checks on the bond graph ontology files.

This is not a full OWL 2 DL profile validation -- that needs the OWL API's
OWL2DLProfile, which needs a JDK, and only a JRE is available here.  It checks the
restrictions that actually bear on this ontology:

  1. Illegal punning: an IRI declared under two incompatible entity types.
  2. Non-simple object properties (those with a property chain or transitivity, or
     with a non-simple sub-property or inverse) used where OWL 2 DL forbids them:
     cardinality restrictions, Self restrictions, functionality, inverse
     functionality, irreflexivity, asymmetry, property disjointness.
  3. Undeclared IRIs used in class or property position.

HermiT itself rejects case 2 outright, so a clean consistency run is corroborating
evidence; this script localises any problem to a specific axiom.
"""

from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

ROOT = Path(__file__).resolve().parent.parent

CARDINALITY = {OWL.cardinality, OWL.minCardinality, OWL.maxCardinality,
               OWL.qualifiedCardinality, OWL.minQualifiedCardinality,
               OWL.maxQualifiedCardinality, OWL.hasSelf}

SIMPLE_ONLY_TYPES = {OWL.FunctionalProperty, OWL.InverseFunctionalProperty,
                     OWL.IrreflexiveProperty, OWL.AsymmetricProperty}

ENTITY_TYPES = [OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
                OWL.AnnotationProperty, OWL.NamedIndividual, OWL.Ontology]


def load(paths):
    g = Graph()
    for p in paths:
        g.parse(str(p), format="xml" if Path(p).suffix == ".owl" else "turtle")
    return g


def declared_entities(paths):
    """IRIs declared as OWL entities in files parsed for declarations only."""
    g = load(paths)
    return {s for s in g.subjects(RDF.type, None)
            if isinstance(s, URIRef) and {t for t in g.objects(s, RDF.type)} & set(ENTITY_TYPES)}


def punning(g):
    bad = []
    for s in set(g.subjects(RDF.type, None)):
        if not isinstance(s, URIRef):
            continue
        types = {t for t in g.objects(s, RDF.type) if t in ENTITY_TYPES}
        incompatible = [
            ({OWL.Class, OWL.ObjectProperty}, "class and object property"),
            ({OWL.Class, OWL.DatatypeProperty}, "class and data property"),
            ({OWL.Class, OWL.AnnotationProperty}, "class and annotation property"),
            ({OWL.ObjectProperty, OWL.DatatypeProperty}, "object and data property"),
            ({OWL.ObjectProperty, OWL.AnnotationProperty}, "object and annotation property"),
            ({OWL.DatatypeProperty, OWL.AnnotationProperty}, "data and annotation property"),
        ]
        for combo, why in incompatible:
            if combo <= types:
                bad.append((s, why))
    return bad


def non_simple(g):
    """Fixpoint over chains, transitivity, sub-property and inverse propagation."""
    ns = set(g.subjects(OWL.propertyChainAxiom, None))
    ns |= set(g.subjects(RDF.type, OWL.TransitiveProperty))
    changed = True
    while changed:
        changed = False
        for sub, _, sup in g.triples((None, RDFS.subPropertyOf, None)):
            if sub in ns and sup not in ns:
                ns.add(sup)
                changed = True
        for a, _, b in g.triples((None, OWL.inverseOf, None)):
            for x, y in ((a, b), (b, a)):
                if x in ns and y not in ns:
                    ns.add(y)
                    changed = True
    return ns


def simple_only_violations(g, ns):
    bad = []
    for r in set(g.subjects(OWL.onProperty, None)):
        prop = next(g.objects(r, OWL.onProperty), None)
        if prop in ns and any(g.value(r, c) is not None for c in CARDINALITY):
            kind = next(c for c in CARDINALITY if g.value(r, c) is not None)
            bad.append((prop, f"used in {kind.split('#')[1]} restriction"))
    for t in SIMPLE_ONLY_TYPES:
        for p in g.subjects(RDF.type, t):
            if p in ns:
                bad.append((p, f"declared {t.split('#')[1]}"))
    for a, _, b in g.triples((None, OWL.propertyDisjointWith, None)):
        for p in (a, b):
            if p in ns:
                bad.append((p, "used in propertyDisjointWith"))
    return bad


def undeclared(g, imported=frozenset()):
    declared = {s for s in g.subjects(RDF.type, None)
                if isinstance(s, URIRef) and {t for t in g.objects(s, RDF.type)} & set(ENTITY_TYPES)}
    declared |= set(imported)
    external = ("http://www.w3.org/", "http://purl.org/dc/terms/",
                "http://biomodels.net/SBO/")
    used_class, used_prop = set(), set()
    for p in (RDFS.subClassOf, OWL.equivalentClass, OWL.complementOf,
              OWL.someValuesFrom, OWL.allValuesFrom, OWL.onClass, OWL.disjointWith):
        for _, _, o in g.triples((None, p, None)):
            if isinstance(o, URIRef):
                used_class.add(o)
        for s, _, _ in g.triples((None, p, None)):
            if isinstance(s, URIRef):
                used_class.add(s)
    for p in (OWL.onProperty, RDFS.subPropertyOf, OWL.inverseOf):
        for s, _, o in g.triples((None, p, None)):
            for x in (s, o):
                if isinstance(x, URIRef):
                    used_prop.add(x)
    miss = sorted(str(x) for x in (used_class | used_prop) - declared
                  if not str(x).startswith(external))
    return miss


def section(paths, label, import_paths=()):
    g = load(paths)
    imported = declared_entities(import_paths) if import_paths else frozenset()
    ns = non_simple(g)
    pun = punning(g)
    viol = simple_only_violations(g, ns)
    miss = undeclared(g, imported)
    out = [f"### {label}\n",
           f"- triples: {len(g)}",
           f"- non-simple object properties (chain or transitive): "
           + (", ".join(sorted(p.split('#')[-1] for p in ns)) or "none"),
           f"- illegal punning: " + ("none" if not pun else
                                     "; ".join(f"{s.split('#')[-1]} ({w})" for s, w in pun)),
           f"- non-simple property in a simple-only axiom: "
           + ("none" if not viol else
              "; ".join(f"{p.split('#')[-1]} {w}" for p, w in viol)),
           f"- IRIs resolved against the import closure: "
           + (f"{len(imported)} declared in imports" if imported else "no imports loaded"),
           f"- undeclared IRIs in class/property position: "
           + ("none" if not miss else ", ".join(m.split('#')[-1] for m in miss)),
           ]
    ok = not (pun or viol or miss)
    return "\n".join(out), ok


def report():
    core = [ROOT / "src/bondgraph-core.ttl"]
    both = core + [ROOT / "src/domains/bondgraph-biochem.ttl"]
    bridge = both + [ROOT / "src/bondgraph-bfo.ttl"]
    domains = [ROOT / "src/bondgraph-core.ttl",
               ROOT / "src/domains/bondgraph-hydraulic.ttl",
               ROOT / "src/domains/bondgraph-thermal.ttl"]
    sections, oks = [], []
    for paths, label in ((core, "`bondgraph-core.ttl`"),
                         (both, "`bondgraph-core.ttl` + `bondgraph-biochem.ttl`"),
                         (bridge, "the two modules + `bondgraph-bfo.ttl`"),
                         (domains, "core + the hydraulic and thermal domain modules")):
        if not all(q.exists() for q in paths):
            continue
        imports = [q for q in (ROOT / "imports/iao.owl", ROOT / "imports/ro.owl")
                   if q.exists()] if "bondgraph-bfo.ttl" in str(paths[-1]) else []
        text, ok = section(paths, label, imports)
        sections.append(text)
        oks.append(ok)
    return "\n\n".join(sections), all(oks)


if __name__ == "__main__":
    text, ok = report()
    print(text)
    print("\nPASS" if ok else "\nFAIL")
