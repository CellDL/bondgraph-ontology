"""Check every published serialisation says the same thing as its authored source.

This replaces the isomorphism check that build_serialisations.py used to perform, and
it is NOT the same test, for a reason worth recording.

Widoco converts through the OWL API, which normalises as it goes. Measured on the core
module: nine two-member `owl:AllDisjointClasses` axioms come back as plain
`owl:disjointWith` triples, and about forty declaration triples are added for
anonymous class expressions. The published graph is therefore *not* isomorphic to the
authored one, and never will be — 1402 triples in, 1397 out for RDF/XML, 1381 for
JSON-LD, 1484 for N-Triples. An isomorphism check would fail on correct output.

What must hold is that the two are logically equivalent, which is decidable and cheap:
HermiT confirms entailment in both directions in well under a second per module. That
is a stronger guarantee than byte equality and a weaker one than isomorphism, and it
is the right property: a consumer of the RDF/XML must be able to draw exactly the
conclusions a consumer of the Turtle can.

Usage:  python scripts/check_published.py
"""

import subprocess
import sys
from pathlib import Path

import jdk4py
import owlready2
from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
TMP = ROOT / "build" / "equiv"
JAVA = str(jdk4py.JAVA)
HERMIT = str(Path(owlready2.__file__).parent / "hermit" / "HermiT.jar")

SOURCES = {
    "core": ROOT / "src/bondgraph-core.ttl",
    "bfo": ROOT / "src/bondgraph-bfo.ttl",
    "biochem": ROOT / "src/domains/bondgraph-biochem.ttl",
    "hydraulic": ROOT / "src/domains/bondgraph-hydraulic.ttl",
    "thermal": ROOT / "src/domains/bondgraph-thermal.ttl",
}
PUBLISHED = {"ontology.rdf": "xml", "ontology.jsonld": "json-ld", "ontology.nt": "nt",
             "ontology.ttl": "turtle"}


DECL_TYPES = (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
              OWL.AnnotationProperty, OWL.NamedIndividual)


def declarations():
    """Entity declarations harvested from every authored module, for re-injection."""
    g = Graph()
    for path in SOURCES.values():
        if path.exists():
            g.parse(str(path), format="turtle")
    return g


def load(src, fmt, decls):
    """Parse, drop owl:imports, and restore the declarations the imports supplied.

    owl:imports are stripped from both sides: the question is whether the published
    file says what the authored module says, not what its import closure entails, and
    leaving the imports in makes HermiT try to fetch IAO and RO over the network.

    Declarations for the entities those imports used to supply are then injected back.
    Without them the OWL API cannot tell whether, say, bg:hasPort is an object or a
    data property, so a qualified-cardinality restriction mentioning it is never
    parsed as a class expression and quietly vanishes. The visible symptom is a module
    failing to entail *itself* -- which is how this was found.
    """
    g = Graph()
    g.parse(str(src), format=fmt)
    for t in list(g.triples((None, OWL.imports, None))):
        g.remove(t)
    for iri in {x for t in g for x in t if isinstance(x, URIRef)}:
        if (iri, RDF.type, None) not in g:
            for ty in decls.objects(iri, RDF.type):
                if ty in DECL_TYPES:
                    g.add((iri, RDF.type, ty))
    return g


def harmonise(a, b):
    """Give both graphs the same entity declarations before comparing them.

    A declaration is bookkeeping, not a claim about the world, and HermiT will not
    derive one: a conclusion containing `obo:BFO_0000015 a owl:Class` is reported as
    not entailed unless the premise declares it too. The OWL API adds such
    declarations for imported entities when it writes the published file -- thirteen
    of them in the BFO bridge module, enough to make it look inequivalent to itself.

    Only rdf:type declarations are copied. Everything else the OWL API introduces
    stays in the comparison and has to be earned: the fourteenth triple by which the
    published bridge module differs from its source is
    `bgf:ExtensiveProperty owl:disjointWith bgf:IntensiveProperty`, the normalisation
    of an authored two-member owl:AllDisjointClasses, and that one is a real axiom
    which the source genuinely entails.
    """
    for src, dst in ((a, b), (b, a)):
        for s, _, o in src.triples((None, RDF.type, None)):
            if o in DECL_TYPES and isinstance(s, URIRef) and (s, RDF.type, o) not in dst:
                dst.add((s, RDF.type, o))


def write(g, target):
    g.serialize(destination=str(target), format="xml")
    return len(g)


def entailed(premise, conclusion):
    r = subprocess.run(
        [JAVA, "-Xmx4g", "-cp", HERMIT, "org.semanticweb.HermiT.cli.CommandLine",
         "--premise=" + Path(premise).resolve().as_uri(),
         "--conclusion=" + Path(conclusion).resolve().as_uri(),
         "--checkEntailment"],
        capture_output=True, text=True, timeout=1800)
    lines = [l for l in (r.stdout + r.stderr).splitlines()
             if l.strip() and "JAVA_TOOL_OPTIONS" not in l]
    return (lines[-1].strip().lower() == "true") if lines else None


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    decls = declarations()
    failures = 0
    print(f"{'module/file':34s} {'triples':>8}  equivalent to source")
    for short, src in SOURCES.items():
        if not src.exists():
            print(f"{short:34s} MISSING SOURCE")
            failures += 1
            continue
        source = load(src, "turtle", decls)
        n_src = len(source)
        ref = TMP / f"{short}-source.owl"
        write(source, ref)
        # Baseline: the source must entail itself. If it does not, the checker has a
        # blind spot and any verdict it gives below is meaningless -- say so rather
        # than blaming the published file.
        if not entailed(ref, ref):
            print(f"{short:34s} {n_src:>8}  CHECK BROKEN: source does not entail itself")
            failures += 1
            continue
        for name, fmt in PUBLISHED.items():
            pub = SITE / short / name
            if not pub.exists():
                print(f"{short + '/' + name:34s} {'-':>8}  NOT PUBLISHED")
                failures += 1
                continue
            cand = TMP / f"{short}-{name}.owl"
            try:
                published = load(pub, fmt, decls)
            except Exception as e:
                print(f"{short + '/' + name:34s} {'-':>8}  PARSE FAILED: {type(e).__name__}")
                failures += 1
                continue
            n = len(published)
            this_ref = TMP / f"{short}-{name}-ref.owl"
            paired = load(src, "turtle", decls)
            harmonise(paired, published)
            write(paired, this_ref)
            write(published, cand)
            fwd = entailed(this_ref, cand)
            rev = entailed(cand, this_ref)
            ok = bool(fwd) and bool(rev)
            failures += 0 if ok else 1
            note = "yes" if ok else f"NO (source|=pub {fwd}, pub|=source {rev})"
            print(f"{short + '/' + name:34s} {n:>8}  {note}"
                  f"{'' if n == n_src else f'   [source {n_src}, normalised by Widoco]'}")
    print(f"\n{'all published serialisations are logically equivalent to their source' if not failures else f'{failures} problem(s)'}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
