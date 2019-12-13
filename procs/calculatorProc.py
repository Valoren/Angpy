import proc
# Calculators are Procs that generate a number; these numbers then feed into
# the formulae the engine uses (or may feed into other Procs, of course).


## This Calculator generates a number based on a multiplier applied to another
# stat.
class PercentageStatModCalculator(proc.Proc):
    ## \param stats things.stats.Stats instance for the entity in question.
    # \param curVal Calculated stat value thus far.
    # \param tier Tier of stat modifier we're using here. We can only consider
    #        lower-valued tiers for calculating our modifier.
    def trigger(self, stats, curVal, tier, *args, **kwargs):
        result = stats.getStatValue(self.params['sourceStat'], tier - 1) * self.params['multiplier']
        return result
      

## This Calculator is similar to the PercentageStatModCalculator, but it does
# a linear combination of any number of stats -- that is, you can specify 
# a stat name and a multiplier for that stat, and the results of all these
# multiplications are added together.
# Parameters are named as "x1", "x2", etc. for the multipliers, and
# "stat1", "stat2", etc. for the stat names.
class LinearCombinationStatModCalculator(proc.Proc):
    def trigger(self, stats, curVal, tier, **kwargs):
        result = 0
        for key, value in self.params.iteritems():
            if key.startswith('stat'):
                index = key[4:]
                statName = value
                # Find the corresponding multiplier.
                for key, value in self.params.iteritems():
                    if key.startswith('x') and key[1:] == index:
                        result += stats.getStatValue(statName, tier - 1) * value
                        break
        return int(result)

