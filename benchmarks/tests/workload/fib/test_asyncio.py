"""
Test asyncio implementation of Fibonacci.
Tests async/await overhead and task scheduling.
"""
import time
import sys
import asyncio

async def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return await fibonacci(n-1) + await fibonacci(n-2)

async def main_async():
    # Create tasks for all numbers
    tasks = [
        asyncio.create_task(fibonacci(n))
        for n in range(32)
    ]
    
    # Wait for all tasks
    await asyncio.gather(*tasks)

def main():
    start = time.time()
    
    # Run async code
    asyncio.run(main_async())
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
