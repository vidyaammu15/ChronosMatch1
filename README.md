# ChronosMatch
## Zero-Copy High-Frequency Trading Engine

ChronosMatch is a low-latency High-Frequency Trading (HFT) engine designed to process and match a large number of trading orders efficiently. The project focuses on zero-copy communication, fast order matching, C-level optimization, performance monitoring, trade persistence, resiliency, and real-time dashboard visualization.

---

# Week-Wise Project Development

## Week 1 — Memory Mapping & Market Firehose

### Memory Mapping

The first week focused on creating an efficient communication mechanism for transferring trading orders between processes.

### Completed Work

- Implemented an mmap-backed SPSC (Single-Producer Single-Consumer) ring buffer.
- Used Python `mmap` for shared-memory communication.
- Used `struct` for fixed-size binary order storage.
- Implemented order serialization and deserialization.
- Implemented ring-buffer read and write operations.
- Added empty and full buffer handling.
- Implemented ring-buffer wraparound.
- Added batched writes for high-throughput order ingestion.
- Maintained FIFO ordering.

### Market Firehose

Implemented an asynchronous Market Firehose to simulate continuous market-order flow.

### Completed Work

- Implemented asynchronous order generation using `asyncio`.
- Generated simulated BUY and SELL orders.
- Connected the Market Firehose with the mmap IPC bus.
- Generated and transferred 100,000 mock trading orders.
- Verified FIFO ordering from order ID 1 to 100,000.
- Successfully consumed all generated orders.
- Measured producer and consumer throughput.

### Week 1 Status

**COMPLETED ✅**

---

# Week 2 — Matching Engine & Latency Dashboard

### Limit Order Book

The second week focused on implementing the core order-book and trade-matching logic.

### Completed Work

- Implemented the Limit Order Book.
- Added BUY and SELL order handling.
- Implemented Price-Time Priority.
- Higher-priced BUY orders receive priority.
- Lower-priced SELL orders receive priority.
- Maintained time priority for orders at the same price.
- Implemented full order fills.
- Implemented partial order fills.
- Implemented multiple order matching.
- Implemented order cancellation.
- Added handling for orders that cannot be matched.

### Matching Engine

- Integrated the Limit Order Book with the matching pipeline.
- Processed incoming orders.
- Compared BUY and SELL prices.
- Applied Price-Time Priority.
- Generated trade objects when orders matched.
- Supported full and partial executions.
- Verified matching behavior.

### Latency Dashboard

Implemented a raw terminal monitoring dashboard using Python `curses`.

### Completed Work

- Implemented the `curses` terminal interface.
- Added Order Book monitoring.
- Added Bid/Ask information.
- Added latency information.
- Added engine status information.
- Added real-time monitoring.

### Week 2 Status

**COMPLETED ✅**

---

# Mid-Project Review — IPC & Engine Verification

The Mid-Project Review focused on verifying the core communication and matching functionality developed during the first two weeks.

### IPC Verification

- Verified mmap-based shared-memory communication.
- Verified SPSC ring-buffer operations.
- Verified producer-to-consumer order transfer.
- Verified FIFO ordering.
- Tested empty-buffer conditions.
- Tested full-buffer conditions.
- Tested wraparound behavior.
- Tested batch-write operations.

### Engine Verification

- Verified BUY and SELL matching.
- Verified Price-Time Priority.
- Verified full fills.
- Verified partial fills.
- Verified multiple matches.
- Verified order cancellation.
- Verified generated trade objects.
- Verified the matching pipeline.

### Mid-Project Review Status

**COMPLETED ✅**

---

# Week 3 — C-Level Optimization & Metrics Tracking

The third week focused on improving the performance of the matching engine and measuring its execution speed.

### Cython / C-Level Optimization

- Implemented the optimized Cython matching engine.
- Optimized the critical matching loop.
- Added C-level order structures.
- Added Cython compiler optimization directives.
- Configured compiler optimization through `setup.py`.
- Optimized binary heap indexing.
- Added direct pointer-based memory access.
- Reduced Python-level overhead.
- Used `nogil` for the performance-critical matching section.
- Preserved Price-Time Priority.
- Maintained the standard Python matching-engine fallback.

### Metrics Tracking

Implemented high-resolution performance tracking using:

```python
time.perf_counter_ns()
