## This simple script handles displaying the output of a cProfile profiling 
# run. 
import sys
import pstats
p = pstats.Stats(sys.argv[1])

p.strip_dirs()
p.sort_stats('time').print_stats(100)
p.print_callees(100)
p.sort_stats('cumulative').print_stats(40)
p.print_callees(40)
