import cProfile
import pstats
import io


def profile_route(func):
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        response = func(*args, **kwargs)
        pr.disable()
        # to txt
        with open("profile_output.txt", "a+") as f:
            ps = pstats.Stats(pr, stream=f).sort_stats("cumtime")
            ps.print_stats()
            f.write("\n")

        # to prof file
        pr.dump_stats("profile_output.prof")
        return response

    return wrapper
