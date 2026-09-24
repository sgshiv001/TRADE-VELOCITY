"""Small, explicit data structures used by the order book and statistics."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Generic, Iterator, TypeVar

T = TypeVar("T")


class BinaryHeap(Generic[T]):
    """Binary heap with a caller supplied higher-priority comparison."""

    def __init__(self, higher_priority):
        self._items: list[T] = []
        self._higher_priority = higher_priority

    def __len__(self) -> int:
        return len(self._items)

    def peek(self) -> T:
        return self._items[0]

    def push(self, item: T) -> None:
        data = self._items
        data.append(item)
        index = len(data) - 1
        while index:
            parent = (index - 1) // 2
            if not self._higher_priority(data[index], data[parent]):
                break
            data[index], data[parent] = data[parent], data[index]
            index = parent

    def pop(self) -> T:
        data = self._items
        top = data[0]
        tail = data.pop()
        if data:
            data[0] = tail
            index = 0
            while (left := 2 * index + 1) < len(data):
                right = left + 1
                child = right if right < len(data) and self._higher_priority(data[right], data[left]) else left
                if not self._higher_priority(data[child], data[index]):
                    break
                data[index], data[child] = data[child], data[index]
                index = child
        return top


@dataclass(slots=True)
class QueueNode(Generic[T]):
    value: T
    previous: QueueNode[T] | None = None
    next: QueueNode[T] | None = None


class LinkedQueue(Generic[T]):
    """FIFO queue whose nodes can also be removed in O(1)."""

    def __init__(self):
        self.head: QueueNode[T] | None = None
        self.tail: QueueNode[T] | None = None
        self.length = 0

    def append(self, value: T) -> QueueNode[T]:
        node = QueueNode(value, self.tail)
        if self.tail is None:
            self.head = node
        else:
            self.tail.next = node
        self.tail = node
        self.length += 1
        return node

    def remove(self, node: QueueNode[T]) -> None:
        if node.previous is None:
            self.head = node.next
        else:
            node.previous.next = node.next
        if node.next is None:
            self.tail = node.previous
        else:
            node.next.previous = node.previous
        node.previous = node.next = None
        self.length -= 1

    def __iter__(self) -> Iterator[T]:
        node = self.head
        while node is not None:
            yield node.value
            node = node.next


@dataclass(slots=True)
class AVLNode(Generic[T]):
    key: Decimal
    value: T
    left: AVLNode[T] | None = None
    right: AVLNode[T] | None = None
    height: int = 1


class AVLTree(Generic[T]):
    """Price-keyed AVL tree for ordered depth queries."""

    def __init__(self):
        self.root: AVLNode[T] | None = None

    @staticmethod
    def _height(node: AVLNode[T] | None) -> int:
        return node.height if node else 0

    @classmethod
    def _update(cls, node: AVLNode[T]) -> None:
        node.height = 1 + max(cls._height(node.left), cls._height(node.right))

    @classmethod
    def _rotate_left(cls, node: AVLNode[T]) -> AVLNode[T]:
        top = node.right
        assert top is not None
        node.right = top.left
        top.left = node
        cls._update(node)
        cls._update(top)
        return top

    @classmethod
    def _rotate_right(cls, node: AVLNode[T]) -> AVLNode[T]:
        top = node.left
        assert top is not None
        node.left = top.right
        top.right = node
        cls._update(node)
        cls._update(top)
        return top

    @classmethod
    def _balance(cls, node: AVLNode[T]) -> AVLNode[T]:
        cls._update(node)
        difference = cls._height(node.left) - cls._height(node.right)
        if difference > 1:
            assert node.left is not None
            if cls._height(node.left.left) < cls._height(node.left.right):
                node.left = cls._rotate_left(node.left)
            return cls._rotate_right(node)
        if difference < -1:
            assert node.right is not None
            if cls._height(node.right.right) < cls._height(node.right.left):
                node.right = cls._rotate_right(node.right)
            return cls._rotate_left(node)
        return node

    def get(self, key: Decimal) -> T | None:
        node = self.root
        while node is not None:
            if key == node.key:
                return node.value
            node = node.left if key < node.key else node.right
        return None

    def insert(self, key: Decimal, value: T) -> None:
        def add(node: AVLNode[T] | None) -> AVLNode[T]:
            if node is None:
                return AVLNode(key, value)
            if key < node.key:
                node.left = add(node.left)
            elif key > node.key:
                node.right = add(node.right)
            else:
                raise ValueError("duplicate price level")
            return self._balance(node)

        self.root = add(self.root)

    def delete(self, key: Decimal) -> None:
        def remove(node: AVLNode[T] | None, target: Decimal) -> AVLNode[T] | None:
            if node is None:
                raise KeyError(target)
            if target < node.key:
                node.left = remove(node.left, target)
            elif target > node.key:
                node.right = remove(node.right, target)
            else:
                if node.left is None:
                    return node.right
                if node.right is None:
                    return node.left
                successor = node.right
                while successor.left is not None:
                    successor = successor.left
                node.key, node.value = successor.key, successor.value
                node.right = remove(node.right, successor.key)
            return self._balance(node)

        self.root = remove(self.root, key)

    def items(self, descending: bool = False) -> Iterator[tuple[Decimal, T]]:
        def walk(node: AVLNode[T] | None) -> Iterator[tuple[Decimal, T]]:
            if node is not None:
                yield from walk(node.right if descending else node.left)
                yield node.key, node.value
                yield from walk(node.left if descending else node.right)

        yield from walk(self.root)


class FenwickTree:
    """Appendable prefix sums; capacity doubling keeps appends amortized O(log n)."""

    def __init__(self):
        self.values: list[int] = []
        self.tree: list[int] = [0, 0]
        self.capacity = 1

    def append(self, value: int) -> None:
        self.values.append(value)
        if len(self.values) > self.capacity:
            self.capacity *= 2
            self.tree = [0] * (self.capacity + 1)
            for index, old_value in enumerate(self.values, 1):
                self._add(index, old_value)
        else:
            self._add(len(self.values), value)

    def _add(self, index: int, value: int) -> None:
        while index <= self.capacity:
            self.tree[index] += value
            index += index & -index

    def prefix_sum(self, count: int) -> int:
        if count < 0 or count > len(self.values):
            raise ValueError("count outside recorded trades")
        result = 0
        while count:
            result += self.tree[count]
            count -= count & -count
        return result

    def range_sum(self, start: int, end: int) -> int:
        """Sum values at zero-based indices in [start, end)."""
        if start < 0 or start > end or end > len(self.values):
            raise ValueError("invalid trade range")
        return self.prefix_sum(end) - self.prefix_sum(start)
