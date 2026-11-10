#===============================================================================

from pathlib import Path
import re
import shutil
import subprocess
import urllib.request

#===============================================================================

import jdk4py

#===============================================================================

JAVA = str(jdk4py.JAVA)

WIDCO_VERSION = "1.4.26"

#===============================================================================

WEBVOWL_IFRAME = '<iframe src="webvowl/index.html"></iframe>'
WEBVOWL_IN_NEW_WINDOW = f'<h2>Visualization</h2>{WEBVOWL_IFRAME}<a href="webvowl/index.html" target="_window">WebVOWL visualization</a> (opens in a new window)</a>'

def webvowl_in_new_window(index_file: Path) -> bool:
    if not index_file.is_file():
        return False
    html = index_file.read_text(encoding='utf-8')
    if WEBVOWL_IN_NEW_WINDOW in html:
        return False
    html = html.replace(WEBVOWL_IFRAME, WEBVOWL_IN_NEW_WINDOW)
    index_file.write_text(html, encoding='utf-8')
    return True

#===============================================================================

def webvowl_hide_sidebar_sections(output_path: Path):
    webvowl_index = output_path / 'webvowl' / 'index.html'
    if not webvowl_index.is_file():
        return False
    html = webvowl_index.read_text(encoding='utf-8')
    sections = ['Description', 'Metadata', 'Statistics']
    for section in sections:
        match = rf'(<h3 .*class="accordion-trigger)( |")(.*">{section}</h3>\n.*<div .*class="accordion-container)([ |"])'
        html = re.sub(match, r'\1 hidden\2\3 hidden\4', html)
    webvowl_index.write_text(html, encoding='utf-8')

#===============================================================================

def generate_widoco_docs(onto_path: str, out_dir: str):
    # Download Widoco if not already present
    widoco_path = Path(out_dir) / 'widoco'
    widoco_path.mkdir(parents=True, exist_ok=True)
    widoco_jar = widoco_path / 'widoco.jar'
    if not widoco_jar.exists():
        url = f"https://github.com/dgarijo/Widoco/releases/download/v{WIDCO_VERSION}/widoco-{WIDCO_VERSION}-jar-with-dependencies_JDK-17.jar"
        print(f"Downloading Widoco {WIDCO_VERSION}...")
        urllib.request.urlretrieve(url, widoco_jar)

    output_path = Path(out_dir) / 'docs'
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Run Widoco
    cmd = [
        JAVA, '-jar', str(widoco_jar),
        '-ontFile', onto_path,
        '-outFolder', str(output_path),
        '-oops',
        '-getOntologyMetadata',
        '-webVowl',
        '-rewriteAll',
        '-uniteSections',
        '-lang', 'en',
        '-includeAnnotationProperties',
        '-noPlaceHolderText',
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Documentation generated in {output_path}")

        # Add a link to open WebVOWL in a new window
        for name in ("index.html", "index-en.html"):
            webvowl_in_new_window(output_path / name)

        # Copy index-en.html to index.html if it exists
        index_en = output_path / 'index-en.html'
        index_default = output_path / 'index.html'
        if index_en.exists():
            shutil.copy(index_en, index_default)

        # Hide sections in WebVOWL's sidebar as they duplicate information
        # on the main HTML page
        webvowl_hide_sidebar_sections(output_path)

    except subprocess.CalledProcessError as e:
        print("Widoco execution failed:")
        print(e)

#===============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        exit(f'Usage: {sys.argv[0]} ONTOLOGY.ttl OUTPUT_DIR')

    generate_widoco_docs(sys.argv[1], sys.argv[2])

#===============================================================================
