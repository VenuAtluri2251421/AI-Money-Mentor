import subprocess
import sys

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'engine/tests/', '-v', '--tb=long'],
    capture_output=True,
    text=True,
    cwd=r'D:\AI advisor Backend'
)
output = result.stdout + result.stderr
with open(r'D:\AI advisor Backend\pytest_results.txt', 'w', encoding='utf-8') as f:
    f.write(output)
print("RETURN_CODE:", result.returncode)
print(output[-3000:])  # print last 3000 chars to console
