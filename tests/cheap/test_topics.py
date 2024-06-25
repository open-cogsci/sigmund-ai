from pathlib import Path
from sigmund import config


def test_topics_exist():
    for topic in config.topic_sources.values():
        assert Path(topic).exists()
