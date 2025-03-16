import cProfile
import logging
import pstats
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

prof = cProfile.Profile()

# Hardcoded sys.argv arguments
sys.argv = ["main.py", "--solve", "--reparse", "-m", "words-with-cheaters", "-s", "example"]

# Run main.py within profiling
prof.run("exec(open('main.py').read(), {'__name__': '__main__', 'sys': sys})")

prof.dump_stats("profile_output.prof")

with open("profile_output.txt", "w") as stream:
    stats = pstats.Stats("profile_output.prof", stream=stream)
    stats.sort_stats("tottime")
    stats.print_stats()

stats = pstats.Stats("profile_output.prof")
total_time: int = stats.total_tt  # type: ignore

if not isinstance(total_time, int):
    raise TypeError("total_time is not an int.")

with open("profile_total_seconds.txt", "w") as f:
    f.write(str(total_time))

logging.info(f"Profiling complete. Total time: {total_time} seconds. Check profile_total_seconds.txt for the value.")
