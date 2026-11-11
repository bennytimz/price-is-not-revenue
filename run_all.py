"""One command that rebuilds every number and chart from the data files in this folder.

    pip install pandas numpy statsmodels scipy
    python run_all.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for script, out in (("verify_data.py", None), ("analysis_confirmatory.py", "confirmatory_results.txt"), ("scenarios.py", "scenarios_results.txt"), ("build_dashboard.py", None)):
    print(f"--> {script}")
    r = subprocess.run([sys.executable, os.path.join(HERE, script)], capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        sys.exit(f"{script} failed")
    if out:
        open(os.path.join(HERE, out), "w").write(r.stdout)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "")
print("Done. Open dashboard.html.")
