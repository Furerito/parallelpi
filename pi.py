import argparse
import threading
import multiprocessing
import time  # <-- hinzufügen

def leibniz(start, end):
    result = 0.0
    for k in range(start, end):
        result += ((-1) ** k) / (2 * k + 1)
    return result

def worker(start, end, result_list, idx):
    result_list[idx] = leibniz(start, end)

def main():
    parser = argparse.ArgumentParser(description='Parallel Pi Calculator')
    parser.add_argument('-i', '--iterations', type=int, required=True, help='Anzahl Iterationen')
    parser.add_argument('-k', '--workers', type=int, default=4, help='Anzahl Threads/Prozesse')
    parser.add_argument('--with-gil', action='store_true', help='mit GIL Threads (threading)')
    parser.add_argument('--with-thread', action='store_true', help='mit parallelen Threads (threading)')
    parser.add_argument('--with-proces', action='store_true', help='mit Prozessen (multiprocessing)')
    args = parser.parse_args()

    iterations = args.iterations
    k_workers = args.workers

    segment_size = iterations // k_workers
    segments = [(i * segment_size, (i + 1) * segment_size) for i in range(k_workers)]
    # Letztes Segment evtl. bis zum Ende auffuellen
    segments[-1] = (segments[-1][0], iterations)

    if args.with_gil or args.with_thread:
        threads = []
        results = [0.0] * k_workers
        start_time = time.time()
        for idx, (start, end) in enumerate(segments):
            t = threading.Thread(target=worker, args=(start, end, results, idx))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        pi = 4 * sum(results)
        elapsed = (time.time() - start_time) * 1000
        print(f'PI (threading): {pi}')
        print(f'Verstrichene Zeit (threading): {elapsed:.2f} ms')
    elif args.with_proces:
        manager = multiprocessing.Manager()
        results = manager.list([0.0] * k_workers)
        processes = []
        start_time = time.time()
        for idx, (start, end) in enumerate(segments):
            p = multiprocessing.Process(target=worker, args=(start, end, results, idx))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
        pi = 4 * sum(results)
        elapsed = (time.time() - start_time) * 1000
        print(f'PI (multiprocessing): {pi}')
        print(f'Verstrichene Zeit (multiprocessing): {elapsed:.2f} ms')
    else:
        start_time = time.time()
        pi = 4 * leibniz(0, iterations)
        elapsed = (time.time() - start_time) * 1000
        print(f'PI (single thread): {pi}')
        print(f'Verstrichene Zeit (single thread): {elapsed:.2f} ms')

if __name__ == '__main__':
    main()
