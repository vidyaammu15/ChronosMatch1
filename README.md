# ChronosMatch — Zero-Copy High-Frequency Trading Engine

ChronosMatch is a low-latency High-Frequency Trading (HFT) engine designed to process and match a large volume of trading orders with minimal communication and data-copying overhead.

The project combines memory-mapped Inter-Process Communication (IPC), a Limit Order Book, Cython-based C-level optimization, asynchronous market-data generation, nanosecond-resolution performance monitoring, asynchronous trade persistence, and a real-time monitoring dashboard.

---

## 1. Project Overview

High-Frequency Trading systems need to process a large number of orders within very small time intervals. In such systems, unnecessary data copying, serialization, memory allocation, and Python-level processing can increase execution latency.

ChronosMatch addresses these challenges by designing a low-latency processing pipeline in which orders are transferred through a memory-mapped ring buffer and processed by a Price-Time Priority matching engine.

The performance-critical matching operations are optimized using Cython and C-level structures, while the surrounding system continues to use Python for flexibility and integration.

The project also provides real-time metrics, trade persistence, Whale Order detection, and web and terminal dashboards for monitoring the engine.

---

## 2. Problem Statement

In High-Frequency Trading, microseconds can have a significant impact on execution performance.

Traditional communication between processes may rely on serialization mechanisms such as JSON or Pickle. Serialization and deserialization introduce additional processing overhead and may require unnecessary data copying.

Python also introduces additional overhead in performance-critical sections due to object management and interpreter-level execution.

ChronosMatch aims to reduce these overheads by:

- Using memory-mapped shared memory for IPC.
- Storing orders in fixed-size binary structures.
- Using an SPSC ring buffer for efficient data transfer.
- Implementing the matching engine using Price-Time Priority.
- Moving the critical matching operations to Cython/C-level structures.
- Measuring execution latency at nanosecond resolution.
- Performing trade persistence asynchronously so database operations do not block matching.

---

## 3. Objectives

The main objectives of ChronosMatch are:

- Implement a memory-mapped IPC mechanism.
- Develop an SPSC ring buffer for order transfer.
- Generate high-volume market orders asynchronously.
- Implement a Limit Order Book.
- Implement Price-Time Priority matching.
- Support full and partial order matching.
- Optimize the matching engine using Cython.
- Reduce Python-level overhead in the critical execution path.
- Measure latency and throughput accurately.
- Compare standard Python and Cython engine performance.
- Persist matched trades asynchronously.
- Handle persistence failures without stopping the matching engine.
- Detect orders that sweep multiple price levels.
- Provide real-time monitoring through a web dashboard.
- Provide a terminal-based monitoring dashboard.
- Validate the complete system using automated tests.

---

# 4. System Architecture

```text
                    MARKET FIREHOSE
                          |
                          v
                +---------------------+
                | mmap / SPSC Buffer  |
                |    Zero-Copy IPC    |
                +---------------------+
                          |
                          v
                +---------------------+
                |  Matching Engine    |
                |  Limit Order Book   |
                +---------------------+
                          |
                 +--------+--------+
                 |                 |
                 v                 v
        Standard Python       Cython Engine
          Matcher             C-Level Matcher
                 |                 |
                 +--------+--------+
                          |
                          v
                  Trade Generation
                          |
              +-----------+-----------+
              |                       |
              v                       v
        Metrics Tracking       Persistence Worker
              |                       |
              v                       v
       Monitoring Dashboard     SQLite Trade Ledger
              |
              v
        Whale Order Detection
