from functools import partial
from logging import getLogger
from typing import Optional, Union, Iterator, Iterable

from . import utils
from .const import TreeConf
from .entry import Record, Reference, OpaqueData
from .memory import FileMemory
from .node import (
    Node, LonelyRootNode, RootNode, InternalNode, LeafNode, OverflowNode
)
from .serializer import Serializer, IntSerializer
import copy

logger = getLogger(__name__)


class BPlusTree:
    __slots__ = ['_filename', '_tree_conf', '_mem', '_root_node_page',
                 '_is_open', 'LonelyRootNode', 'RootNode', 'InternalNode',
                 'LeafNode', 'OverflowNode', 'Record', 'Reference']

    # ######################### Public API ################################

    def __init__(self, filename: str, page_size: int = 4096, order: int = 100,
                 key_size: int = 8, value_size: int = 32, cache_size: int = 64,
                 serializer: Optional[Serializer] = None):
        self._filename = filename
        self._tree_conf = TreeConf(
            page_size, order, key_size, value_size,
            serializer or IntSerializer()
        )
        self._create_partials()
        self._mem = FileMemory(filename, self._tree_conf,
                               cache_size=cache_size)
        try:
            metadata = self._mem.get_metadata()
        except ValueError:
            self._initialize_empty_tree()
        else:
            self._root_node_page, self._tree_conf = metadata
        self._is_open = True

    def close(self):
        with self._mem.write_transaction:
            if not self._is_open:
                logger.info('Tree is already closed')
                return

            self._mem.close()
            self._is_open = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def checkpoint(self):
        with self._mem.write_transaction:
            self._mem.perform_checkpoint(reopen_wal=True)

    def insert(self, key, value: bytes, replace=False):
        """Insert a value in the tree.

        :param key: The key at which the value will be recorded, must be of the
                    same type used by the Serializer
        :param value: The value to record in bytes
        :param replace: If True, already existing value will be overridden,
                        otherwise a ValueError is raised.
        """
        print(f"*** {key} insert ***")

        if not isinstance(value, bytes):
            ValueError('Values must be bytes objects')

        with self._mem.write_transaction:
            node = self._search_in_tree(key, self._root_node)

            # Check if a record with the key already exists
            try:
                existing_record = node.get_entry(key)
            except ValueError:
                pass
            else:
                if not replace:
                    raise ValueError('Key {} already exists'.format(key))

                if existing_record.overflow_page:
                    self._delete_overflow(existing_record.overflow_page)

                if len(value) <= self._tree_conf.value_size:
                    existing_record.value = value
                    existing_record.overflow_page = None
                else:
                    existing_record.value = None
                    existing_record.overflow_page = self._create_overflow(
                        value
                    )
                self._mem.set_node(node)
                return

            if len(value) <= self._tree_conf.value_size:
                record = self.Record(key, value=value)
            else:
                # Record values exceeding the max value_size must be placed
                # into overflow pages
                first_overflow_page = self._create_overflow(value)
                record = self.Record(key, value=None,
                                     overflow_page=first_overflow_page)

            if node.can_add_entry:
                node.insert_entry(record)
                self._mem.set_node(node)

            else:
                node.insert_entry(record)
                self._split_leaf(node)
            print(f"insert complete\n\n")

    def batch_insert(self, iterable: Iterable):
        """Insert many elements in the tree at once.

        The iterable object must yield tuples (key, value) in ascending order.
        All keys to insert must be bigger than all keys currently in the tree.
        All inserts happen in a single transaction. This is way faster than
        manually inserting in a loop.
        """
        node = None
        with self._mem.write_transaction:

            for key, value in iterable:

                if node is None:
                    node = self._search_in_tree(key, self._root_node)

                try:
                    biggest_entry = node.biggest_entry
                except IndexError:
                    biggest_entry = None
                if biggest_entry and key <= biggest_entry.key:
                    raise ValueError('Keys to batch insert must be sorted and '
                                     'bigger than keys currently in the tree')

                if len(value) <= self._tree_conf.value_size:
                    record = self.Record(key, value=value)
                else:
                    # Record values exceeding the max value_size must be placed
                    # into overflow pages
                    first_overflow_page = self._create_overflow(value)
                    record = self.Record(key, value=None,
                                         overflow_page=first_overflow_page)

                if node.can_add_entry:
                    node.insert_entry_at_the_end(record)
                else:
                    node.insert_entry_at_the_end(record)
                    self._split_leaf(node)
                    node = None

            if node is not None:
                self._mem.set_node(node)

    def get(self, key, default=None) -> bytes:
        with self._mem.read_transaction:
            node = self._search_in_tree(key, self._root_node)
            try:
                record = node.get_entry(key)
            except ValueError:
                return default
            else:
                rv = self._get_value_from_record(record)
                assert isinstance(rv, bytes)
                return rv

    def __contains__(self, item):
        with self._mem.read_transaction:
            o = object()
            return False if self.get(item, default=o) is o else True

    def __setitem__(self, key, value):
        self.insert(key, value, replace=True)

    def __getitem__(self, item):
        with self._mem.read_transaction:

            if isinstance(item, slice):
                # Returning a dict is the most sensible thing to do
                # as a method cannot return a sometimes a generator
                # and sometimes a normal value
                rv = dict()
                for record in self._iter_slice(item):
                    rv[record.key] = self._get_value_from_record(record)
                return rv

            else:
                rv = self.get(item)
                if rv is None:
                    raise KeyError(item)
                return rv

    def __len__(self):
        with self._mem.read_transaction:
            node = self._left_record_node
            rv = 0
            while True:
                rv += len(node.entries)
                if not node.next_page:
                    return rv
                node = self._mem.get_node(node.next_page)

    def __length_hint__(self):
        with self._mem.read_transaction:
            node = self._root_node
            if isinstance(node, LonelyRootNode):
                # Assume that the lonely root node is half full
                return node.max_children // 2
            # Assume that there are no holes in pages
            last_page = self._mem.last_page
            # Assume that 70% of nodes in a tree carry values
            num_leaf_nodes = int(last_page * 0.70)
            # Assume that every leaf node is half full
            num_records_per_leaf_node = int(
                (node.max_children + node.min_children) / 2
            )
            return num_leaf_nodes * num_records_per_leaf_node

    def __iter__(self, slice_: Optional[slice] = None):
        if not slice_:
            slice_ = slice(None)
        with self._mem.read_transaction:
            for record in self._iter_slice(slice_):
                yield record.key

    keys = __iter__

    def items(self, slice_: Optional[slice] = None) -> Iterator[tuple]:
        if not slice_:
            slice_ = slice(None)
        with self._mem.read_transaction:
            for record in self._iter_slice(slice_):
                yield record.key, self._get_value_from_record(record)

    def values(self, slice_: Optional[slice] = None) -> Iterator[bytes]:
        if not slice_:
            slice_ = slice(None)
        with self._mem.read_transaction:
            for record in self._iter_slice(slice_):
                yield self._get_value_from_record(record)

    def __bool__(self):
        with self._mem.read_transaction:
            for _ in self:
                return True
            return False

    def __repr__(self):
        return '<BPlusTree: {} {}>'.format(self._filename, self._tree_conf)

    # ####################### Implementation ##############################

    def _initialize_empty_tree(self):
        self._root_node_page = self._mem.next_available_page
        with self._mem.write_transaction:
            self._mem.set_node(self.LonelyRootNode(page=self._root_node_page))
        self._mem.set_metadata(self._root_node_page, self._tree_conf)

    def _create_partials(self):
        self.LonelyRootNode = partial(LonelyRootNode, self._tree_conf)
        self.RootNode = partial(RootNode, self._tree_conf)
        self.InternalNode = partial(InternalNode, self._tree_conf)
        self.LeafNode = partial(LeafNode, self._tree_conf)
        self.OverflowNode = partial(OverflowNode, self._tree_conf)
        self.Record = partial(Record, self._tree_conf)
        self.Reference = partial(Reference, self._tree_conf)

    @property
    def _root_node(self) -> Union['LonelyRootNode', 'RootNode']:
        root_node = self._mem.get_node(self._root_node_page)
        if not isinstance(root_node, (LonelyRootNode, RootNode)):
            print(root_node)
            self._print_node(root_node)
        assert isinstance(root_node, (LonelyRootNode, RootNode))
        return root_node

    @property
    def _left_record_node(self) -> Union['LonelyRootNode', 'LeafNode']:
        node = self._root_node
        while not isinstance(node, (LonelyRootNode, LeafNode)):
            node = self._mem.get_node(node.smallest_entry.before)
        return node

    def _iter_slice(self, slice_: slice) -> Iterator[Record]:
        if slice_.step is not None:
            raise ValueError('Cannot iterate with a custom step')

        if (slice_.start is not None and slice_.stop is not None and
                slice_.start >= slice_.stop):
            raise ValueError('Cannot iterate backwards')

        if slice_.start is None:
            node = self._left_record_node
        else:
            node = self._search_in_tree(slice_.start, self._root_node)

        while True:
            for entry in node.entries:
                if slice_.start is not None and entry.key < slice_.start:
                    continue

                if slice_.stop is not None and entry.key >= slice_.stop:
                    return

                yield entry

            if node.next_page:
                node = self._mem.get_node(node.next_page)
            else:
                return

    def _search_in_tree(self, key, node) -> 'Node':
        if isinstance(node, (LonelyRootNode, LeafNode)):
            return node

        page = None

        if key < node.smallest_key:
            page = node.smallest_entry.before

        elif node.biggest_key <= key:
            page = node.biggest_entry.after

        else:
            for ref_a, ref_b in utils.pairwise(node.entries):
                if ref_a.key <= key < ref_b.key:
                    page = ref_a.after
                    break

        assert page is not None

        child_node = self._mem.get_node(page)
        child_node.parent = node
        return self._search_in_tree(key, child_node)

    def _split_leaf(self, old_node: 'Node'):
        """Split a leaf Node to allow the tree to grow."""
        print("leaf node split")
        parent = old_node.parent
        new_node = self.LeafNode(page=self._mem.next_available_page,
                                 next_page=old_node.next_page)
        new_entries = old_node.split_entries()
        new_node.entries = new_entries
        ref = self.Reference(new_node.smallest_key,
                             old_node.page, new_node.page)

        if isinstance(old_node, LonelyRootNode):
            # Convert the LonelyRoot into a Leaf
            old_node = old_node.convert_to_leaf()
            self._create_new_root(ref)
        elif parent.can_add_entry:
            parent.insert_entry(ref)
            self._mem.set_node(parent)
        else:
            parent.insert_entry(ref)
            self._split_parent(parent)

        old_node.next_page = new_node.page

        self._mem.set_node(old_node)
        self._mem.set_node(new_node)

    def _split_parent(self, old_node: Node):
        print("Parent(Interior) Node Split")
        parent = old_node.parent
        new_node = self.InternalNode(page=self._mem.next_available_page)
        new_entries = old_node.split_entries()
        new_node.entries = new_entries

        ref = new_node.pop_smallest()
        ref.before = old_node.page
        ref.after = new_node.page

        if isinstance(old_node, RootNode):
            # Convert the Root into an Internal
            print("New Root Node create")
            old_node = old_node.convert_to_internal()
            self._create_new_root(ref)
        elif parent.can_add_entry:
            parent.insert_entry(ref)
            self._mem.set_node(parent)
        else:
            parent.insert_entry(ref)
            self._split_parent(parent)

        self._mem.set_node(old_node)
        self._mem.set_node(new_node)

    def _create_new_root(self, reference: Reference):
        new_root = self.RootNode(page=self._mem.next_available_page)
        new_root.insert_entry(reference)
        self._root_node_page = new_root.page
        self._mem.set_metadata(self._root_node_page, self._tree_conf)
        self._mem.set_node(new_root)

    def _create_overflow(self, value: bytes) -> int:
        first_overflow_page = self._mem.next_available_page
        next_overflow_page = first_overflow_page

        iterator = utils.iter_slice(value, self.OverflowNode().max_payload)
        for slice_value, is_last in iterator:
            current_overflow_page = next_overflow_page

            if is_last:
                next_overflow_page = None
            else:
                next_overflow_page = self._mem.next_available_page

            overflow_node = self.OverflowNode(
                page=current_overflow_page, next_page=next_overflow_page
            )
            overflow_node.insert_entry_at_the_end(OpaqueData(data=slice_value))
            self._mem.set_node(overflow_node)

        return first_overflow_page

    def _traverse_overflow(self, first_overflow_page: int):
        """Yield all Nodes of an overflow chain."""
        next_overflow_page = first_overflow_page
        while True:
            overflow_node = self._mem.get_node(next_overflow_page)
            yield overflow_node

            next_overflow_page = overflow_node.next_page
            if next_overflow_page is None:
                break

    def _read_from_overflow(self, first_overflow_page: int) -> bytes:
        """Collect all values of an overflow chain."""
        rv = bytearray()
        for overflow_node in self._traverse_overflow(first_overflow_page):
            rv.extend(overflow_node.smallest_entry.data)

        return bytes(rv)

    def _delete_overflow(self, first_overflow_page: int):
        """Delete all Nodes in an overflow chain."""
        for overflow_node in self._traverse_overflow(first_overflow_page):
            self._mem.del_node(overflow_node)

    def _get_value_from_record(self, record: Record) -> bytes:
        if record.value is not None:
            return record.value

        return self._read_from_overflow(record.overflow_page)

    def display(self):
        with self._mem.read_transaction:
            parents = list()
            root_node = self._root_node
            parents.append(root_node)
            self._print_node(root_node)
            print(f"\n")

            if not isinstance(root_node, LonelyRootNode):
                self._print_children(parents)

    def _print_children(self, parents):
        children = list()
        for node in parents:
            for e in node.entries:
                if e.key == node.smallest_key:
                    child_node = self._mem.get_node(e.before)
                    child_node.parent = node
                    children.append(child_node)
                    self._print_node(child_node)

                    child_node = self._mem.get_node(e.after)
                    child_node.parent = node
                    children.append(child_node)
                    self._print_node(child_node)

                else:
                    child_node = self._mem.get_node(e.after)
                    child_node.parent = node
                    children.append(child_node)
                    self._print_node(child_node)

        print(f"\n")

        if isinstance(children[0], LeafNode):
            return None
        else:
            return self._print_children(children)

    def _print_node(self, node):
        print(f"[#{node.page}: ", end='')
        for e in node.entries:
            print(f"{e.key}, ", end='')
        if not isinstance(node, (RootNode, LonelyRootNode)):
            print(f"<parent #{node.parent.page}>", end='')

        print(f"]  ", end='')

    """ 

    아래의 Function들을 완성하시오 

    """

    def delete(self, key):
        print(f"*** {key} delete ***")
        with self._mem.write_transaction:
            node = self._search_in_tree(key, self._root_node)
            print("delete--node key", node.entries) # for test
            if isinstance(node, LonelyRootNode):  # Root Node & Leaf Node
                print("In LonelyRootnode, delete entry");
                node.remove_entry(key)
                self._mem.set_node(node)
            else:  # Leaf Node
                print("In LeafNode, delete entry")
                parent = node.parent
                if node.can_delete_entry:
                    print("case1: simple case, key is at only leaf, not internal") # test
                    node.remove_entry(key)
                    self._mem.set_node(node)
                else:
                    print("case2: key is at leaf")  # test
                    if node.smallest_key > parent.biggest_key:
                        # impossible case if it is well-implemented
                        assert ("Tree Error, parnet's biggest key < child's smallest key")
                    elif node.smallest_key == parent.biggest_key:
                        print("case2-1: node is at the rightmost")  # test
                        src_node = self._mem.get_node(parent.biggest_entry.before)
                        src_node.parent = parent
                    else:
                        print("case2-2")    # test
                        src_node = self._mem.get_node(node.next_page)
                        src_node.parent = parent

                    if src_node.can_delete_entry:
                        self._redistribute_leaf(src_node, node)
                    else:
                        node = self._merge_leaf(src_node, node)

                    node.remove_entry(key)
                    self._mem.set_node(node)

                parent = node.parent
                # change Interior Node

                if key < node.smallest_key and key >= parent.smallest_key:
                    parent.get_entry(key).key = node.smallest_key
                    self._mem.set_node(parent)

            print(f"delete complete\n\n")

    def _redistribute_leaf(self, src_node, dst_node):
        print("Leaf Node redistribute")

        # To do
        parent = src_node.parent

        # borrow one from sibling
        dst_node.insert_entry(src_node.smallest_entry)
        # delete if it is borrowed
        src_node.pop_smallest()

        for elem in parent.entries:
            if elem.after == src_node.page:

                elem.key = src_node.smallest_key
        print("_redistribute_leaf finished:", parent.entries)
        return dst_node

    def _redistribute_parent(self, src_node, dst_node):
        print("Parent(interior) Node redistribute")

        # To do
        parent = dst_node.parent
        if (dst_node.smallest_key > parent.biggest_key):
            _to_be_moved = src_node.entries[-1].key
            dst_node.insert_entry(src_node.get_entry(_to_be_moved))
            src_node.remove_entry(_to_be_moved)

            self._mem.set_node(dst_node); self._mem.set_node(src_node)

            for elem in parent.entries:
                if (elem.before == src_node.page):
                    elem.key = src_node.biggest_key
            self._mem.set_node(parent)
        else:
            dst_node.insert_entry_at_the_end(src_node.pop_smallest())
            self._mem.set_node(dst_node); self._mem.set_node(src_node)

            for elem in parent.entries:
                if (elem.after == src_node.page):
                    elem.key = src_node.smallest_key
            self._mem.set_node(parent)

    def _merge_leaf(self, src_node, dst_node):
        print("Leaf Node merge")
        parent = dst_node.parent

        # To do
        if dst_node.smallest_key == parent.biggest_key:
            for elem in parent.entries:
                if elem.before == src_node.page:
                    _to_be_deleted = parent.get_entry(elem.key)
        else:
            for elem in parent.entries:
                if elem.after == src_node.page:
                    _to_be_deleted = parent.get_entry(elem.key)

        """ Merge src_node and dst_node
            Delete parent entry if needed """
        if isinstance(parent, RootNode):
            if parent.can_delete_entry:
                # To do
                for elem1 in src_node.entries:
                    dst_node.insert_entry(elem1)

                for elem2 in src_node.entries:
                    src_node.remove_entry(elem2)

                self._mem.set_node(dst_node)
                parent.remove_entry(_to_be_deleted.key); self._mem.set_node(parent)

            else:
                # To do
                for elem1 in src_node.entries:
                    dst_node.insert_entry(elem1)

                for elem2 in src_node.entries:
                    src_node.remove_entry(elem2)

        elif parent.can_delete_entry:
            # To do
            for elem1 in src_node.entries:
                dst_node.insert_entry(elem1)

            for elem2 in src_node.entries:
                src_node.remove_entry(elem2.key)
            # update for dst_node, src_node
            self._mem.set_node(dst_node); self._mem.set_node(src_node)

            parent.remove_entry(_to_be_deleted.key)
            self._mem.set_node(parent)

        else:
            # To do
            grand_parent = parent.parent
            for elem in grand_parent.entries:
                if (parent == elem) and (elem == grand_parent.smallest_entry):
                    src_parent = self._mem.get_node(grand_parent.biggest_entry.after)
                elif (parent == elem) and (elem == grand_parent.biggest_entry):
                    src_parent = self._mem.get_node(grand_parent.biggest_entry.before)
                else:
                    src_parent = self._mem.get_node(grand_parent.biggest_entry.after)

            if src_parent.can_delete_entry:
                self._redistribute_parent(src_parent, parent)
            else:
                # Merge between two lists
                dst_node.entries = dst_node.entries + src_node.entries

                for elem1 in parent.entries:
                    if elem1.after == src_node.page:
                        parent.remove_entry(elem1.key)

                for elem2 in parent.entries:
                    if elem2.before == src_node.page:
                        elem2.before = dst_node.page
                parent = self._merge_parent(src_parent, parent)

            # To do OR Nothing
                # Do nothing

        # To do OR Nothing
            # Do nothing
        return dst_node

    def _merge_parent(self, src_node, dst_node):
        # print("src_node: ", str(src_node.entries))
        # print("dst_node: ", str(dst_node.entries))
        print("Parent(interior) Node merge")
        parent = dst_node.parent

        # To do
        node_ref = parent.entries[-1]
        node_ref.before, node_ref.after = dst_node.biggest_entry.after, src_node.smallest_entry.before

        dst_node.insert_entry(node_ref)
        print("*****test1")
        print(src_node.entries)
        print(dst_node.entries)
        print(src_node.parent.entries)
        for elem1 in src_node.entries: dst_node.insert_entry(elem1)
        for elem2 in src_node.entries: src_node.remove_entry(elem2.key)
        print("*****test2")
        for elem in parent.entries:
            if elem.before == src_node.page: elem.before = dst_node.page
        print("*****test3")
        """ Merge src_node and dst_node
            Delete parent entry if needed """
        if isinstance(parent, RootNode):
            # case: parent is the most-upper(ROOT)
            if parent.can_delete_entry:
                # the root is enough
                print("*****if")
                parent.remove_entry(node_ref.key)
                self._mem.set_node(parent)
                # return dst_node
            else:
                # To do
                print("*****else")
                parent.remove_entry(node_ref.key)
                # list concatenating
                parent.entries = parent.entries + dst_node.entries
                # update all nodes to disk
                self._mem.set_node(src_node)
                self._mem.set_node(dst_node)
                self._mem.set_node(parent)

                print("Root Node Delete")

                # return dst_node

        elif parent.can_delete_entry:
            # To do
            parent.remove_entry(node_ref.key)
            self._mem.set_node(parent)

        else:
            # To do
            parent.remove_entry(node_ref.key)
            self._mem.set_node(parent)
            grandparent = parent.parent
            for g_elem in grandparent.entries:
                if g_elem.before == parent.page:
                    src_parent = self._mem.get_node(g_elem.after)
            if src_parent.can_delete_entry:
                self._redistribute_parent(src_parent, parent)
            else:
                parent = self._merge_parent(src_parent, parent)
                # dst_node.parent = parent; src_node.parent = parent
            # To do OR Nothing

        # To do OR Nothing
        '''
        if key < node.smallest_key and key >= parent.smallest_key:
            print("change internal node")
            parent.get_entry(key).key = node.smallest_key
            self._mem.set_node(parent)
        '''
        return dst_node