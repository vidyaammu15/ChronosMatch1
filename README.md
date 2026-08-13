# ChronosMatch - Zero-Copy High-Frequency Trading Engine

## Week 1 - Memory Mapping & Market Firehose

### Completed Work

- Implemented an mmap-backed Single-Producer Single-Consumer (SPSC) ring buffer.
- Used Python `mmap` and `struct` for fixed-size binary order storage.
- Implemented order serialization and deserialization.
- Implemented ring-buffer read/write operations.
- Implemented empty/full state handling and wraparound support.
- Added batched writes for high-throughput order ingestion.
- Implemented the asynchronous Market Firehose using `asyncio`.
- Generated and transferred 100,000 mock trading orders through the mmap IPC bus.
- Verified FIFO ordering from order ID 1 through 100,000.
- Achieved approximately 847K-933K orders/second in the firehose producer benchmark.
- Successfully consumed all 100,000 orders.
- Added automated tests with 42 tests passing.

### Week 1 Status

**Completed successfully.**

### Performance

| Metric | Result |
|---|---:|
| Orders generated | 100,000 |
| Producer throughput | ~847K-933K orders/sec |
| Orders consumed | 100,000 |
| Consumer throughput | ~432K orders/sec |
| Automated tests | 42 passed |

## Upcoming - Week 2

### Python Matching Engine

- Implement the Limit Order Book.
- Implement Price-Time Priority.
- Prepare the matching engine for low-latency execution.

### Latency Dashboard

- Build a raw `curses` terminal interface.
- Display the top of the Order Book.
- Display Bid/Ask spread in real time.