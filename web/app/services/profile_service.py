import cProfile
import pstats
import io


def profile_route(func):
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        response = func(*args, **kwargs)
        pr.disable()
        with open("profile_output.txt", "a+") as f:
            ps = pstats.Stats(pr, stream=f).sort_stats("cumtime")
            ps.print_stats()
            f.write("\n")

        pr.dump_stats("profile_output.prof")

        # s = io.StringIO()
        # ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
        # ps.print_stats()
        # print(s.getvalue())
        return response

    return wrapper
