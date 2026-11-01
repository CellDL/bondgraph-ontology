"""Reason over the bond graph ontology with HermiT and write a report.

Resolves owl:imports against local files, merges each model with its import closure
into a single RDF/XML document, then runs HermiT for

  * ontology consistency            (-k)
  * unsatisfiable classes           (-U)
  * entailment of named conclusions (--premise/--conclusion --checkEntailment)

Usage:  python scripts/validate.py
"""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dl_checks
import jdk4py
import owlready2
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
JAVA = str(jdk4py.JAVA)
HERMIT = str(Path(owlready2.__file__).parent / "hermit" / "HermiT.jar")

BG = Namespace("https://w3id.org/bondgraph/core#")
BGB = Namespace("https://w3id.org/bondgraph/biochem#")

IRI_TO_FILE = {
    "https://w3id.org/bondgraph/core": ROOT / "src/bondgraph-core.ttl",
    "https://w3id.org/bondgraph/biochem": ROOT / "src/domains/bondgraph-biochem.ttl",
}

NOISE = "Picked up JAVA_TOOL_OPTIONS"


def hermit(*args, timeout=1800):
    r = subprocess.run([JAVA, "-Xmx4g", "-cp", HERMIT,
                        "org.semanticweb.HermiT.cli.CommandLine", *args],
                       capture_output=True, text=True, timeout=timeout)
    text = "\n".join(l for l in (r.stdout + r.stderr).splitlines()
                     if not l.strip().startswith(NOISE))
    return r.returncode, text.strip()


def merge(path, seen=None, graph=None):
    """Load a Turtle file and recursively inline its local owl:imports."""
    graph = Graph() if graph is None else graph
    seen = set() if seen is None else seen
    g = Graph()
    g.parse(str(path), format="turtle")
    for ont in set(g.subjects(RDF.type, OWL.Ontology)):
        for imp in g.objects(ont, OWL.imports):
            key = str(imp)
            if key in IRI_TO_FILE and key not in seen:
                seen.add(key)
                merge(IRI_TO_FILE[key], seen, graph)
    graph += g
    return graph


def flatten(graph, iri):
    """Collapse several ontology headers into one, so OWL API sees a single ontology."""
    out = Graph()
    headers = set(graph.subjects(RDF.type, OWL.Ontology))
    for s, p, o in graph:
        if s in headers:
            continue
        out.add((s, p, o))
    root = URIRef(iri)
    out.add((root, RDF.type, OWL.Ontology))
    return out


def write_owl(graph, name):
    BUILD.mkdir(exist_ok=True)
    target = BUILD / name
    graph.serialize(destination=str(target), format="xml")
    return target


def prepare(path, tag):
    g = flatten(merge(path), f"https://w3id.org/bondgraph/merged/{tag}")
    return write_owl(g, f"{tag}.owl"), len(g)


def conclusion(tag, triples, prefixes=(("bg", BG), ("bgb", BGB))):
    g = Graph()
    for p, ns in prefixes:
        g.bind(p, ns)
    g.add((URIRef(f"https://w3id.org/bondgraph/conclusions/{tag}"), RDF.type, OWL.Ontology))
    for t in triples:
        g.add(t)
    return write_owl(g, f"conclusion-{tag}.owl")


EX = Namespace("https://w3id.org/bondgraph/examples/reaction-chain#")
RL = Namespace("https://w3id.org/bondgraph/tests/ok-rl-circuit#")
DC = Namespace("https://w3id.org/bondgraph/tests/ok-derivative-causality#")

# (model file, tag, expected consistency)
MODELS = [
    (ROOT / "src/bondgraph-core.ttl", "core", True),
    (ROOT / "src/domains/bondgraph-biochem.ttl", "biochem", True),
    (ROOT / "examples/reaction-chain.ttl", "example-reaction-chain", True),
    (ROOT / "tests/test-ok-rl-circuit.ttl", "ok-rl-circuit", True),
    (ROOT / "tests/test-ok-derivative-causality.ttl", "ok-derivative-causality", True),
    (ROOT / "tests/test-conflict-two-effort-sources.ttl", "conflict-two-effort-sources", False),
    (ROOT / "tests/test-conflict-sf-into-i.ttl", "conflict-sf-into-i", False),
    (ROOT / "tests/test-conflict-two-species.ttl", "conflict-two-species", False),
    (ROOT / "tests/test-conflict-gyrator-causality.ttl", "conflict-gyrator-causality", False),
    (ROOT / "tests/test-conflict-double-causality.ttl", "conflict-double-causality", False),
    (ROOT / "tests/test-conflict-signal-causality.ttl", "conflict-signal-causality", False),
    (ROOT / "tests/test-conflict-bond-three-ends.ttl", "conflict-bond-three-ends", False),
]

