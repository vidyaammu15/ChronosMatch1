RING_BUFFER_CAPACITY = 1024

# Binary format for one order:
# Q = unsigned long long (8 bytes) -> order_id
# B = unsigned char (1 byte)        -> side
# Q = unsigned long long (8 bytes) -> price
# Q = unsigned long long (8 bytes) -> quantity
# Q = unsigned long long (8 bytes) -> timestamp
#
# Total = 33 bytes
ORDER_FORMAT = "=QBQQQ"