# Core Performance Concepts in Python Interpreters

## Introduction

## 1. Thread Affinity and Biased Reference Counting

### Concept
Thread affinity refers to how objects "stick" to their creating threads. Biased reference counting optimizes for the common case where objects are mostly accessed by one thread.

### Visual Representation
```
Traditional Reference Counting:
Thread1    Memory     Thread2
   │     [refcount]     │
   │         ↕          │
   ├─────────┼──────────┤
   │    inc  │    inc   │
   │    dec  │    dec   │
   └─────────┼──────────┘

Biased Reference Counting:
Thread1    Memory     Thread2
   │     [refcount]     │
   │      [bias]        │
   ├───fast─┐           │
   │    inc │           │
   │    dec │           │
   │        └──slow─────┤
   │                    │
```

### What We're Testing
```python
def test_thread_affinity():
    """
    Create objects with varying bias ratios:
    
    High Bias (0.9):
    Thread1 ──► [Obj1] ◄── 90% access
           └─► [Obj2] ◄── 10% access by other threads
    
    Low Bias (0.1):
    Thread1 ──► [Obj1] ◄── 10% access
           └─► [Obj2] ◄── 90% access by other threads
    """
```


## 2. False Sharing

### Concept
False sharing occurs when threads access different variables that happen to be on the same cache line, causing unnecessary cache coherency traffic.

### Visual Representation
```
Cache Line (64 bytes):
Without Padding:
┌────────────┬────────────┬────────────┐
│ Thread1    │ Thread2    │ Thread3    │
│ Counter    │ Counter    │ Counter    │
└────────────┴────────────┴────────────┘
                 ↓
     Cache line bounces between CPUs

With Padding:
┌────────────┐ ┌────────────┐ ┌────────────┐
│ Thread1    │ │ Thread2    │ │ Thread3    │
│ Counter    │ │ Counter    │ │ Counter    │
│ [Padding]  │ │ [Padding]  │ │ [Padding]  │
└────────────┘ └────────────┘ └────────────┘
     ↓              ↓              ↓
Each counter on separate cache line
```

### What We're Testing
```python
# Bad: False sharing
class SharedCounters:
    def __init__(self):
        self.counter1 = 0  # Same cache line
        self.counter2 = 0  # as counter1

# Good: Padded to avoid false sharing
class PaddedCounters:
    def __init__(self):
        self.counter1 = 0
        self._pad1 = bytes(64)  # Force new cache line
        self.counter2 = 0
```

## Performance Implications

### Thread Affinity Impact
```
Access Patterns vs Performance:
Local Access:  ▁▁▂▂░░░░░░  (fast)
Cross-Thread:  ▅▅▆▆▇▇██░░  (slow)
Cache Miss:    ██████████  (slowest)
```

### Specialization Cost
```
Operation Costs:
Specialized Int Add:   ▁▁░░░░░░░░
Generic Add:          ▅▅▅▅░░░░░░
Type Check + Add:     ██████░░░░
Full Dynamic Add:     ██████████
```

### False Sharing Impact
```
Cache Line Behavior:
No Sharing:      ▁▁▂▂░░░░░░  (optimal)
False Sharing:   ██████████  (heavy traffic)
True Sharing:    ▅▅▅▅▅▅░░░░  (necessary traffic)
```

## Key Metrics to Collect

1. **Thread Affinity**
   - Object migration frequency
   - Bias switch counts
   - Cache coherency traffic

2. **Specialization**
   - Type check frequency
   - Despecialization events
   - Code path frequency

3. **Memory Access**
   - Cache miss rates
   - Memory barrier counts
   - Cache line bouncing
