from libc.stdint cimport uint64_t
from libc.stddef cimport size_t
from libc.stdlib cimport malloc, free


cdef struct COrder:
    uint64_t order_id
    uint64_t side
    uint64_t price
    uint64_t quantity
    bint active


cdef inline uint64_t min_quantity(
    uint64_t a,
    uint64_t b,
) noexcept nogil:
    if a < b:
        return a
    return b


cdef inline bint buy_before(
    COrder* orders,
    size_t a,
    size_t b,
) noexcept nogil:
    if orders[a].price != orders[b].price:
        return orders[a].price > orders[b].price

    return a < b


cdef inline bint sell_before(
    COrder* orders,
    size_t a,
    size_t b,
) noexcept nogil:
    if orders[a].price != orders[b].price:
        return orders[a].price < orders[b].price

    return a < b


cdef inline void heap_push_buy(
    size_t* heap,
    size_t* heap_size,
    COrder* orders,
    size_t index,
) noexcept nogil:
    cdef:
        size_t pos = heap_size[0]
        size_t parent
        size_t temp

    heap[pos] = index
    heap_size[0] += 1

    while pos > 0:
        parent = (pos - 1) // 2

        if buy_before(
            orders,
            heap[parent],
            heap[pos],
        ):
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
    COrder* orders,
    size_t index,
) noexcept nogil:
    cdef:
        size_t pos = heap_size[0]
        size_t parent
        size_t temp

    heap[pos] = index
    heap_size[0] += 1

    while pos > 0:
        parent = (pos - 1) // 2

        if sell_before(
            orders,
            heap[parent],
            heap[pos],
        ):
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
    COrder* orders,
) noexcept nogil:
    cdef:
        size_t result = heap[0]
        size_t last
        size_t pos = 0
        size_t left
        size_t right
        size_t best
        size_t temp

    heap_size[0] -= 1

    if heap_size[0] == 0:
        return result

    last = heap[heap_size[0]]
    heap[0] = last

    while True:
        left = pos * 2 + 1

        if left >= heap_size[0]:
            break

        right = left + 1
        best = left

        if right < heap_size[0]:
            if buy_before(
                orders,
                heap[right],
                heap[left],
            ):
                best = right

        if buy_before(
            orders,
            heap[pos],
            heap[best],
        ):
            break

        temp = heap[pos]
        heap[pos] = heap[best]
        heap[best] = temp

        pos = best

    return result


cdef inline size_t heap_pop_sell(
    size_t* heap,
    size_t* heap_size,
    COrder* orders,
) noexcept nogil:
    cdef:
        size_t result = heap[0]
        size_t last
        size_t pos = 0
        size_t left
        size_t right
        size_t best
        size_t temp

    heap_size[0] -= 1

    if heap_size[0] == 0:
        return result

    last = heap[heap_size[0]]
    heap[0] = last

    while True:
        left = pos * 2 + 1

        if left >= heap_size[0]:
            break

        right = left + 1
        best = left

        if right < heap_size[0]:
            if sell_before(
                orders,
                heap[right],
                heap[left],
            ):
                best = right

        if sell_before(
            orders,
            heap[pos],
            heap[best],
        ):
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
        size_t best_index
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

                while (
                    sell_size[0] > 0
                    and not orders[sell_heap[0]].active
                ):
                    heap_pop_sell(
                        sell_heap,
                        sell_size,
                        orders,
                    )

                if sell_size[0] == 0:
                    break

                best_index = buy_heap[0]

                if (
                    orders[best_index].price
                    < orders[sell_heap[0]].price
                ):
                    break

                matched = min_quantity(
                    orders[best_index].quantity,
                    orders[sell_heap[0]].quantity,
                )

                orders[best_index].quantity -= matched
                orders[sell_heap[0]].quantity -= matched

                trades += 1

                if orders[sell_heap[0]].quantity == 0:
                    orders[sell_heap[0]].active = False
                    heap_pop_sell(
                        sell_heap,
                        sell_size,
                        orders,
                    )

                if orders[best_index].quantity == 0:
                    orders[best_index].active = False
                    heap_pop_buy(
                        buy_heap,
                        buy_size,
                        orders,
                    )

        elif orders[i].side == 2:

            heap_push_sell(
                sell_heap,
                sell_size,
                orders,
                i,
            )

            while buy_size[0] > 0 and sell_size[0] > 0:

                while (
                    buy_size[0] > 0
                    and not orders[buy_heap[0]].active
                ):
                    heap_pop_buy(
                        buy_heap,
                        buy_size,
                        orders,
                    )

                if buy_size[0] == 0:
                    break

                best_index = sell_heap[0]

                if (
                    orders[best_index].price
                    > orders[buy_heap[0]].price
                ):
                    break

                matched = min_quantity(
                    orders[best_index].quantity,
                    orders[buy_heap[0]].quantity,
                )

                orders[best_index].quantity -= matched
                orders[buy_heap[0]].quantity -= matched

                trades += 1

                if orders[buy_heap[0]].quantity == 0:
                    orders[buy_heap[0]].active = False
                    heap_pop_buy(
                        buy_heap,
                        buy_size,
                        orders,
                    )

                if orders[best_index].quantity == 0:
                    orders[best_index].active = False
                    heap_pop_sell(
                        sell_heap,
                        sell_size,
                        orders,
                    )

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

    if (
        sides.shape[0] != count
        or prices.shape[0] != count
        or quantities.shape[0] != count
    ):
        raise ValueError(
            "All order arrays must have the same length"
        )

    orders = <COrder*>malloc(
        count * sizeof(COrder)
    )

    buy_heap = <size_t*>malloc(
        count * sizeof(size_t)
    )

    sell_heap = <size_t*>malloc(
        count * sizeof(size_t)
    )

    if (
        orders == NULL
        or buy_heap == NULL
        or sell_heap == NULL
    ):
        if orders != NULL:
            free(orders)

        if buy_heap != NULL:
            free(buy_heap)

        if sell_heap != NULL:
            free(sell_heap)

        raise MemoryError()

    try:
        for i in range(count):
            orders[i].order_id = order_ids[i]
            orders[i].side = sides[i]
            orders[i].price = prices[i]
            orders[i].quantity = quantities[i]
            orders[i].active = True

        with nogil:
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
