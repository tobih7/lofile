# lool #

from cProfile import Profile
from pstats import Stats, SortKey

with Profile() as pr:
    from lofile.cli import main
    try:
        main()
    except BaseException:
        pass

stats = Stats(pr)
stats.sort_stats(SortKey.TIME)
stats.dump_stats(filename='lofile.prof')

print("end")
