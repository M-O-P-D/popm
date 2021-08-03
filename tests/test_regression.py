import subprocess
import pandas as pd

ACTIVE = "active_psus.csv"
DEPTIMES = "deployment_times.csv"


def test_regression():

  result = subprocess.run(["python", "batch_simple.py", "scenario/regression.json"], stderr=subprocess.PIPE)

  assert result.returncode == 0, "Script returned error code: %d" % result.returncode
  assert len(result.stderr) == 0, "Script generated errors:\n%s" % result.stderr

  baseline_active = pd.read_csv(f"tests/{ACTIVE}")
  baseline_deptimes = pd.read_csv(f"tests/{DEPTIMES}")

  active = pd.read_csv(f"model-output/regression/{ACTIVE}")
  deptimes = pd.read_csv(f"model-output/regression/{DEPTIMES}")

  assert active.equals(baseline_active)
  assert deptimes.equals(baseline_deptimes)

if __name__ == "__main__":
  test_regression()
