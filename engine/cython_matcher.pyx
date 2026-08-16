from libc.stdint cimport uint64_t
from libc.stddef cimport size_t
from libc.stdlib cimport malloc, free


cdef struct COrder:
    uint64_t order_id
    uint64_t side
    uint64_t price
    uint64_t quantity


cdef inline uint64_t min_quantity(
    uint64_t a,
    uint64_t b,
):
    if a < b:
        return a

    return b


cdef uint64_t match_batch(
    COrder* orders,
    size_t count,
):
    cdef:
        size_t i
        uint64_t buy_quantity = 0
        uint64_t trades = 0
        uint64_t matched

    for i in range(count):
        if orders[i].side == 1:
            buy_quantity += orders[i].quantity

        elif orders[i].side == 2:
            if buy_quantity > 0:
                matched = min_quantity(
                    buy_quantity,
                    orders[i].quantity,
                )

                buy_quantity -= matched
                trades += 1

    return trades


cpdef uint64_t process_batch(
    uint64_t[::1] order_ids,
    uint64_t[::1] sides,
    uint64_t[::1] prices,
    uint64_t[::1] quantities,
):
    cdef:
        size_t count = order_ids.shape[0]
        size_t i
        COrder* orders
        uint64_t result

    if (
        sides.shape[0] != count
        or prices.shape[0] != count
        or quantities.shape[0] != count
    ):
        raise ValueError("All order arrays must have the same length")

    orders = <COrder*>malloc(
        count * sizeof(COrder)
    )

    if orders == NULL:
        raise MemoryError()

    try:
        for i in range(count):
            orders[i].order_id = order_ids[i]
            orders[i].side = sides[i]
            orders[i].price = prices[i]
            orders[i].quantity = quantities[i]

        result = match_batch(
            orders,
            count,
        )

        return result

    finally:
        free(orders)
