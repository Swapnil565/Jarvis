import sys, os
# Ensure project package root is importable
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
package_root = os.path.join(repo_root, 'Jarvis3.0')
sys.path.insert(0, package_root)

from celery_tasks import run_all_agents

res = run_all_agents.delay()
print('Dispatched task id:', res.id)
