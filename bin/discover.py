"""
Find common V genes
"""
import logging
from collections import Counter

from table import read_table_and_filter

logger = logging.getLogger(__name__)


def add_subcommand(subparsers):
	subparser = subparsers.add_parser('discover', help=__doc__)
	subparser.set_defaults(func=discover_command)
	subparser.add_argument('--minimum-frequency', '-n', type=int, metavar='N',
		default=None,
		help='Minimum number of datasets in which sequence must occur (default is no. of files divided by two)')
	subparser.add_argument('table', help='Table with parsed IgBLAST results (give at least two)', nargs='+')
	return subparser


def discover_command(args):
	if args.minimum_frequency is None:
		minimum_frequency = (len(args.table) + 1) // 2
	else:
		minimum_frequency = args.minimum_frequency
	logger.info('Minimum frequency set to %s', minimum_frequency)
	tables = []
	for path in args.table:
		table = read_table_and_filter(path)
		table = table.loc[:,['V_gene', 'V%SHM', 'V_nt']]
		tables.append(table)
	counter = Counter()
	for table in tables:
		counter.update(set(table.V_nt))
	print('Frequency', 'Gene', '%SHM', 'Sequence', sep='\t')
	for sequence, frequency in counter.most_common():
		if frequency < minimum_frequency:
			break
		for table in tables:
			matching_rows = table[table.V_nt == sequence]
			if matching_rows.empty:
				continue
			row = matching_rows.iloc[0]
			gene = row['V_gene']
			shm = row['V%SHM']
			break
		print(frequency, gene, shm, sequence, sep='\t')