from __future__ import division
import numpy as np
from multiprocessing import Pool, cpu_count
from itertools import combinations
from math import factorial as bang
import logging

seed = 1337

def hybrid_permutation(y, z, max_comparision=100000):
    n = y.size + z.size
    r = y.size

    exact_comparisions = bang(n) / bang(r) / bang(n-r)

    if exact_comparisions > max_comparision:
        logging.warn('Using approximate test with %d samples' % max_comparision)
        return permutation(y, z, max_comparision)
    else:
        return exact_permutation(y, z)

def permutation(y, z, numSamples=100000):
    """1-sided permutation significance test
    :param y Numpy array
    :param z Numpy array
    :returns Significance level p
    """
    np.random.seed(seed)

    pooled = np.hstack([z,y])
    sizeZ = z.size
    sizeY = y.size

    def run_permutation_test(numrun):
        np.random.shuffle(pooled)
        starZ = pooled[:sizeZ]
        starY = pooled[-sizeY:]
        return starZ.mean() - starY.mean()

    delta = z.mean() - y.mean()
    estimates = np.array(map(run_permutation_test , range(numSamples)))
    diffCount = len(np.where(estimates <=delta)[0])
    return 1.0 - (diffCount / numSamples), delta

def exact_permutation(y, z):

    """1-sided exact permutation significance test
    :param y Numpy array
    :param z Numpy array
    :returns Significance level p
    """

    pooled = np.hstack([z,y])

    def run_permutation_test(data):
        z, y = data
        return np.array(z).mean() - np.array(y).mean()

    delta = z.mean() - y.mean()
    groupZ = combinations(pooled, len(z))
    groupY = list(combinations(pooled, len(y)))
    groupY.reverse()

    estimates = np.array(map(run_permutation_test, zip(groupZ, groupY)))
    diffCount = len(np.where(estimates <=delta)[0])
    return 1.0 - (diffCount / len(groupY)), delta


if __name__ == '__main__':
    print exact_permutation(np.array(range(3)), np.array(range(3,7)))
    print exact_permutation(np.array(range(3)), np.array(range(3)))
