import curses
from controller import GameApplication


def main(stdscr):
    """
    Точка входа приложения.
    Args:
        stdscr: объект окна curses (предоставляется curses.wrapper)
    """
    app = GameApplication(stdscr)
    app.run()


if __name__ == '__main__':
    curses.wrapper(main)
