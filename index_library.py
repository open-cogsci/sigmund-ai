from sigmund import library, config
import logging; logging.basicConfig(level=logging.INFO, force=True)

if __name__ == '__main__':
    library.load_library(force_reindex=True, exclude_filter=['forum'])
