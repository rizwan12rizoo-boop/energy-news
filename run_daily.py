# Runs the daily robot: collect -> label -> report.
#   Real news:      python run_daily.py
#   Practice mode:  python run_daily.py practice
import runpy
import sys

practice = len(sys.argv) > 1 and sys.argv[1] == "practice"
steps = [("step1_collect_news.py", ["practice"] if practice else []),
         ("step2_ai_label.py", []),
         ("step3_make_report.py", [])]

for script, args in steps:
    print("\n" + "=" * 70 + f"\n RUNNING {script}\n" + "=" * 70)
    sys.argv = [script] + args
    runpy.run_path(script, run_name="__main__")
print("\nDone! Open reports/latest.html to see today's brief.")
