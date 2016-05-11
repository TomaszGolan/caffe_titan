#!/usr/bin/env python
"""
Recursive workaround for 2 hours walltime.
"""
import click
from ConfigParser import SafeConfigParser
import os
from datetime import datetime as date


def check_paths(paths):
    """Create missing paths."""
    for p in paths:
        if not os.path.exists(p[1]):
            os.makedirs(p[1])


def make_unique(name):
    return name + date.now().isoformat()


@click.group()
def main():
    pass


@main.command()
@click.option('--config', help='config ini file', required=True)
@click.option('--name', help='job name', default=None)
def new(config, name):
    cfg = SafeConfigParser()
    cfg.read(config)
    check_paths(cfg.items('path'))
    jobname = make_unique(name or "mlmpr_caffe")
    print jobname

if __name__ == '__main__':
    main()
