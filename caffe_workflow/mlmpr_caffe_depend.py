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
                                  + "_" + cfg.get("status", "current_run") \
                                  + ".out"
    name = cfg.get("status", "name") + "_" + cfg.get("status", "current_run")

    pbsf = open(pbs, 'w')

    print >> pbsf, "#!/bin/bash"
    print >> pbsf, "#PBS -A hep105"
    print >> pbsf, "#PBS -l nodes=1"
    print >> pbsf, "#PBS -l walltime=02:00:00"
    print >> pbsf, "#PBS -N", name
    print >> pbsf, "#PBS -o", out
    print >> pbsf, "#PBS -j oe"
    print >> pbsf, "#PBS -m n"

    print >> pbsf, "qsub -W depend=afternotok:$PBS_JOBID " \
        + cfg.get("status", "updater")

    print >> pbsf, "source $MODULESHOME/init/bash"
    print >> pbsf, "source $PROJWORK/hep105/steven_caffe2/bashsetup.execenv.sh"
    print >> pbsf, "module load cray-mpich"

    print >> pbsf, "cd", cfg.get("path", "caffe")

    if not snapshot:
        print >> pbsf, "command time -v aprun -n 1 -N 1", \
                       "./build/tools/caffe train", \
                       "--solver=" + cfg.get("status", "solver")
    else:
        print >> pbsf, "command time -v aprun -n 1 -N 1", \
                       "./build/tools/caffe train", \
                       "--solver=" + cfg.get("status", "solver"), \
                       "--snapshot=" + snapshot

    pbsf.close()

    return pbs


def generate_updater(cfg):
    """Generate PBS script called when job is killed."""
    pbs = cfg.get("path", "logs") + "/" + cfg.get("status", "name") \
                                  + "_updater.pbs"
    out = cfg.get("path", "logs") + "/" + cfg.get("status", "name") \
                                  + "_updater.out"
    name = cfg.get("status", "name") + "_" \
                                     + cfg.get("status", "current_run") \
                                     + "_updater"

    pbsf = open(pbs, 'w')

    print >> pbsf, "#!/bin/bash"
    print >> pbsf, "#PBS -A hep105"
    print >> pbsf, "#PBS -l nodes=1"
    print >> pbsf, "#PBS -l walltime=00:10:00"
    print >> pbsf, "#PBS -N", name
    print >> pbsf, "#PBS -o", out
    print >> pbsf, "#PBS -j oe"
    print >> pbsf, "#PBS -m n"

    print >> pbsf, "cd " + cfg.get("path", "logs")

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
        elif line.startswith('net'):
            line = 'net: "' + cfg.get("status", "prototxt") + '"\n'
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

    with open(cfg.get("status", "solver"), 'r') as f:
        solver = f.readlines()

    with open(cfg.get("status", "solver"), 'w') as f:
        for line in solver:
            if line.startswith("max_iter"):
                line = "max_iter: " + str(max_iter) + "\n"
            print >> f, line,


def get_proto_path(solver):
    """Extract path to net conf file based on default solver."""
    with open(solver) as f:
        init_solver = f.readlines()

    for line in init_solver:
        if line.startswith('net'):
            return line[4:].strip().strip('"')


def generate_prototxt(cfg, batch_size):
    """Make a clone of prototxt with params defined in config file."""
    prototxt = cfg.get("path", "logs") + "/" \
                                       + cfg.get("status", "name") \
                                       + ".prototxt"

    with open(get_proto_path(cfg.get("path", "solver"))) as f:
        init_proto = f.readlines()

    prototxtf = open(prototxt, 'w')

    for line in init_proto:
        if batch_size and line.strip().startswith('batch_size'):
            line = "batch_size: %s" % batch_size
        print >> prototxtf, line,

    prototxtf.close()

    return prototxt


def submit(pbs):
    """qsub the script"""
    cmd = "qsub -q titan " + pbs
    subprocess.call(cmd, shell=True)


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


def update_iterations(cfg, batch_size, epoch, learn, test):
    """Set proper no. of iterations."""
    max_iter = learn / batch_size * epoch
    test_iter = test / batch_size
    test_interval = learn / batch_size / 5
    display = learn / batch_size / 100
    snapshot = learn / batch_size / 10

    cfg.set("caffe", "max_iter", str(max_iter))
    cfg.set("caffe", "test_iter", str(test_iter))
    cfg.set("caffe", "test_interval", str(test_interval))
    cfg.set("caffe", "display", str(display))
    cfg.set("caffe", "snapshot", str(snapshot))


@click.group()
def main():
    pass


@main.command()
@click.option('-c', '--config', help='config ini file', required=True)
@click.option('-n', '--name', help='job name', default=None)
@click.option('-b', '--batch_size', help='batch size', default=None)
@click.option('-e', '--epoch', type=int, help='number of epochs', default=None)
@click.option('-l', '--learn', type=int, help='no. of training samples', default=None)
@click.option('-t', '--test', type=int, help='no. of testing samples', default=None)
def new(config, name, batch_size, epoch, learn, test):
    """Prepare a job based on config file."""
    cfg = SafeConfigParser()
    cfg.read(config)

    check_paths(cfg.items('path'))

    jobname = make_unique(name or "mlmpr_caffe")
    current_run = 1

    if epoch and learn and test:
        update_iterations(cfg, int(batch_size), int(epoch), int(learn), int(test))

    cfg.add_section("status")
    cfg.set("status", "name", jobname)
    cfg.set("status", "current_run", str(current_run))

    prototxt = generate_prototxt(cfg, batch_size)
    cfg.set("status", "prototxt", prototxt)

    solver = generate_solver(cfg)
    cfg.set("status", "solver", solver)

    updater = generate_updater(cfg)
    cfg.set("status", "updater", updater)

    save_config(cfg)

    pbs = generate_pbs(cfg)

    submit(pbs)


@main.command()
@click.option('--status', help='status ini file', required=True)
def advance(status):
    """Continue job saved with last checkpoint saved in status file."""
    cfg = SafeConfigParser()
    cfg.read(status)

    last_checkpoint, current_iter = get_checkpoint(cfg)

    current_run = cfg.getint("status", "current_run") + 1
    cfg.set("status", "current_run", str(current_run))

    save_config(cfg)

    pbs = generate_pbs(cfg, last_checkpoint)

    submit(pbs)

if __name__ == '__main__':
    main()
