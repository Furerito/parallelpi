import argparse
import threading
import multiprocessing
from functools import reduce
import sys
import time

# Leibniz-Reihe für Pi
def leibniz(start, end):
    result = 0.0
    for k in range(start, end):
        result += ((-1) ** k) / (2 * k + 1)
    return result

def worker(start, end, result_list, idx):
    result_list[idx] = leibniz(start, end)

def pool_worker(args):
    start, end = args
    return leibniz(start, end)

def simulate_hosts(hosts, segments):
    # Dummy-Verteilung auf Hosts, ohne echte Netzwerkkommunikation
    host_count = len(hosts)
    host_work = {host: [] for host in hosts}
    for idx, segment in enumerate(segments):
        host = hosts[idx % host_count]
        host_work[host].append(segment)
    results = []
    for host in hosts:
        print(f"[Host: {host}] bearbeitet Segmente: {host_work[host]}")
        for seg in host_work[host]:
            start, end = seg
            results.append(leibniz(start, end))
    return results

def map_filter_reduce_mode(iterations, workers):
    # Aufteilen in Segmente
    segment_size = iterations // workers
    segments = [(i * segment_size, (i + 1) * segment_size) for i in range(workers)]
    segments[-1] = (segments[-1][0], iterations)

    # map: Berechne für jedes Segment die Leibniz-Summe
    mapped = list(map(lambda seg: leibniz(seg[0], seg[1]), segments))
    # filter: Behalte nur positive Ergebnisse (konstruiertes Beispiel)
    filtered = list(filter(lambda x: x > 0, mapped))
    # reduce: Summiere die gefilterten Teilergebnisse auf
    result = reduce(lambda a, b: a + b, filtered)
    pi = 4 * result
    print(f"PI (mit map/filter/reduce): {pi}")

def main():
    parser = argparse.ArgumentParser(description='Parallel Pi Calculator')
    parser.add_argument('-i', '--iterations', type=int, help='Anzahl Iterationen')
    parser.add_argument('-k', '--workers', type=int, default=4, help='Anzahl Threads/Prozesse')
    parser.add_argument('--with-gil', action='store_true', help='mit GIL Threads (threading)')
    parser.add_argument('--with-thread', action='store_true', help='mit parallelen Threads (threading)')
    parser.add_argument('--with-proces', action='store_true', help='mit Prozessen (multiprocessing)')
    parser.add_argument('--pool', type=int, help='mit Pool aus N Prozessen')
    parser.add_argument('--hosts', type=str, help='Verteile Arbeit auf Hosts (kommagetrennt)')
    parser.add_argument('-s', '--segment', type=int, help='Nummer des Segments (für Einzel-Host-Betrieb)')
    parser.add_argument('--seg-size', type=int, help='Grösse eines Segments (für Einzel-Host-Betrieb)')
    parser.add_argument('--with-mapfilterreduce', action='store_true', help='Demonstration von map/filter/reduce')
    args = parser.parse_args()

    # Modus: map/filter/reduce
    if args.with_mapfilterreduce:
        if args.iterations is None:
            print("Bitte --iterations angeben!")
            sys.exit(1)
        map_filter_reduce_mode(args.iterations, args.workers)
        sys.exit(0)

    # Segment-Modus für verteilte Hosts
    if args.segment is not None and args.seg_size is not None and args.hosts:
        start = args.segment * args.seg_size
        end = start + args.seg_size
        print(f"Segment-Modus: Bearbeite Segment {args.segment} (k={start} bis {end}) auf Hosts {args.hosts}")
        result = leibniz(start, end)
        pi = 4 * result
        print(f"PI (Segment {args.segment}): {pi}")
        sys.exit(0)

    # Hosts-Modus (simuliert)
    if args.hosts:
        if args.iterations is None:
            print("Bitte --iterations angeben!")
            sys.exit(1)
        hosts = [h.strip() for h in args.hosts.split(",")]
        k_workers = args.workers
        segment_size = args.iterations // k_workers
        segments = [(i * segment_size, (i + 1) * segment_size) for i in range(k_workers)]
        segments[-1] = (segments[-1][0], args.iterations)
        results = simulate_hosts(hosts, segments)
        pi = 4 * sum(results)
        print(f"PI (simulierte Hosts): {pi}")
        sys.exit(0)

    # Pool-Modus
    if args.pool:
        if args.iterations is None:
            print("Bitte --iterations angeben!")
            sys.exit(1)
        poolsize = args.pool
        segment_size = args.iterations // poolsize
        segments = [(i * segment_size, (i + 1) * segment_size) for i in range(poolsize)]
        segments[-1] = (segments[-1][0], args.iterations)
        with multiprocessing.Pool(poolsize) as pool:
            results = pool.map(pool_worker, segments)
        pi = 4 * sum(results)
        print(f'PI (Pool mit {poolsize} Prozessen): {pi}')
        sys.exit(0)

    # Klassische Modi
    if args.iterations is None:
        print("Bitte --iterations angeben!")
        sys.exit(1)
    iterations = args.iterations
    k_workers = args.workers
    segment_size = iterations // k_workers
    segments = [(i * segment_size, (i + 1) * segment_size) for i in range(k_workers)]
    segments[-1] = (segments[-1][0], iterations)

    if args.with_gil or args.with_thread:
        threads = []
        results = [0.0] * k_workers
        for idx, (start, end) in enumerate(segments):
            t = threading.Thread(target=worker, args=(start, end, results, idx))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        pi = 4 * sum(results)
        print(f'PI (threading): {pi}')
    elif args.with_proces:
        manager = multiprocessing.Manager()
        results = manager.list([0.0] * k_workers)
        processes = []
        for idx, (start, end) in enumerate(segments):
            p = multiprocessing.Process(target=worker, args=(start, end, results, idx))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
        pi = 4 * sum(results)
        print(f'PI (multiprocessing): {pi}')
    else:
        pi = 4 * leibniz(0, iterations)
        print(f'PI (single thread): {pi}')

if __name__ == '__main__':
    main()
