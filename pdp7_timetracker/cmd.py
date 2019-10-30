import IPython

import pdp7_timetracker


def main():
    config = pdp7_timetracker.Config()
    tt = pdp7_timetracker.TimeTracker(config)
    tt  # is put into ipython context
    IPython.embed()


if __name__ == "__main__":
    main()
