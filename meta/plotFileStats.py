## Just a fun little utility to plot line-of-code statistics.

import subprocess
import numpy
import pylab

def measureLines():
    baseCommand = 'find . -name "*py" | grep -v data | xargs cat'
    totalLines = int(subprocess.Popen(
            '%s | wc -l' % baseCommand, 
            stdout = subprocess.PIPE, shell = True).communicate()[0])
    commentLines = int(subprocess.Popen(
            '%s | grep -c "#"' % baseCommand,
            stdout = subprocess.PIPE, shell = True).communicate()[0])
    blankLines = int(subprocess.Popen(
            '%s | grep -cE "^\s*$"' % baseCommand,
            stdout = subprocess.PIPE, shell = True).communicate()[0])
    return [totalLines, commentLines, blankLines]

# Find out how many commits there are.
history = subprocess.Popen('hg history | head -1',
        stdout = subprocess.PIPE, shell = True).communicate()[0]
history = int(history.split(':')[1])

lines = []
for i in xrange(history + 1):
    subprocess.Popen('hg revert -r %d .' % i, stdout = subprocess.PIPE, 
            shell = True).wait()
    # Delete all untracked files so we only generate stats on files we care
    # about. And yes, I'm aware of the irony in invoking Perl here, but 
    # I don't really care.
    subprocess.Popen("hg status -u . | perl -ne 'chomp; /\? (.*)/; `rm $1`'",
            shell = True).wait()
    lines.append(measureLines())

lines = numpy.array(lines)
xVals = numpy.arange(history + 1)

colors = ['r', 'g', 'b']
labels = ['Total lines', 'Comments', 'Whitespace']
for i in xrange(len(lines[0])):
    pylab.plot(xVals, lines[:, i], colors[i], label = labels[i])
pylab.legend(loc = 'upper left')
pylab.show()

