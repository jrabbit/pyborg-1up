import statsd

c = statsd.StatsClient("localhost", 8125, prefix="pyborg")


def send_stats(pyb):
    c.gauge("words", pyb.settings.num_words)
    c.gauge("contexts", pyb.settings.num_contexts)
    c.gauge("lines", len(pyb.lines))
