import collections
import json
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import requests
from requests.exceptions import ConnectionError
from matplotlib import pyplot, dates

Status = collections.namedtuple("Status", ["date", "status_code", "response_time"])

status_path = Path("status")


def parse_arguments():
    parser = ArgumentParser("Uptime monitor")
    parser.add_argument("url", help="URL to monitor")
    parser.add_argument("-f", "--follow_redirect", help="Follow redirects",
                        action="store_true")
    return parser.parse_args()


def add_status(status: Status, url: str,  max_history: int = 1000):
    """Add the new status

    Will delete
    """
    stats = read_status(url)
    stats.setdefault(url, dict(date=[], status_code=[], response_time=[]))
    stats[url]["date"].append(status.date)
    stats[url]["status_code"].append(status.status_code)
    stats[url]["response_time"].append(status.response_time)
    if len(stats[url]["date"]) > max_history:
        stats[url]["date"].pop(0)
        stats[url]["status_code"].pop(0)
        stats[url]["response_time"].pop(0)
    status_path.write_text(json.dumps(stats))
    return stats


def read_status(url: str):
    """Read any existing status, creating it if it does not exist"""
    if not status_path.exists():
        stats = {url: dict(
            date=[], status_code=[], response_time=[]
        )}
        status_path.write_text(json.dumps(stats))
    else:
        stats = json.loads(status_path.read_text())
    return stats


def plot_stats(stats, url):
    data = stats[url]
    fig, ax = pyplot.subplots()
    ax.plot("date", "response_time", data=data)
    ax2 = ax.twinx()
    ax2.plot("date", "status_code", data=data, color="green")
    ax.set(title=url, ylabel="Response time [s]")
    ax2.set(ylabel="Status code")
    ax.format_xdata = dates.AutoDateFormatter(dates.AutoDateLocator())
    ax.xaxis.set_major_locator(pyplot.MaxNLocator(10))
    fig.autofmt_xdate()
    fig.savefig('status.svg')


def ping(url: str, follow_redirect: bool) -> Status:
    now = datetime.now()
    try:
        response = requests.get(url, allow_redirects=follow_redirect)
    except ConnectionError:
        status = 0
        response_time = 0
    else:
        status = response.status_code
        response_time = response.elapsed.total_seconds()
    return Status(str(now), status, response_time)


def run(url, follow_redirect):
    """"""
    status = ping(url=url, follow_redirect=follow_redirect)
    stats = add_status(status, url=url)
    plot_stats(stats, url=url)


if __name__ == "__main__":
    args = parse_arguments()
    run(url=args.url, follow_redirect=args.follow_redirect)
