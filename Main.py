import multiprocessing
import Launcher

if __name__ == '__main__':

    while True:
        p = multiprocessing.Process(target=Launcher.main)
        p.start()
        p.join()