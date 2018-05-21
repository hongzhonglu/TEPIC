import argparse
import datetime

from utils import readGTF, readIntraLoops, writeToFile


# Iterates over all genes and for each gene over all loops of its respective chromosome
# to find loops within a given radius of the TSS
# Returns:
# 	all matched loops
# 		{key : value} -> {gene : [loopID]}
# 	the loopset
# 		set of { loopID }
# 	all loops per chromosome
# 		{key : value} -> {chr : set of {(loopID, start X, end X, start Y, end Y, observations count)}}
def run(genes, loops, radius):
    matchedLoops = {}
    loopSet = set()
    loopsPerChromosome = {}

    for geneKey in genes:
        chrLoops = loops[genes[geneKey][0]]
        pos = genes[geneKey][1]
        posRight = pos + radius
        posLeft = pos - radius

        if geneKey not in matchedLoops:
            matchedLoops[geneKey] = []

        if genes[geneKey][0] not in loopsPerChromosome:
            loopsPerChromosome[genes[geneKey][0]] = set()

        for loop in chrLoops:

            if posLeft <= loop[1] <= posRight or posLeft <= loop[2] <= posRight:

                matchedLoops[geneKey].append(loop[0])
                loopSet.add(loop)
                loopsPerChromosome[genes[geneKey][0]].add(loop)

            else:
                if posLeft <= loop[3] <= posRight or posLeft <= loop[4] <= posRight:
                    matchedLoops[geneKey].append(loop[0])
                    loopSet.add(loop)
                    loopsPerChromosome[genes[geneKey][0]].add(loop)

    return matchedLoops, loopSet, loopsPerChromosome


# Aggregates various statistical properties from the results and writes it to file
def postProcessing(results, tss, intraLoops, radius):
    totalGeneCount = len(tss)

    totalLoopCount = 0
    for chrLoops in intraLoops:
        totalLoopCount += len(intraLoops[chrLoops])

    matchedLoops = results[0]
    loopSet = results[1]
    loopsPerChromosome = results[2]

    hitCounter = 0
    maxl = 0

    output = {}
    header = 'ChrNo	Counts	Remaining	Total	Coverage'
    outstring = ''

    print('Extracting statistics and preparing output')
    for geneKey in matchedLoops:
        hits = len(matchedLoops[geneKey])
        if hits > maxl:
            maxl = hits
        hitCounter += hits

    for chrKey in loopsPerChromosome:
        outputKey = chrKey
        if outputKey not in output:
            output[outputKey] = 0
        output[outputKey] += len(loopsPerChromosome[chrKey])

    for chrKey in output:
        outstring += str(chrKey) + '	'
        outstring += str(output[chrKey]) + '	'
        outstring += str(len(intraLoops[chrKey]) - output[chrKey]) + '	'
        outstring += str(len(intraLoops[chrKey])) + '	'
        if len(intraLoops[chrKey]) > 0:
            outstring += str(
                '%.1f' % round(float(len(loopsPerChromosome[chrKey])) / float(len(intraLoops[chrKey])) * 100, 1))
        else:
            outstring += str(0.0)
        outstring += '\n'

    tset = set(tss.keys())
    mset = set(matchedLoops.keys())
    geneIntersection = tset.intersection(mset)

    outstring += 'ALL	'
    outstring += str(sum(output.values())) + '	'
    outstring += str(sum(len(v) for v in intraLoops.itervalues()) - len(loopSet)) + '	'
    outstring += str(sum(len(v) for v in intraLoops.itervalues())) + '	'
    outstring += str('%.1f' % round(float(len(loopSet)) / float(totalLoopCount) * 100, 1))
    outstring += '\n'

    print('\n###############')
    print('Parsed ' + str(totalGeneCount) + ' genes in total.')
    print('Parsed ' + str(totalLoopCount) + ' intrachromosomal loops in total.')
    print(str(len(geneIntersection)) + ' genes have a loop within the radius, that are ' + str(
        '%.1f' % round(float(len(geneIntersection)) / float(totalGeneCount) * 100, 1)) + ' % of all genes.')
    print('Found ' + str(len(loopSet)) + ' loops within a distance of ' + str(
        radius) + ' bases around the annotated TSS.')
    print('That are ' + str('%.1f' % round(float(len(loopSet)) / float(totalLoopCount) * 100, 1)) + '% of all loops.')
    print('Observed a maximum of ' + str(maxl) + ' loops nearby a single gene.')
    print('On average, there are ' + str(
        '%.1f' % round(float(hitCounter) / float(totalGeneCount), 1)) + ' loops nearby a gene.')
    print('###############\n')

    now = datetime.datetime.now()
    filename = now.strftime("%Y-%m-%d-%H-%M") + '_' + str(radius / 1000) + 'kb' + '.txt'

    writeToFile(filename, header, outstring)

    return 0


# Main entry point for algorithm, requires:
# 	an annotation-file
#  	a loop-file
# 	a radius in 1000 bases, which is >= 100
def collectLoopsAtGenes(annotationFile, loopsFile, radius):
    print('Indexing TSSs')
    tss = readGTF(annotationFile)
    print('Indexing Loops')
    intraLoops = readIntraLoops(loopsFile)

    if radius < 100:
        print('Radius too small... please use greater values e.g. 100 and above.')
        return 1

    print('Running core algorithm')
    results = run(tss, intraLoops, radius)

    postProcessing(results, tss, intraLoops, radius)

    return 0


######
##
# #	Required arguments: 1) annotation File (.gtf), 2) loop file in Hi-C loop format,
# #  3) radius (window radius around TSS in thousand bases)
##
######

# preparation-routine 
parser = argparse.ArgumentParser(
    description='Collects all loops in a window around genes and extracts some statistical values')
parser.add_argument('annotation', help='Path to an annotation file containing genes of interest.')
parser.add_argument('loops', help='Path to a Hi-C loop file')
parser.add_argument('radius', type=int, help='A radius around the TSS which should be scanned')

args = parser.parse_args()

print('Starting to collect data...')
collectLoopsAtGenes(args.annotation, args.loops, args.radius)
print('\n-> Completed all!')
