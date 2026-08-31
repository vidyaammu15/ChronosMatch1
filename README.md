# ChronosMatch
## Zero-Copy High-Frequency Trading Engine

ChronosMatch is a low-latency High-Frequency Trading (HFT) engine designed to efficiently generate, transfer, process, match, and monitor a high volume of trading orders.

The project focuses on memory-mapped Inter-Process Communication (IPC), an SPSC ring buffer, a Limit Order Book, Price-Time Priority matching, Cython-based optimization, nanosecond-level performance measurement, asynchronous trade persistence, resiliency, Whale Order detection, and real-time monitoring.

---

# Project Development Progress

The ChronosMatch project was developed progressively according to the planned weekly roadmap.

---

## Week 1 — Memory Mapping & Market Firehose

### Memory-Mapped IPC

Implemented the low-level communication layer using shared memory.

### Completed Work

- Implemented an mmap-backed SPSC (Single-Producer Single-Consumer) ring buffer.
- Used Python `mmap` for shared-memory communication.
- Used `struct` for fixed-size binary order storage.
- Implemented order serialization and deserialization.
- Implemented ring-buffer read and write operations.
- Implemented empty-buffer handling.
- Implemented full-buffer handling.
- Implemented ring-buffer wraparound.
- Added batched writes for high-throughput order ingestion.
- Maintained FIFO ordering of orders.

### Market Firehose

Implemented an asynchronous market-order generator to simulate high-volume order flow.

### Completed Work

- Implemented asynchronous Market Firehose using `asyncio`.
- Generated simulated BUY and SELL orders.
- Connected the Market Firehose with the mmap IPC layer.
- Generated and transferred 100,000 mock trading orders.
- Verified FIFO ordering from order ID 1 through 100,000.
- Successfully consumed all generated orders.
- Measured producer throughput.
- Measured consumer throughput.

### Week 1 Status

**COMPLETED**

---

# Week 2 — Matching Engine & Latency Dashboard

## Limit Order Book

Implemented the core order-book functionality required for trade matching.

### Completed Work

- Implemented the Limit Order Book.
- Added BUY order handling.
- Added SELL order handling.
- Implemented Price-Time Priority.
- Higher-priced BUY orders receive priority.
- Lower-priced SELL orders receive priority.
- Orders at the same price are processed according to arrival time.
- Implemented full fills.
- Implemented partial fills.
- Implemented multiple order matches.
- Implemented order cancellation.
- Added handling for orders that cannot be matched.

## Matching Engine

Integrated the Limit Order Book with the order-processing pipeline.

### Completed Work

- Processed incoming orders through the matching engine.
- Compared BUY and SELL prices.
- Applied Price-Time Priority.
- Generated trade objects when orders matched.
- Supported full and partial executions.
- Supported multiple matches.
- Integrated the engine with the existing processing pipeline.

## Latency Dashboard

Implemented a raw terminal dashboard using Python `curses`.

### Completed Work

- Implemented raw `curses` terminal interface.
- Added Order Book display.
- Added Bid/Ask information.
- Added latency information.
- Added real-time engine information.

### Week 2 Status

**COMPLETED**

---

# Mid-Project Review — IPC & Engine Verification

The Mid-Project Review focused on verifying the core IPC and matching-engine implementation before moving to performance optimization.

## IPC Verification

### Completed Work

- Verified mmap-based shared-memory communication.
- Verified SPSC ring-buffer operations.
- Verified producer-to-consumer order transfer.
- Verified FIFO ordering.
- Verified empty-buffer handling.
- Verified full-buffer handling.
- Verified wraparound behavior.
- Verified batch-write operations.

## Matching Engine Verification

### Completed Work

- Verified BUY and SELL matching.
- Verified Price-Time Priority.
- Verified full fills.
- Verified partial fills.
- Verified multiple matches.
- Verified order cancellation.
- Verified generated trade objects.
- Verified the matching pipeline.

### Mid-Project Review Status

**COMPLETED**

---

# Week 3 — C-Level Optimization & Metrics

The third phase focused on improving the performance of the matching engine and introducing high-resolution performance monitoring.

## Cython / C-Level Optimization

### Completed Work

- Implemented the optimized Cython matching engine.
- Optimized the critical matching loop.
- Added C-level order structures.
- Added Cython compiler optimization directives.
- Configured C-compiler optimization through `setup.py`.
- Optimized binary heap indexing.
- Added direct pointer-based memory access.
- Reduced Python-level overhead in the matching path.
- Used `nogil` for the performance-critical matching section.
- Preserved Price-Time Priority.
- Preserved the standard Python matching-engine fallback.

## Metrics Tracking

Implemented high-resolution performance measurement using:

```python
time.perf_counter_ns()


# Week 4 — Resiliency & Refine/Polish

The fourth phase focused on improving system reliability, asynchronous trade persistence, failure handling, Whale Order detection, and dashboard refinement.

## 4.1 Trade Persistence & Resiliency

### Completed Work

- Implemented SQLite-based trade persistence.
- Added `TradeLedger` for storing matched trades.
- Added individual trade saving.
- Added batch trade saving.
- Added trade retrieval and counting.
- Added validation for invalid trade records.
- Implemented `TradePersistenceWorker` for background processing.
- Added asynchronous trade submission using a queue.
- Added batch trade submission.
- Added pending queue tracking.
- Added graceful worker shutdown.
- Ensured pending trades are processed before shutdown.
- Added SQLite error handling.
- Added worker-level exception handling.
- Ensured database failures do not stop the matching engine.
- Added tests for database and worker failure scenarios.

### Trade Persistence Flow

```text
Matching Engine
       |
       v
Matched Trade
       |
       v
Persistence Queue
       |
       v
Background Worker
       |
       v
SQLite Trade Ledger
