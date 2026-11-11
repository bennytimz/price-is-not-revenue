"""One command that rebuilds every number and chart from the data files in this folder.

    pip install -r requirements.txt
    python run_all.py

DefiLlama raw files are not in the repository (DefiLlama's terms; PREREGISTRATION.md Amendment 8b). If they are
missing, this first pulls them from DefiLlama's free API (no key) with pull_defillama_intents.py. Everything else
is read from the committed files.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFILLAMA = ("raw_defillama_intents.json", "raw_defillama_intents_fees.json", "raw_defillama_intents_revenue.json")

steps = []
if not all(os.path.exists(os.path.join(HERE, f)) for f in DEFILLAMA):
    steps.append((["pull_defillama_intents.py"], None))
steps += [(["verify_data.py"], None), (["analysis_confirmatory.py"], "confirmatory_results.txt"), (["scenarios.py"], "scenarios_results.txt"),
          (["analysis_extension.py"], "extension_results.txt"), (["verify_data.py", "--extension"], None), (["build_dashboard.py"], None)]
for args, out in steps:
    print(f"--> {' '.join(args)}")
    r = subprocess.run([sys.executable, os.path.join(HERE, args[0])] + args[1:], capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        sys.exit(f"{args[0]} failed")
    if out:
        open(os.path.join(HERE, out), "w").write(r.stdout)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "")
print("Done. Open dashboard.html.")
