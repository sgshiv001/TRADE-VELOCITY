"""Exercise structural invariants and collision cases, independently of matching."""

from dataclasses import dataclass
from decimal import Decimal
import random

import pytest

from stock_engine.structures import AVLTree, BinaryHeap, FenwickTree, HashTable, LinkedQueue


@dataclass(frozen=True)
class CollidingKey:
    value: int

    def __hash__(self):
        return 7


def test_hash_table_collision_chains_survive_resize_update_and_removal():
    table = HashTable[CollidingKey, int | None]()
    for value in range(200):
        table[CollidingKey(value)] = value
    assert len(table) == 200
    assert len(table._buckets) > 8
    for value in range(200):
        assert table[CollidingKey(value)] == value

    table[CollidingKey(50)] = None
    assert len(table) == 200
    assert table.get(CollidingKey(50), "missing") is None
    assert table.pop(CollidingKey(50)) is None
    assert CollidingKey(50) not in table
    assert table.pop(CollidingKey(50), "missing") == "missing"
    with pytest.raises(KeyError):
        del table[CollidingKey(50)]
    with pytest.raises(TypeError):
        table[[]] = 0

    # Remove chain head, middle, and tail nodes across successive shrinkages.
    order = list(range(200))
    random.Random(13).shuffle(order)
    for value in order:
        if value != 50:
            assert table.pop(CollidingKey(value)) == value
    assert dict(table) == {}
    assert len(table._buckets) == 8
    table[CollidingKey(200)] = 200
    assert list(table.items()) == [(CollidingKey(200), 200)]


def test_hash_table_randomized_operations_agree_with_dictionary():
    rng = random.Random(91)
    table = HashTable[int, int]()
    reference = {}
    for _ in range(2000):
        key = rng.randrange(100)
        if rng.randrange(3):
            value = rng.randrange(1000)
            table[key] = reference[key] = value
        else:
            assert table.pop(key, None) == reference.pop(key, None)
        assert len(table) == len(reference)
        assert dict(table.items()) == reference


@pytest.mark.parametrize("descending", [False, True])
def test_bulk_heap_and_incremental_pushes_obey_priority(descending):
    rng = random.Random(17)
    values = [rng.randrange(-100, 101) for _ in range(500)]
    higher = (lambda a, b: a > b) if descending else (lambda a, b: a < b)
    heap = BinaryHeap(higher, values[:250])
    for value in values[250:]:
        heap.push(value)
    for expected in sorted(values, reverse=descending):
        assert heap.peek() == expected
        assert heap.pop() == expected
    assert len(heap) == 0
    with pytest.raises(IndexError):
        heap.pop()


def test_queue_unlinks_middle_head_tail_and_reuses_empty_queue():
    queue = LinkedQueue[int]()
    nodes = [queue.append(value) for value in range(5)]
    for index, expected in [(2, [0, 1, 3, 4]), (0, [1, 3, 4]), (4, [1, 3]), (1, [3]), (3, [])]:
        queue.remove(nodes[index])
        assert list(queue) == expected
        assert queue.length == len(expected)
        assert queue.head is None or queue.head.previous is None
        assert queue.tail is None or queue.tail.next is None
        node = queue.head
        previous = None
        while node is not None:
            assert node.previous is previous
            previous, node = node, node.next
    queue.append(9)
    assert queue.head is queue.tail
    assert list(queue) == [9]


def test_avl_balances_and_heights_hold_after_every_mutation():
    def check(node):
        if node is None:
            return 0, []
        left_height, left_keys = check(node.left)
        right_height, right_keys = check(node.right)
        assert abs(left_height - right_height) <= 1
        assert node.height == 1 + max(left_height, right_height)
        assert all(key < node.key for key in left_keys)
        assert all(key > node.key for key in right_keys)
        return node.height, left_keys + [node.key] + right_keys

    tree = AVLTree[int]()
    keys = list(range(100))
    rng = random.Random(29)
    rng.shuffle(keys)
    for key in keys:
        tree.insert(Decimal(key), key)
        check(tree.root)
    rng.shuffle(keys)
    for key in keys:
        assert tree.get(Decimal(key)) == key
        tree.delete(Decimal(key))
        assert tree.get(Decimal(key)) is None
        check(tree.root)
    assert tree.root is None


def test_fenwick_prefixes_remain_correct_at_capacity_boundaries():
    tree = FenwickTree()
    values = []
    for value in range(1, 258):
        values.append(value)
        tree.append(value)
        assert tree.prefix_sum(len(values)) == sum(values)
        assert tree.range_sum(max(0, len(values) - 9), len(values)) == sum(values[-9:])
    for start, end in [(-1, 1), (2, 1), (0, 258)]:
        with pytest.raises(ValueError):
            tree.range_sum(start, end)
