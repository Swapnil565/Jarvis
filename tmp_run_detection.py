import sys, json
proj=r'c:\Users\swapn\OneDrive\Documents\Jarvis\Jarvis_Backend\JARVIS3.0_BACKEND\Jarvis3.0'
sys.path.insert(0, proj)
from simple_jarvis_db import jarvis_db
from agents.pattern_detector import pattern_detector

uid = 99999
print('creating sample events for user', uid)
# create 20 days with alternating workouts and tasks
for i in range(20):
    day = f'2025-10-{i+1:02d}T12:00:00'
    # workout every other day
    if i % 2 == 0:
        jarvis_db.create_event(uid, 'physical', 'workout', 'energized', {'workout_type':'full_body','duration':30})
    # completed task counts vary
    completed = (i % 3 == 0)
    jarvis_db.create_event(uid, 'mental', 'task', None, {'title':f'task {i}','completed': completed})

print('running detection...')
import asyncio
res = asyncio.get_event_loop().run_until_complete(pattern_detector.detect_patterns(uid))
print('detected patterns:', json.dumps(res, indent=2))
print('stored patterns count:', len(jarvis_db.get_patterns(uid, active_only=False)))
