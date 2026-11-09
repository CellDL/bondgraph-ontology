"""Emit RDF/XML, JSON-LD and N-Triples for each ontology module into dist/.

The hand-authored Turtle under src/ stays canonical and is what a Turtle request
resolves to: it carries the comments that explain the axioms, and reserialising would
throw them away. The files written here exist so that a client asking for RDF/XML or
JSON-LD is given that syntax rather than Turtle under a different media type, which
is what the w3id reviewer objected to.

Each generated file is parsed back and checked isomorphic against its source, so a
serialiser that silently drops structure cannot pass unnoticed -- rdflib's
`pretty-xml` does exactly that to RDF collections, which is why `xml` is used.

Usage:  python scripts/build_serialisations.py
"""

import sys
from pathlib import Path

from rdflib import Graph
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# module name -> hand-authored Turtle source
MODULES = {
    "bondgraph-core": ROOT / "src/bondgraph-core.ttl",
    "bondgraph-bfo": ROOT / "src/bondgraph-bfo.ttl",
    "bondgraph-biochem": ROOT / "src/domains/bondgraph-biochem.ttl",
    "bondgraph-hydraulic": ROOT / "src/domains/bondgraph-hydraulic.ttl",
    "bondgraph-thermal": ROOT / "src/domains/bondgraph-thermal.ttl",
}

# file extension -> rdflib serializer name. 'xml', never 'pretty-xml'.
FORMATS = {"rdf": "xml", "jsonld": "json-ld", "nt": "nt"}


def main():
    DIST.mkdir(exist_ok=True)
    failures = 0
    for name, src in sorted(MODULES.items()):
        if not src.exists():
            print(f"MISSING SOURCE {src}")
            failures += 1
            continue
        g = Graph()
        g.parse(str(src), format="turtle")
        for ext, fmt in FORMATS.items():
            target = DIST / f"{name}.{ext}"
            g.serialize(destination=str(target), format=fmt)
            back = Graph()
            back.parse(str(target), format=fmt)
            ok = isomorphic(g, back)
            failures += 0 if ok else 1
            print(f"{target.relative_to(ROOT)}: {len(back)}/{len(g)} triples "
                  f"{'isomorphic' if ok else 'NOT ISOMORPHIC'}")
    print(f"\n{'all serialisations round-trip' if not failures else f'{failures} problem(s)'}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
