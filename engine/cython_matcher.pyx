# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False
# cython: initializedcheck=False

from libc.stdint cimport uint64_t, uint8_t
from libc.stddef cimport size_t
from libc.stdlib cimport malloc, free


cdef struct COrder:
    uint64_t order_id
    uint64_t side
    uint64_t price
    uint64_t quantity
    uint8_t active


cdef inline uint64_t min_quantity(
    uint64_t a,
    uint64_t b,
) noexcept nogil:
    return a if a < b else b


cdef inline bint buy_before(
    const COrder* orders,
    size_t a,
    size_t b,
) noexcept nogil:
    if orders[a].price != orders[b].price:
        return orders[a].price > orders[b].price
    return a < b


cdef inline bint sell_before(
    const COrder* orders,
    size_t a,
    size_t b,
) noexcept nogil:
    if orders[a].price != orders[b].price:
        return orders[a].price < orders[b].price
    return a < b


cdef inline void heap_push_buy(
    size_t* heap,
    size_t* heap_size,
    const COrder* orders,
    size_t index,
) noexcept nogil:
    cdef:
        size_t pos = heap_size[0]
        size_t parent
        size_t temp

    heap[pos] = index
    heap_size[0] = pos + 1

    while pos > 0:
        parent = (pos - 1) >> 1

        if buy_before(orders, heap[parent], heap[pos]):
            break

        if (
            orders[heap[parent]].price == orders[heap[pos]].price
            and heap[parent] < heap[pos]
        ):
            break

        temp = heap[parent]
        heap[parent] = heap[pos]
        heap[pos] = temp

        pos = parent


cdef inline void heap_push_sell(
    size_t* heap,
    size_t* heap_size,
    const COrder* orders,
    size_t index,
) noexcept nogil:
    cdef:
        size_t pos = heap_size[0]
        size_t parent
        size_t temp

    heap[pos] = index
    heap_size[0] = pos + 1

    while pos > 0:
        parent = (pos - 1) >> 1

        if sell_before(orders, heap[parent], heap[pos]):
            break

        if (
            orders[heap[parent]].price == orders[heap[pos]].price
            and heap[parent] < heap[pos]
        ):
            break

        temp = heap[parent]
        heap[parent] = heap[pos]
        heap[pos] = temp

        pos = parent


cdef inline size_t heap_pop_buy(
    size_t* heap,
    size_t* heap_size,
    const COrder* orders,
) noexcept nogil:
    cdef:
        size_t result = heap[0]
        size_t count = heap_size[0] - 1
        size_t pos = 0
        size_t left
        size_t right
        size_t best
        size_t temp

    heap_size[0] = count

    if count == 0:
        return result

    heap[0] = heap[count]

    while True:
        left = (pos << 1) + 1

        if left >= count:
            break

        right = left + 1
        best = left

        if right < count and buy_before(orders, heap[right], heap[left]):
            best = right

        if buy_before(orders, heap[pos], heap[best]):
            break

        temp = heap[pos]
        heap[pos] = heap[best]
        heap[best] = temp

        pos = best

    return result


cdef inline size_t heap_pop_sell(
    size_t* heap,
    size_t* heap_size,
    const COrder* orders,
) noexcept nogil:
    cdef:
        size_t result = heap[0]
        size_t count = heap_size[0] - 1
        size_t pos = 0
        size_t left
        size_t right
        size_t best
        size_t temp

    heap_size[0] = count

    if count == 0:
        return result

    heap[0] = heap[count]

    while True:
        left = (pos << 1) + 1

        if left >= count:
            break

        right = left + 1
        best = left

        if right < count and sell_before(orders, heap[right], heap[left]):
            best = right

        if sell_before(orders, heap[pos], heap[best]):
            break

        temp = heap[pos]
        heap[pos] = heap[best]
        heap[best] = temp

        pos = best

    return result


