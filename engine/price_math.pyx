from libc.stdint cimport uint64_t


cdef inline uint64_t calculate_trade_quantity(
    uint64_t incoming_quantity,
    uint64_t resting_quantity,
):
    if incoming_quantity < resting_quantity:
        return incoming_quantity

    return resting_quantity


cpdef uint64_t trade_quantity(
    uint64_t incoming_quantity,
    uint64_t resting_quantity,
):
    """
    C-level calculation of the executable trade quantity.
    """

    return calculate_trade_quantity(
        incoming_quantity,
        resting_quantity,
    )
