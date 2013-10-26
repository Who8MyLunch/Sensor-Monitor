from __future__ import division, print_function, unicode_literals
"""
Generate items from multiple generators (multiplex).
"""

import Queue
import threading


def gen_multiplex(gen_list):
    item_q = Queue.Queue()

    def run_one(source):
        """Receive data from a single generator, place it into a queue.
        """
        for item in source:
            item_q.put(item)

    def run_all():
        """
        Run each source generator inside its own run_one thread.  Wait for individual threads
        to end when corresponding generator is finished.  Finally send StopIteration through the
        Queue to indicate all sources are finished.
        """
        thread_list = []
        for source in gen_list:
            t = threading.Thread(target=run_one, args=(source,))
            t.start()
            thread_list.append(t)

        for t in thread_list:
            t.join()

        item_q.put(StopIteration)

    # Start up all the threads with their own queues.
    threading.Thread(target=run_all).start()

    # Main loop receiving data from Queue.
    while True:
        item = item_q.get()
        if item is StopIteration:
            # All done.
            return

        yield item

#################################################


if __name__ == '__main__':

    import numpy as np
    import time

    # Some generators.
    def gen_alpha(N):
        for k in range(N):
            numeric = np.random.random_integers(65, 65+25)
            alpha = chr(numeric)
            time.sleep(0.1)  # np.random.uniform(0.5))
            yield alpha

    def gen_numeric(N):
        for k in range(N):
            numeric = np.random.random_integers(35, 35+25)
            time.sleep(0.05)  # np.random.uniform(0.5))
            yield numeric

    #############################################

    N = 10

    gens = gen_alpha(N), gen_numeric(N), gen_numeric(N)
    gen_combo = gen_multiplex(gens)

    for value in gen_combo:
        print(value)
