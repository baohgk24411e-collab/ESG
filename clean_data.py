import os
import glob
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_dir = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(base_dir, "output_results")
cache_dir = os.path.join(base_dir, "data", "incident_cache")

print("Cleaning old results and cache...")

# Clear output_results/
if os.path.exists(results_dir):
    for f in glob.glob(os.path.join(results_dir, "*.*")):
        try:
            os.remove(f)
            print(f"  Removed: {os.path.basename(f)}")
        except Exception as e:
            print(f"  Could not remove {f}: {e}")

# Clear incident_cache/
if os.path.exists(cache_dir):
    for f in glob.glob(os.path.join(cache_dir, "*.*")):
        try:
            os.remove(f)
        except Exception:
            pass
    print("  Cleared incident cache.")

# Clear root output files
for root_file in ["output_results.json", "output_results.html", "dashboard.html"]:
    rf = os.path.join(base_dir, root_file)
    if os.path.exists(rf):
        try:
            os.remove(rf)
            print(f"  Removed: {root_file}")
        except Exception:
            pass

print("✨ All old batch data cleared! Ready for fresh run.")