# (premise tag, label, conclusion triples, expected entailment)
ENTAILMENTS = [
    ("example-reaction-chain", "Re port 1 of r1 is flow-determining",
     [(EX["p_r1_1"], RDF.type, BG.FlowDeterminingPort)], True),
    ("example-reaction-chain", "the 0-junction port facing r1 is effort-determining",
     [(EX["p_JB_1"], RDF.type, BG.EffortDeterminingPort)], True),
    ("example-reaction-chain", "the port of species pool A is effort-determining",
     [(EX["p_A"], RDF.type, BG.EffortDeterminingPort)], True),
    ("example-reaction-chain", "the junction on B is a non-degenerate junction",
     [(EX["J_B"], RDF.type, BG.NonDegenerateJunction)], True),
    ("example-reaction-chain", "bond b1 connects species pool A",
     [(EX["b1"], BG.connectsElement, EX["Ce_A"])], True),
    ("example-reaction-chain", "Ce:A and Re:r1 are bonded, in both directions",
     [(EX["Ce_A"], BG.bondedTo, EX["Re_r1"]), (EX["Re_r1"], BG.bondedTo, EX["Ce_A"])], True),
    ("example-reaction-chain", "the chain is NOT a model with derivative causality",
     [(EX["abcChain"], RDF.type, BG.ModelWithDerivativeCausality)], False),
    ("example-reaction-chain", "the chain is NOT provably fully causal (open world)",
     [(EX["abcChain"], RDF.type, BG.FullyCausalBondGraph)], False),
    ("example-reaction-chain", "the chain is NOT an open reaction network",
     [(EX["abcChain"], RDF.type, BGB.OpenReactionNetwork)], False),
    ("ok-rl-circuit", "the source port is effort-determining",
     [(RL["p_se"], RDF.type, BG.EffortDeterminingPort)], True),
    ("ok-rl-circuit", "the inertia port is flow-determining",
     [(RL["p_i"], RDF.type, BG.FlowDeterminingPort)], True),
    ("ok-rl-circuit", "the junction port facing the inertia is effort-determining",
     [(RL["p_j3"], RDF.type, BG.EffortDeterminingPort)], True),
    ("ok-rl-circuit", "the resistor port is effort-determining (full assignment propagated)",
     [(RL["p_r"], RDF.type, BG.EffortDeterminingPort)], True),
    ("ok-rl-circuit", "the resistor is classified as a one-port element",
     [(RL["R_coil"], RDF.type, BG.OnePortElement)], True),
    ("ok-derivative-causality", "the model is classified as having derivative causality",
     [(DC["m"], RDF.type, BG.ModelWithDerivativeCausality)], True),
]


def main():
    lines, failures = [], 0
    lines.append("# HermiT reasoning report\n")
    lines.append(f"Reasoner: HermiT (bundled with Owlready2 {owlready2.VERSION}); "
                 f"JVM: jdk4py {jdk4py.__version__ if hasattr(jdk4py, '__version__') else ''}\n")

    lines.append("\n## Consistency and class satisfiability\n")
    lines.append("| model | triples (with import closure) | expected | HermiT |")
    lines.append("|---|---|---|---|")
    prepared = {}
    for path, tag, expect_consistent in MODELS:
        owl_path, n = prepare(path, tag)
        prepared[tag] = owl_path
        rc, out = hermit("-k", str(owl_path))
        consistent = "is satisfiable" in out and "not satisfiable" not in out
        ok = consistent == expect_consistent
        failures += 0 if ok else 1
        verdict = "consistent" if consistent else "INCONSISTENT"
        lines.append(f"| `{tag}` | {n} | {'consistent' if expect_consistent else 'inconsistent'} "
                     f"| {verdict} {'(ok)' if ok else '(MISMATCH)'} |")

    lines.append("\n### Unsatisfiable classes\n")
    for tag in ("core", "biochem"):
        rc, out = hermit("-U", str(prepared[tag]))
        body = [l.strip() for l in out.splitlines() if l.strip().startswith(("owl:", "bg", "http"))]
        extra = [b for b in body if b != "owl:Nothing"]
        failures += 0 if not extra else 1
        lines.append(f"- `{tag}`: {'none' if not extra else 'FOUND ' + ', '.join(extra)}")

    lines.append("\n## Entailment tests\n")
    lines.append("| premise | conclusion | expected | HermiT |")
    lines.append("|---|---|---|---|")
    for i, (tag, label, triples, expect) in enumerate(ENTAILMENTS):
        conc = conclusion(f"{tag}-{i}", triples)
        rc, out = hermit("--premise=" + prepared[tag].as_uri(), "--conclusion=" + conc.as_uri(),
                         "--checkEntailment")
        low = out.strip().splitlines()[-1].strip().lower() if out.strip() else ""
        entailed = {"true": True, "false": False}.get(low)
        ok = entailed is expect
        failures += 0 if ok else 1
        got = {True: "entailed", False: "not entailed", None: f"UNPARSED: {out[:80]}"}[entailed]
        lines.append(f"| `{tag}` | {label} | {'entailed' if expect else 'not entailed'} "
                     f"| {got} {'(ok)' if ok else '(MISMATCH)'} |")

    dl_text, dl_ok = dl_checks.report()
    lines.append("\n## OWL 2 DL structural checks\n")
    lines.append("Targeted checks on punning and on non-simple properties in "
                 "simple-only axioms; see `scripts/dl_checks.py` for scope.\n")
    lines.append(dl_text)
    failures += 0 if dl_ok else 1

    lines.append(f"\n**Mismatches: {failures}**\n")
    report = "\n".join(lines)
    (ROOT / "reasoner-report.md").write_text(report)
    print(report)
    return failures


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
