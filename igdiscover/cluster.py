from collections import OrderedDict, defaultdict
import pandas as pd
from scipy.spatial import distance
from scipy.cluster import hierarchy
from sqt.align import hamming_distance
from .utils import distances
from .trie import Trie


def all_nodes(root):
	"""Return a list of all nodes of the tree, from left to right (iterative implementation)."""
	result = []
	path = [None]
	node = root
	while node is not None:
		if node.left is not None:
			path.append(node)
			node = node.left
		elif node.right is not None:
			result.append(node)
			node = node.right
		else:
			result.append(node)
			node = path.pop()
			if node is not None:
				result.append(node)
				node = node.right

	return result


def inner_nodes(root):
	"""
	Return a list of all inner nodes of the tree, from left to right.
	"""
	return [node for node in all_nodes(root) if not node.is_leaf()]


def collect_ids(root):
	"""
	Return a list of ids of all leaves of the given tree
	"""
	return [node.id for node in all_nodes(root) if node.is_leaf()]


def cluster_sequences(sequences, minsize=5):
	"""
	Cluster the given sequences into groups of similar sequences.

	Return a triple that contains a pandas.DataFrame with the edit distances,
	the linkage result, and a list that maps sequence ids to their cluster id.
	If an entry is zero in that list, it means that the sequence is not part of
	a cluster.
	"""
	matrix = distances(sequences)
	linkage = hierarchy.linkage(distance.squareform(matrix), method='average')
	# Linkage columns are:
	# 0, 1: merged clusters, 2: distance, 3: number of nodes in cluster
	inner = inner_nodes(hierarchy.to_tree(linkage))
	prev = linkage[:, 2].max()  # highest distance
	clusters = [0] * len(sequences)
	cl = 1
	for n in inner:
		if n.dist > 0 and prev / n.dist < 0.8 \
				and n.left.count >= minsize and n.right.count >= minsize:
			for id in collect_ids(n.left):
				# Do not overwrite previously assigned ids
				if clusters[id] == 0:
					clusters[id] = cl
			cl += 1
		prev = n.dist
	# At the end of the above loop, we have not processed the rightmost
	# subtree. In our experiments, it never contains true novel sequences,
	# so we omit it.

	return pd.DataFrame(matrix), linkage, clusters


class Graph:
	"""Graph that can find connected components"""
	def __init__(self, nodes):
		self._nodes = OrderedDict()
		for node in nodes:
			self._nodes[node] = []

	def add_edge(self, node1, node2):
		self._nodes[node1].append(node2)
		self._nodes[node2].append(node1)

	def connected_components(self):
		"""Return a list of connected components."""
		visited = set()
		components = []
		for node, neighbors in self._nodes.items():
			if node in visited:
				continue
			# Start a new component
			to_visit = [node]
			component = []
			while to_visit:
				n = to_visit.pop()
				if n in visited:
					continue
				visited.add(n)
				component.append(n)
				for neighbor in self._nodes[n]:
					if neighbor not in visited:
						to_visit.append(neighbor)
			components.append(component)
		return components


def hamming_single_linkage(strings, mismatches, use_trie=False):
	"""
	Cluster a set of strings by their hamming distance: Strings with
	a distance of at most 'mismatches' will be put into the same cluster.

	Return a list of connected components (clusters).
	"""
	components = []

	# First pre-cluster strings by length
	string_lists = defaultdict(list)
	for s in strings:
		string_lists[len(s)].append(s)
	for strings in string_lists.values():
		graph = Graph(strings)
		if use_trie:
			trie = Trie()
			for s in strings:
				trie.add(s)
			for s in strings:
				for neighbor in trie.find_all_similar(s, mismatches):
					if neighbor != s:
						graph.add_edge(s, neighbor)
		else:
			for i, s in enumerate(strings):
				for j, t in enumerate(strings[i + 1:]):
					if hamming_distance(s, t) <= mismatches:
						graph.add_edge(s, t)

		components.extend(graph.connected_components())
	return components
