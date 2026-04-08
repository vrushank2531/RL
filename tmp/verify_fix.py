import sys
import os

# Add root to path so we can import server
sys.path.append(r"c:\Users\TANISHRAJ\Downloads\RL-main\RL-main")

from server.grader import calculate_reward

def test():
    print("Testing reward normalization...")
    
    # 1. Crash (previously 0.0)
    norm_crash, score_crash = calculate_reward(0, 3, True)
    print(f"Crash: normalized={norm_crash:.4f}, score={score_crash:.4f}")
    assert 0.0 < norm_crash < 1.0, f"Crash reward {norm_crash} out of range (0, 1)"
    
    # 2. Perfect Pass (previously 1.0)
    norm_pass, score_pass = calculate_reward(3, 3, False)
    print(f"Perfect Pass: normalized={norm_pass:.4f}, score={score_pass:.4f}")
    assert 0.0 < norm_pass < 1.0, f"Perfect Pass reward {norm_pass} out of range (0, 1)"
    
    # 3. Partial Pass
    norm_part, score_part = calculate_reward(1, 3, False)
    print(f"Partial Pass (1/3): normalized={norm_part:.4f}, score={score_part:.4f}")
    assert 0.0 < norm_part < 1.0, f"Partial Pass reward {norm_part} out of range (0, 1)"

    print("\nSUCCESS: All rewards are strictly within (0, 1)!")

if __name__ == "__main__":
    test()
