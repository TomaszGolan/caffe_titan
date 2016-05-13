#!/usr/bin/env python
"""
Recursive workaround for 2 hours walltime.
"""
import click
from ConfigParser import SafeConfigParser
import os
from os.path import isfile, join
from datetime import datetime as date
import subprocess


def check_paths(paths):
    """Create missing paths."""
    for p in paths:
        if not os.path.exists(p[1]):
            os.makedirs(p[1])


def make_unique(name):
    """Just to make sure there are no name duplicates."""
    return name + "_" + date.now().isoformat().replace(":", ".")


def generate_pbs(cfg, snapshot=None):
    """Generate PBS script."""
    pbs = cfg.get("path", "logs") + "/" + cfg.get("status", "name") \
                                  + ".pbs"
    out = cfg.get("path", "logs") + "/" + cfg.get("status", "name") \
                                  + ".out"

    pbsf = open(pbs, 'w')

    print >> pbsf, "#!/bin/bash"
    print >> pbsf, "#PBS -A hep105"
    print >> pbsf, "#PBS -l nodes=1"
    print >> pbsf, "#PBS -l walltime=2:00:00"
    print >> pbsf, "#PBS -N", cfg.get("status", "name")
    print >> pbsf, "#PBS -o", out
    print >> pbsf, "#PBS -j oe"

    print >> pbsf, "source $MODULESHOME/init/bash"
    print >> pbsf, "source $PROJWORK/hep105/steven_caffe2/bashsetup.execenv.sh"
    print >> pbsf, "module load cray-mpich"

    print >> pbsf, "cd", cfg.get("path", "caffe")

    if not snapshot:
        print >> pbsf, "aprun -n 1 -N 1", \
                       "./build/tools/caffe train", \
                       "--solver=" + cfg.get("status", "solver")
    else:
        print >> pbsf, "aprun -n 1 -N 1", \
                       "./build/tools/caffe train", \
                       "--solver=" + cfg.get("status", "solver"), \
                       "--snapshot=" + snapshot

    print >> pbsf, "python", cfg.get("path", "myself"), "advance --status", \
        cfg.get("path", "logs") + "/" + cfg.get("status", "name") + ".ini"

    pbsf.close()

    return pbs


def generate_solver(cfg):
    """Make a clone of solver with params defined in config file."""
    solver = cfg.get("path", "logs") + "/" \
                                     + cfg.get("status", "name") \
                                     + ".solver"

    with open(cfg.get("path", "solver")) as f:
        init_solver = f.readlines()

    solverf = open(solver, 'w')

    for line in init_solver:
        if line.startswith('snapshot_prefix'):
            line = 'snapshot_prefix: "' + cfg.get("path", "snapshots") + '/' \
                   + cfg.get("status", "name") + '"\n'
        else:
            for option in cfg.items("caffe"):
                if line.startswith(option[0]):
                    line = option[0] + ": " + option[1]
        print >> solverf, line,

    solverf.close()

    return solver


def update_solver(cfg):
    """Update max_iter for next job."""
    max_iter = \
        cfg.getint("caffe", "max_iter") * cfg.getint("status", "current_run")

    with open(cfg.get("status", "solver"), 'r+') as f:
        solver = f.readlines()
        for line in solver:
            if line.startswith("max_iter"):
                line = "max_iter: " + str(max_iter) + "\n"
            print >> f, line,


def submit(pbs):
    """qsub the script"""
    return
    cmd = "qsub -q titan " + pbs
    subprocess.Popen(cmd, shell=True, executable="/bin/bash")


def save_config(cfg):
    """Save current status."""
    statusfile = cfg.get("path", "logs") \
        + "/" + cfg.get("status", "name") + ".ini"
    with open(statusfile, 'w') as configcopy:
        cfg.write(configcopy)


def get_checkpoint(cfg):
    """Find the last caffe snapshot."""
    path = cfg.get("path", "snapshots")
    prefix = cfg.get("status", "name") + "_iter_"
    suffix = ".solverstate"
    snapshots = [f for f in os.listdir(path) if isfile(join(path, f))]
    snapshots = [f for f in snapshots if f.startswith(prefix)]
    snapshots = [f for f in snapshots if f.endswith(suffix)]
    iterations = [int(i[len(prefix):-len(suffix)]) for i in snapshots]
    last = max(iterations)
    return path + "/" + prefix + str(last) + suffix, last


@click.group()
def main():
    pass


@main.command()
@click.option('--config', help='config ini file', required=True)
@click.option('--name', help='job name', default=None)
def new(config, name):
    """Prepare a job based on config file."""
    cfg = SafeConfigParser()
    cfg.read(config)

    check_paths(cfg.items('path'))

    jobname = make_unique(name or "mlmpr_caffe")
    current_run = 1

    cfg.add_section("status")
    cfg.set("status", "name", jobname)
    cfg.set("status", "current_run", str(current_run))

    solver = generate_solver(cfg)
    cfg.set("status", "solver", solver)

    save_config(cfg)

    pbs = generate_pbs(cfg)

    submit(pbs)


@main.command()
@click.option('--status', help='status ini file', required=True)
def advance(status):
    """Continue job saved with last checkpoint saved in status file."""
    cfg = SafeConfigParser()
    cfg.read(status)

    current_run = cfg.getint("status", "current_run") + 1
    cfg.set("status", "current_run", str(current_run))

    save_config(cfg)

    last_checkpoint, current_iter = get_checkpoint(cfg)

    try:
        max_iter = cfg.getint("caffe", "last_iter")
    except:
        max_iter = 0

    if max_iter and current_iter < max_iter:
        update_solver(cfg)
        pbs = generate_pbs(cfg, last_checkpoint)
        submit(pbs)

if __name__ == '__main__':
    main()
