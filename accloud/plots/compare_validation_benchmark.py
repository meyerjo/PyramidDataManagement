import argparse
from accloud import paths
from accloud.plots import boxplot_benchmark
import numpy as np
import itertools
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf', '-c', nargs='+')
    parser.add_argument('--bench', '-b', nargs='+')
    parser.add_argument('--meta', '-m')
    args = parser.parse_args()

    # Read in benchmark coefficient of variance
    cloud_stats = boxplot_benchmark.benchmark_stats(args.bench)
    cloud_coef = (np.mean(np.array(cloud_stats['stds']) / np.array(cloud_stats['means'])))

    meta_stats = boxplot_benchmark.benchmark_stats(['bench-' + args.meta])
    meta_coef = (np.mean(np.array(meta_stats['stds']) / np.array(meta_stats['means'])))

    # Read in configuration quality
    _, data = paths.sorted_scenario_data(args.conf)
    vm_qualities = np.hstack(data)

    # Read in meta quality
    _, meta_data = paths.sorted_scenario_data([args.meta])
    meta_qualities = np.hstack(meta_data)

    # Compare cloud to meta
    mean_diff = (np.mean(vm_qualities) - np.mean(meta_qualities))

    # Compare
    print(', '.join(['Scenario',
            'Total difference between cloud and meta',
            'Mean coefficient of variance']))
    print(', '.join(map(str, [
          os.path.basename(os.path.dirname(os.path.abspath(args.meta))),
          mean_diff,
          cloud_coef])))


if __name__ == '__main__':
    main()