cdef uint64_t match_batch(
    COrder* orders,
    size_t count,
    size_t* buy_heap,
    size_t* buy_size,
    size_t* sell_heap,
    size_t* sell_size,
) noexcept nogil:
    cdef:
        size_t i
        size_t best_buy_idx
        size_t best_sell_idx
        uint64_t matched
        uint64_t trades = 0

    for i in range(count):
        if orders[i].side == 1:
            heap_push_buy(
                buy_heap,
                buy_size,
                orders,
                i,
            )

            while buy_size[0] > 0 and sell_size[0] > 0:
                while sell_size[0] > 0 and not orders[sell_heap[0]].active:
                    heap_pop_sell(sell_heap, sell_size, orders)

                if sell_size[0] == 0:
                    break

                best_buy_idx = buy_heap[0]
                best_sell_idx = sell_heap[0]

                if orders[best_buy_idx].price < orders[best_sell_idx].price:
                    break

                matched = min_quantity(
                    orders[best_buy_idx].quantity,
                    orders[best_sell_idx].quantity,
                )

                orders[best_buy_idx].quantity -= matched
                orders[best_sell_idx].quantity -= matched

                trades += 1

                if orders[best_sell_idx].quantity == 0:
                    orders[best_sell_idx].active = 0
                    heap_pop_sell(sell_heap, sell_size, orders)

                if orders[best_buy_idx].quantity == 0:
                    orders[best_buy_idx].active = 0
                    heap_pop_buy(buy_heap, buy_size, orders)

        elif orders[i].side == 2:
            heap_push_sell(
                sell_heap,
                sell_size,
                orders,
                i,
            )

            while buy_size[0] > 0 and sell_size[0] > 0:
                while buy_size[0] > 0 and not orders[buy_heap[0]].active:
                    heap_pop_buy(buy_heap, buy_size, orders)

                if buy_size[0] == 0:
                    break

                best_sell_idx = sell_heap[0]
                best_buy_idx = buy_heap[0]

                if orders[best_sell_idx].price > orders[best_buy_idx].price:
                    break

                matched = min_quantity(
                    orders[best_sell_idx].quantity,
                    orders[best_buy_idx].quantity,
                )

                orders[best_sell_idx].quantity -= matched
                orders[best_buy_idx].quantity -= matched

                trades += 1

                if orders[best_buy_idx].quantity == 0:
                    orders[best_buy_idx].active = 0
                    heap_pop_buy(buy_heap, buy_size, orders)

                if orders[best_sell_idx].quantity == 0:
                    orders[best_sell_idx].active = 0
                    heap_pop_sell(sell_heap, sell_size, orders)

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
        size_t* buy_heap
        size_t* sell_heap
        size_t buy_size = 0
        size_t sell_size = 0
        uint64_t result
        const uint64_t* raw_ids
        const uint64_t* raw_sides
        const uint64_t* raw_prices
        const uint64_t* raw_qtys

    if (
        sides.shape[0] != count
        or prices.shape[0] != count
        or quantities.shape[0] != count
    ):
        raise ValueError(
            "All order arrays must have the same length"
        )

    if count == 0:
        return 0

    raw_ids = &order_ids[0]
    raw_sides = &sides[0]
    raw_prices = &prices[0]
    raw_qtys = &quantities[0]

    orders = <COrder*>malloc(count * sizeof(COrder))
    buy_heap = <size_t*>malloc(count * sizeof(size_t))
    sell_heap = <size_t*>malloc(count * sizeof(size_t))

    if orders == NULL or buy_heap == NULL or sell_heap == NULL:
        if orders != NULL:
            free(orders)
        if buy_heap != NULL:
            free(buy_heap)
        if sell_heap != NULL:
            free(sell_heap)
        raise MemoryError("Failed to allocate memory for order matching")

    try:
        with nogil:
            for i in range(count):
                orders[i].order_id = raw_ids[i]
                orders[i].side = raw_sides[i]
                orders[i].price = raw_prices[i]
                orders[i].quantity = raw_qtys[i]
                orders[i].active = 1

            result = match_batch(
                orders,
                count,
                buy_heap,
                &buy_size,
                sell_heap,
                &sell_size,
            )

        return result

    finally:
        free(orders)
        free(buy_heap)
        free(sell_heap)
