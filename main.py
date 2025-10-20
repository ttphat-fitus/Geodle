import sys

def main():
    from gameplay import main as gameplay_main
    try:
        gameplay_main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
