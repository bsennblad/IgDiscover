"""
Filter table with parsed IgBLAST results

Discard the following rows in the table:
- no J assigned
- stop codon found
- V gene coverage less than 90
- J gene coverage less than 60
- V gene E-value greater than 1E-3

The filtered table is printed to standard output.
"""
import logging
from itertools import islice

from .table import read_table

logger = logging.getLogger(__name__)

def add_subcommand(subparsers):
	subparser = subparsers.add_parser('filter', help=__doc__.split('\n')[1], description=__doc__)
	subparser.set_defaults(func=filter_command)
	subparser.add_argument('table', help='Table with filtered IgBLAST results.')
	return subparser


def filtered_table(table,
		v_gene_coverage=90,  # at least
		j_gene_coverage=60,  # at least
		v_gene_evalue=1E-3,  # at most
		log=False
	):
	"""
	Discard the following rows in the table (read in by read_table):
	- no J assigned
	- stop codon found
	- V gene coverage less than v_gene_coverage
	- J gene coverage less than j_gene_coverage
	- V gene E-value greater than v_gene_evalue

	Return the filtered table.
	"""
	# Both V and J must be assigned
	filtered = table.dropna(subset=('V_gene', 'J_gene'))[:]
	if log: logger.info('%s rows have both V and J assignment', len(filtered))
	filtered['V_gene'] = pd.Categorical(filtered['V_gene'])

	# Filter out sequences that have a stop codon
	filtered = filtered[filtered.stop == 'no']
	if log: logger.info('%s of those do not have a stop codon', len(filtered))

	# Filter out sequences with a too low V gene hit E-value
	filtered = filtered[filtered.V_evalue <= v_gene_evalue]
	if log: logger.info('%s of those have an E-value of at most %s', len(filtered), v_gene_evalue)

	# Filter out sequences with too low V gene coverage
	filtered = filtered[filtered.V_covered >= v_gene_coverage]
	if log: logger.info('%s of those cover the V gene by at least %s%%', len(filtered), v_gene_coverage)

	# Filter out sequences with too low J gene coverage
	filtered = filtered[filtered.J_covered >= j_gene_coverage]
	if log: logger.info('%s of those cover the J gene by at least %s%%', len(filtered), j_gene_coverage)

	return filtered


def filter_command(args):
	d = read_table(args.table, log=True)
	d = filtered_table(d, log=True)
	print(d.to_csv(sep='\t', index=False))
	logger.info('%d rows written', len(d))
