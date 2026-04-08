import os
import sys
import time
import json
import requests

BASE_URL = os.getenv("OPENENV_URL", "http://localhost:7860")
TASKS = ["syntax_fix", "logic_fix", "security_fix"]
MAX_STEPS = 5
REQUEST_TIMEOUT = 30

def make_request_with_retry(method, url, **kwargs):
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    try:
        res = requests.request(method, url, **kwargs)
        res.raise_for_status()
        return res
    except requests.exceptions.ConnectionError as e:
        sys.stderr.write(f"ConnectionError for {url}. Retrying in 3 seconds...\n")
        time.sleep(3)
        try:
            res = requests.request(method, url, **kwargs)
            res.raise_for_status()
            return res
        except Exception as retry_e:
            sys.stderr.write(f"Retry failed via ConnectionError: {retry_e}\n")
            raise retry_e
    except Exception as e:
        sys.stderr.write(f"Request failed: {e}\n")
        raise e

def generate_fix(task_id, buggy_code, step):
    fixed_code = buggy_code
    
    if task_id == "syntax_fix":
        lines = fixed_code.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("def ") and not line.rstrip().endswith(":"):
                lines[i] = line.rstrip() + ":"
            elif stripped.startswith("if ") and not line.rstrip().endswith(":"):
                lines[i] = line.rstrip() + ":"
            elif stripped.startswith("for ") and not line.rstrip().endswith(":"):
                lines[i] = line.rstrip() + ":"
            elif stripped.startswith("while ") and not line.rstrip().endswith(":"):
                lines[i] = line.rstrip() + ":"
        fixed_code = "\n".join(lines)
        
        # unbalanced parens/brackets
        if fixed_code.count('(') > fixed_code.count(')'):
            fixed_code += ")" * (fixed_code.count('(') - fixed_code.count(')'))
        if fixed_code.count('[') > fixed_code.count(']'):
            fixed_code += "]" * (fixed_code.count('[') - fixed_code.count(']'))
        if fixed_code.count('{') > fixed_code.count('}'):
            fixed_code += "}" * (fixed_code.count('{') - fixed_code.count('}'))
            
        if "return" not in fixed_code and "def " in fixed_code:
            fixed_code += "\n    return None"
            
    elif task_id == "logic_fix":
        lines = fixed_code.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("if ") and "=" in line and "==" not in line and "!=" not in line and ">=" not in line and "<=" not in line:
                lines[i] = line.replace("=", "==")
            elif "==" in line and step % 2 != 0:
                # Toggle logic back on odd steps to test variations
                lines[i] = line.replace("==", "=")
            elif ">" in line and not ">=" in line:
                lines[i] = line.replace(">", "<")
            elif "<" in line and not "<=" in line:
                lines[i] = line.replace("<", ">")
            elif "+" in line:
                lines[i] = line.replace("+", "-")
            elif "-" in line:
                lines[i] = line.replace("-", "+")
            elif "range(" in line:
                if "range(1," not in line.replace(" ", ""):
                    lines[i] = line.replace("range(", "range(1, ")
        fixed_code = "\n".join(lines)
        
    elif task_id == "security_fix":
        fixed_code = fixed_code.replace("eval(", "ast.literal_eval(")
        fixed_code = fixed_code.replace("exec(", "pass # ")
        fixed_code = fixed_code.replace("os.system(", "subprocess.run(")
        fixed_code = fixed_code.replace("shell=True", "shell=False")
        
        lines = fixed_code.split("\n")
        for i, line in enumerate(lines):
            # rudimentary string concat sql inject bypass
            if "+" in line and "SELECT" in line.upper():
                lines[i] = line.replace("+", ",")
            # strip hardcoded passwords
            if "password=" in line.replace(" ", "") and ("'" in line or '"' in line):
                lines[i] = line.split("password")[0] + "password = os.getenv('DB_PASS')  # sanitized"
        fixed_code = "\n".join(lines)
        
    return fixed_code

def run_episode(task_id):
    best_reward = 0.0
    steps_taken = 0
    print(f"[START] task={task_id}", flush=True)
    try:
        url = f"{BASE_URL}/reset"
        res = make_request_with_retry("POST", url, json={"task_id": task_id})
        obs = res.json()
        buggy_code = obs.get("buggy_code", "")
    except Exception as e:
        sys.stderr.write(f"Failed to reset task {task_id}: {e}\n")
        print(f"[END] task={task_id} score={best_reward} steps={steps_taken}", flush=True)
        return best_reward

    current_code = buggy_code
    for step_num in range(MAX_STEPS):
        steps_taken += 1
        fixed_code = generate_fix(task_id, current_code, step_num)
        action = {
            "fixed_code": fixed_code,
            "bug_explanation": f"Heuristic string manip fix applied at step {step_num}",
            "bug_type": task_id.replace("_fix", ""),
            "confidence": round(max(0.1, 0.9 - step_num * 0.1), 2)
        }
        
        try:
            url = f"{BASE_URL}/step"
            res = make_request_with_retry("POST", url, json={"action": action})
            data = res.json()
            reward_data = data.get("reward", {})
            if isinstance(reward_data, dict):
                reward = float(reward_data.get("grader_score", 0.0))
            else:
                try:
                    reward = float(reward_data)
                except:
                    reward = 0.0
            
            print(f"[STEP] step={step_num + 1} reward={reward}", flush=True)
            
            done = data.get("done", False)
            
            if reward > best_reward:
                best_reward = reward
                
            if done:
                break
                
            current_code = fixed_code
        except Exception as e:
            sys.stderr.write(f"Failed step {step_num} for task {task_id}: {e}\n")
            # Step failed: mark done=True, keep best_reward
            break

    print(f"[END] task={task_id} score={best_reward} steps={steps_taken}", flush=True)
    return best_reward


if __name__ == "__main__":
    try:
        print("Running CodeBugEnv baseline inference...")
        scores = {}
        total_score = 0.0
        
        for i, task_id in enumerate(TASKS):
            score = run_episode(task_id)
            scores[task_id] = round(score, 4)
            total_score += score
            print(f"Task {i+1}/3: {task_id} ... score: {scores[task_id]:.4f}")
            
        overall = round(total_score / len(TASKS), 4) if len(TASKS) > 0 else 0.0
        scores["overall"] = overall
        
        print("---")
        print("Final scores:")
        print(json.dumps(scores, indent=2))
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"Fatal unhandled exception: {e}\n")
        fallback_scores = {
            "syntax_fix": 0.0,
            "logic_fix": 0.0,
            "security_fix": 0.0,
            "overall": 0.0
        }
        print("---")
        print("Final scores:")
        print(json.dumps(fallback_scores, indent=2))
        sys.exit(0)
