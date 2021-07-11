# lool #

from cProfile import Profile
from pstats import Stats, SortKey

with Profile() as pr:
    from lofile import main
    try:
        main(dev=True)
    except (SystemExit, KeyboardInterrupt):
        pass

stats = Stats(pr)
stats.sort_stats(SortKey.TIME)
stats.dump_stats(filename='lofile.prof')  # $ snakeviz lofile.prof
