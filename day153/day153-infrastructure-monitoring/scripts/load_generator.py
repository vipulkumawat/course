"""Load generator for testing"""
import time
import random
import multiprocessing

def cpu_intensive_work(duration):
    """CPU intensive task"""
    end_time = time.time() + duration
    while time.time() < end_time:
        _ = sum(i*i for i in range(100000))
        time.sleep(0.01)

def generate_load(duration=60):
    """Generate sustained load"""
    print(f"Generating load for {duration} seconds...")
    
    processes = []
    for i in range(4):
        p = multiprocessing.Process(target=cpu_intensive_work, args=(duration,))
        p.start()
        processes.append(p)
        print(f"Started load process {i+1}/4")
    
    for p in processes:
        p.join()
    
    print("Load generation completed")

if __name__ == '__main__':
    generate_load()
